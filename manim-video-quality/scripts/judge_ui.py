#!/usr/bin/env python3
# /// script
# requires-python = ">=3.9"
# dependencies = []
# ///
"""Pairwise video judging UI — collect human ground truth for Dataset A.

Humans are unreliable at absolute 1-10 scoring and reliable at "which of
these two is better." This serves forced-choice pairs in a browser and
records the results, which become the ground truth that any LLM grader is
then validated against (Spearman rho, see ../reference/gemini-video-analysis.md §8).

Design decisions that protect validity:
  - Left/right position is randomized per pair and recorded, so position
    bias can be measured rather than assumed away.
  - Clip filenames shown to the browser are opaque (clip_04.mp4); the true
    ids live only in the manifest and the saved results.
  - "Too close to call" is a first-class answer. Forcing a decision on a
    genuine tie manufactures noise.
  - Every judgment is written to disk immediately, so the session is
    resumable and a crash costs nothing.

Zero dependencies — stdlib only, so onboarding is `python3 judge_ui.py`.

Usage:
    python3 judge_ui.py --corpus /path/to/corpus [--out judgments.json]
    uv run judge_ui.py --corpus /path/to/corpus
"""

from __future__ import annotations

import argparse
import json
import os
import random
import re
import socketserver
import sys
import webbrowser
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler
from itertools import combinations
from pathlib import Path

QUESTION = ("Which is closer to the target: a patient, idea-first technical "
            "explainer in the 3Blue1Brown tradition?")

STATE: dict = {}


# ---------------------------------------------------------------------------
# Pair scheduling
# ---------------------------------------------------------------------------

def build_pairs(clip_files: list[str], seed: int) -> list[dict]:
    """All unique pairs, shuffled, with left/right assignment randomized."""
    rng = random.Random(seed)
    pairs = list(combinations(sorted(clip_files), 2))
    rng.shuffle(pairs)
    out = []
    for a, b in pairs:
        left, right = (a, b) if rng.random() < 0.5 else (b, a)
        out.append({"pair_id": f"{min(a,b)}|{max(a,b)}",
                    "left": left, "right": right})
    return out


def load_results(path: Path) -> dict:
    if path.exists():
        try:
            return json.loads(path.read_text())
        except json.JSONDecodeError:
            print(f"  warning: {path} unreadable, starting fresh",
                  file=sys.stderr)
    return {"started": datetime.now(timezone.utc).isoformat(),
            "question": QUESTION, "judgments": []}


def save_results(path: Path, results: dict) -> None:
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(results, indent=2))
    tmp.replace(path)


def next_index(results: dict, pairs: list[dict]) -> int:
    done = {j["pair_id"] for j in results["judgments"]}
    for i, p in enumerate(pairs):
        if p["pair_id"] not in done:
            return i
    return len(pairs)


# ---------------------------------------------------------------------------
# HTTP
# ---------------------------------------------------------------------------

class Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def log_message(self, *a):  # quiet
        pass

    # -- helpers ------------------------------------------------------------
    def _json(self, obj, code=200):
        body = json.dumps(obj).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _html(self, text: str):
        body = text.encode()
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _serve_video(self, path: Path):
        """Serve with HTTP Range support — Safari refuses video without it."""
        if not path.is_file():
            self.send_error(404)
            return
        size = path.stat().st_size
        rng = self.headers.get("Range")
        start, end = 0, size - 1
        status = 200
        if rng:
            m = re.match(r"bytes=(\d*)-(\d*)", rng)
            if m:
                if m.group(1):
                    start = int(m.group(1))
                if m.group(2):
                    end = int(m.group(2))
                end = min(end, size - 1)
                if start > end:
                    self.send_response(416)
                    self.send_header("Content-Range", f"bytes */{size}")
                    self.end_headers()
                    return
                status = 206
        length = end - start + 1
        self.send_response(status)
        self.send_header("Content-Type", "video/mp4")
        self.send_header("Accept-Ranges", "bytes")
        self.send_header("Content-Length", str(length))
        if status == 206:
            self.send_header("Content-Range", f"bytes {start}-{end}/{size}")
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        with path.open("rb") as f:
            f.seek(start)
            remaining = length
            while remaining > 0:
                chunk = f.read(min(65536, remaining))
                if not chunk:
                    break
                try:
                    self.wfile.write(chunk)
                except (BrokenPipeError, ConnectionResetError):
                    return
                remaining -= len(chunk)

    def _state_payload(self):
        pairs, results = STATE["pairs"], STATE["results"]
        i = next_index(results, pairs)
        done = len(results["judgments"])
        total = len(pairs)
        cur = pairs[i] if i < total else None
        return {"done": done, "total": total, "question": QUESTION,
                "current": cur, "finished": cur is None,
                "out": str(STATE["out"])}

    # -- routes -------------------------------------------------------------
    def do_GET(self):
        if self.path == "/" or self.path.startswith("/?"):
            self._html(PAGE)
        elif self.path == "/api/state":
            self._json(self._state_payload())
        elif self.path.startswith("/clips/"):
            name = os.path.basename(self.path.split("?")[0])
            self._serve_video(STATE["corpus"] / name)
        else:
            self.send_error(404)

    def do_POST(self):
        length = int(self.headers.get("Content-Length", 0))
        try:
            data = json.loads(self.rfile.read(length) or b"{}")
        except json.JSONDecodeError:
            self._json({"error": "bad json"}, 400)
            return

        if self.path == "/api/judge":
            pairs, results = STATE["pairs"], STATE["results"]
            i = next_index(results, pairs)
            if i >= len(pairs):
                self._json(self._state_payload())
                return
            p = pairs[i]
            choice = data.get("choice")  # 'left' | 'right' | 'tie'
            if choice not in ("left", "right", "tie"):
                self._json({"error": "bad choice"}, 400)
                return
            winner = None if choice == "tie" else p[choice]
            results["judgments"].append({
                "pair_id": p["pair_id"],
                "left": p["left"], "right": p["right"],
                "choice": choice,
                "winner_file": winner,
                "winner_id": STATE["file2id"].get(winner) if winner else None,
                "left_id": STATE["file2id"].get(p["left"]),
                "right_id": STATE["file2id"].get(p["right"]),
                "note": (data.get("note") or "").strip(),
                "elapsed_s": round(float(data.get("elapsed", 0)), 1),
                "ts": datetime.now(timezone.utc).isoformat(),
            })
            save_results(STATE["out"], results)
            self._json(self._state_payload())

        elif self.path == "/api/undo":
            results = STATE["results"]
            if results["judgments"]:
                results["judgments"].pop()
                save_results(STATE["out"], results)
            self._json(self._state_payload())
        else:
            self.send_error(404)


PAGE = r"""<!doctype html>
<meta charset="utf-8">
<title>Pairwise video judging</title>
<style>
  :root { --bg:#111214; --fg:#e8eaed; --dim:#9aa0a6; --line:#2a2d31;
          --accent:#58c4dd; }
  * { box-sizing:border-box; }
  body { margin:0; background:var(--bg); color:var(--fg);
         font:15px/1.5 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif; }
  header { padding:14px 20px; border-bottom:1px solid var(--line);
           display:flex; align-items:center; gap:20px; }
  #q { font-weight:600; font-size:15px; }
  #prog { margin-left:auto; color:var(--dim); font-variant-numeric:tabular-nums;
          white-space:nowrap; }
  #bar { height:3px; background:var(--line); }
  #barfill { height:100%; width:0; background:var(--accent); transition:width .2s; }
  main { display:grid; grid-template-columns:1fr 1fr; gap:16px; padding:16px 20px; }
  .pane { border:1px solid var(--line); border-radius:10px; overflow:hidden;
          background:#000; cursor:pointer; position:relative;
          transition:border-color .12s; }
  .pane:hover { border-color:var(--accent); }
  .pane video { width:100%; display:block; aspect-ratio:16/9; background:#000; }
  .tag { position:absolute; top:8px; left:8px; background:rgba(0,0,0,.65);
         color:var(--fg); padding:2px 8px; border-radius:5px; font-size:12px;
         letter-spacing:.04em; }
  footer { padding:0 20px 22px; }
  .row { display:flex; gap:10px; align-items:center; }
  button { font:inherit; padding:11px 18px; border-radius:9px; cursor:pointer;
           border:1px solid var(--line); background:#1b1d20; color:var(--fg); }
  button:hover { border-color:var(--accent); }
  button.primary { flex:1; font-weight:600; }
  #note { flex:1; padding:10px 12px; border-radius:9px; border:1px solid var(--line);
          background:#1b1d20; color:var(--fg); font:inherit; }
  .hint { color:var(--dim); font-size:12.5px; margin-top:10px; }
  kbd { background:#26292d; border:1px solid var(--line); border-bottom-width:2px;
        border-radius:5px; padding:1px 6px; font-size:12px; font-family:inherit; }
  #done { padding:60px 20px; text-align:center; display:none; }
  #done h2 { font-weight:600; }
  code { background:#1b1d20; padding:2px 7px; border-radius:5px; font-size:13px; }
</style>

<header>
  <div id="q">…</div>
  <div id="prog"></div>
</header>
<div id="bar"><div id="barfill"></div></div>

<div id="app">
  <main>
    <div class="pane" id="paneL" onclick="judge('left')">
      <span class="tag">A</span>
      <video id="vidL" muted loop playsinline preload="auto"></video>
    </div>
    <div class="pane" id="paneR" onclick="judge('right')">
      <span class="tag">B</span>
      <video id="vidR" muted loop playsinline preload="auto"></video>
    </div>
  </main>
  <footer>
    <div class="row">
      <button class="primary" onclick="judge('left')">◀ A is better</button>
      <button onclick="judge('tie')">Too close to call</button>
      <button class="primary" onclick="judge('right')">B is better ▶</button>
    </div>
    <div class="row" style="margin-top:10px">
      <input id="note" placeholder="Optional: what decided it? (helps a lot later)">
      <button onclick="replay()">Replay</button>
      <button onclick="undo()">Undo</button>
    </div>
    <div class="hint">
      <kbd>←</kbd> A better &nbsp; <kbd>→</kbd> B better &nbsp;
      <kbd>↓</kbd> or <kbd>space</kbd> tie &nbsp; <kbd>r</kbd> replay &nbsp;
      <kbd>u</kbd> undo &nbsp;— judge on overall feel; both loop automatically.
    </div>
  </footer>
</div>

<div id="done">
  <h2>Done — thank you.</h2>
  <p id="donemsg" style="color:var(--dim)"></p>
  <button onclick="undo()">Undo last</button>
</div>

<script>
let S = null, t0 = Date.now();

async function load() {
  S = await (await fetch('/api/state')).json();
  document.getElementById('q').textContent = S.question;
  document.getElementById('prog').textContent = S.done + ' / ' + S.total;
  document.getElementById('barfill').style.width =
    (S.total ? (100 * S.done / S.total) : 0) + '%';

  if (S.finished) {
    document.getElementById('app').style.display = 'none';
    document.getElementById('done').style.display = 'block';
    document.getElementById('donemsg').innerHTML =
      S.done + ' judgments saved to <code>' + S.out + '</code>';
    return;
  }
  document.getElementById('app').style.display = '';
  document.getElementById('done').style.display = 'none';

  const L = document.getElementById('vidL'), R = document.getElementById('vidR');
  L.src = '/clips/' + S.current.left;
  R.src = '/clips/' + S.current.right;
  L.load(); R.load();
  L.play().catch(()=>{}); R.play().catch(()=>{});
  document.getElementById('note').value = '';
  t0 = Date.now();
}

async function judge(choice) {
  if (!S || S.finished) return;
  const note = document.getElementById('note').value;
  const elapsed = (Date.now() - t0) / 1000;
  S = null;                                  // guard against double-submit
  await fetch('/api/judge', {
    method: 'POST', headers: {'Content-Type':'application/json'},
    body: JSON.stringify({choice, note, elapsed})
  });
  load();
}

async function undo() {
  await fetch('/api/undo', {method:'POST', headers:{'Content-Type':'application/json'}, body:'{}'});
  load();
}

function replay() {
  for (const id of ['vidL','vidR']) {
    const v = document.getElementById(id);
    v.currentTime = 0; v.play().catch(()=>{});
  }
}

addEventListener('keydown', e => {
  if (e.target.tagName === 'INPUT' && e.key !== 'Enter') return;
  if (e.key === 'ArrowLeft')  { e.preventDefault(); judge('left'); }
  if (e.key === 'ArrowRight') { e.preventDefault(); judge('right'); }
  if (e.key === 'ArrowDown' || e.key === ' ') { e.preventDefault(); judge('tie'); }
  if (e.key === 'r') replay();
  if (e.key === 'u') undo();
});

load();
</script>
"""


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--corpus", type=Path, required=True,
                    help="dir containing clip_*.mp4 and manifest.json")
    ap.add_argument("--out", type=Path, default=None,
                    help="results file (default: <corpus>/judgments.json)")
    ap.add_argument("--port", type=int, default=8765)
    ap.add_argument("--seed", type=int, default=7)
    ap.add_argument("--no-open", action="store_true")
    args = ap.parse_args()

    corpus = args.corpus.expanduser().resolve()
    man_path = corpus / "manifest.json"
    if not man_path.exists():
        sys.exit(f"No manifest.json in {corpus} — run prep_corpus.py first")

    manifest = json.loads(man_path.read_text())
    files = [c["file"] for c in manifest["clips"]]
    file2id = {c["file"]: c["id"] for c in manifest["clips"]}
    if len(files) < 2:
        sys.exit("Need at least 2 clips")

    out = (args.out or corpus / "judgments.json").expanduser().resolve()

    STATE.update({
        "corpus": corpus, "out": out, "file2id": file2id,
        "pairs": build_pairs(files, args.seed),
        "results": load_results(out),
    })
    STATE["results"]["corpus_manifest"] = str(man_path)
    STATE["results"]["pair_seed"] = args.seed

    done = len(STATE["results"]["judgments"])
    total = len(STATE["pairs"])
    url = f"http://127.0.0.1:{args.port}/"

    print(f"\n  {len(files)} clips  ->  {total} pairs")
    if done:
        print(f"  resuming: {done} already judged")
    print(f"  results: {out}")
    print(f"\n  {url}\n")
    print("  ←/→ choose · ↓ tie · r replay · u undo · Ctrl-C to stop "
          "(progress is saved continuously)\n")

    if not args.no_open:
        try:
            webbrowser.open(url)
        except Exception:
            pass

    class Server(socketserver.ThreadingTCPServer):
        allow_reuse_address = True
        daemon_threads = True

    try:
        with Server(("127.0.0.1", args.port), Handler) as httpd:
            httpd.serve_forever()
    except KeyboardInterrupt:
        n = len(STATE["results"]["judgments"])
        print(f"\n  stopped — {n}/{total} judged, saved to {out}\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
