#!/usr/bin/env python3
# /// script
# requires-python = ">=3.9"
# dependencies = []
# ///
"""Learn narration pacing from reference videos by measuring their subtitles.

Motivation: if your explainer is narrated, beat duration is not a taste call
— a beat should last about as long as it takes to SAY its line. That makes
pacing derivable from a script, but only once you know the target speaking
rate and how much silence the reference style leaves between lines.

Rather than guessing those constants, measure them. Subtitles are kilobytes
and carry both the words and their timing, so a broad sample is cheap.

Reports, per video and pooled:
  - speech rate in words/minute *while actually speaking* (not wall-clock,
    which conflates rate with pausing)
  - speech density: fraction of runtime that has narration over it
  - effective wall-clock words/minute (rate x density) — the number that
    actually determines how long your animation must hold
  - cue length distribution — how long one spoken unit tends to run, which
    maps onto how long one visual beat should hold

Requires yt-dlp. Downloads subtitles only, never video.

Usage:
    python3 harvest_reference_pacing.py --list refs.txt --out ./ref_pacing
    uv run harvest_reference_pacing.py --query "ytsearch1:..." --out ./ref_pacing
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import statistics
import subprocess
import sys
from pathlib import Path

TS = re.compile(r"(\d{2}):(\d{2}):(\d{2})[.,](\d{3})\s*-->\s*"
                r"(\d{2}):(\d{2}):(\d{2})[.,](\d{3})")
TAG = re.compile(r"<[^>]+>")


def secs(h, m, s, ms) -> float:
    return int(h) * 3600 + int(m) * 60 + int(s) + int(ms) / 1000.0


def parse_vtt(path: Path) -> list[tuple[float, float, str]]:
    """Return [(start, end, text)] with duplicate/rolling cues collapsed.

    YouTube auto-captions repeat lines across cues to create a scrolling
    effect; counting those naively roughly doubles the apparent word count.
    """
    cues: list[tuple[float, float, str]] = []
    cur = None
    for raw in path.read_text(errors="ignore").splitlines():
        line = raw.strip()
        m = TS.search(line)
        if m:
            if cur:
                cues.append(cur)
            cur = (secs(*m.groups()[:4]), secs(*m.groups()[4:]), "")
            continue
        if cur is None or not line or line.upper().startswith(("WEBVTT", "KIND:", "LANGUAGE:", "NOTE")):
            continue
        text = TAG.sub("", line).strip()
        if text:
            cur = (cur[0], cur[1], (cur[2] + " " + text).strip())
    if cur:
        cues.append(cur)

    # collapse rolling duplicates: drop text already fully contained in prev
    out: list[tuple[float, float, str]] = []
    for st, en, tx in cues:
        if not tx:
            continue
        if out and (tx in out[-1][2] or out[-1][2].endswith(tx)):
            continue
        if out and tx.startswith(out[-1][2]) and out[-1][2]:
            tx = tx[len(out[-1][2]):].strip()
            if not tx:
                continue
        out.append((st, en, tx))
    return out


def fetch_subs(target: str, workdir: Path) -> Path | None:
    workdir.mkdir(parents=True, exist_ok=True)
    tmpl = str(workdir / "%(id)s.%(ext)s")
    for args in (["--write-subs", "--sub-langs", "en.*"],
                 ["--write-auto-subs", "--sub-langs", "en.*"]):
        before = set(workdir.glob("*.vtt"))
        r = subprocess.run(
            ["yt-dlp", "-q", "--no-warnings", "--skip-download",
             "--sub-format", "vtt", *args, "-o", tmpl, target],
            capture_output=True, text=True)
        new = sorted(set(workdir.glob("*.vtt")) - before)
        if new:
            return new[0]
        if r.returncode != 0 and "Unsupported URL" in (r.stderr or ""):
            break
    return None


def analyse(cues) -> dict | None:
    if len(cues) < 5:
        return None
    speech = sum(max(0.0, e - s) for s, e, _ in cues)
    words = sum(len(t.split()) for _, _, t in cues)
    span = cues[-1][1] - cues[0][0]
    if speech <= 0 or span <= 0:
        return None

    rates, durs = [], []
    for s, e, t in cues:
        d = e - s
        w = len(t.split())
        if d >= 0.4 and w >= 2:
            rates.append(w / d * 60.0)
            durs.append(d)

    gaps = [max(0.0, cues[i + 1][0] - cues[i][1]) for i in range(len(cues) - 1)]
    return {
        "cues": len(cues),
        "span_s": round(span, 1),
        "speech_s": round(speech, 1),
        "words": words,
        "speech_density": round(speech / span, 3),
        "wpm_speaking": round(statistics.median(rates), 1) if rates else None,
        "wpm_wallclock": round(words / span * 60.0, 1),
        "cue_s_median": round(statistics.median(durs), 2) if durs else None,
        "cue_s_p90": round(sorted(durs)[int(len(durs) * 0.9)], 2) if durs else None,
        "gap_s_median": round(statistics.median(gaps), 2) if gaps else None,
        "gap_pct_over_1s": round(100 * sum(g > 1.0 for g in gaps) / len(gaps), 1) if gaps else None,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--list", type=Path, help="file of URLs or ytsearch1: queries")
    ap.add_argument("--query", action="append", default=[])
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()

    if not shutil.which("yt-dlp"):
        sys.exit("yt-dlp not found (uv tool install yt-dlp)")

    targets = list(args.query)
    if args.list:
        targets += [l.strip() for l in args.list.read_text().splitlines()
                    if l.strip() and not l.startswith("#")]
    if not targets:
        sys.exit("no targets")

    out = args.out
    subs = out / "subs"
    out.mkdir(parents=True, exist_ok=True)
    results = []

    for i, t in enumerate(targets, 1):
        name = t.replace("ytsearch1:", "")[:58]
        print(f"[{i}/{len(targets)}] {name}")
        vtt = fetch_subs(t, subs)
        if not vtt:
            print("    no subtitles")
            continue
        st = analyse(parse_vtt(vtt))
        if not st:
            print("    too few cues")
            continue
        st["target"] = t
        st["vtt"] = vtt.name
        results.append(st)
        print(f"    {st['wpm_speaking']} wpm speaking | "
              f"{st['speech_density']:.0%} speech | "
              f"cue {st['cue_s_median']}s | gap {st['gap_s_median']}s")

    if not results:
        sys.exit("nothing analysed")

    def med(k):
        vals = [r[k] for r in results if r.get(k) is not None]
        return round(statistics.median(vals), 2) if vals else None

    pooled = {
        "n_videos": len(results),
        "wpm_speaking_median": med("wpm_speaking"),
        "wpm_wallclock_median": med("wpm_wallclock"),
        "speech_density_median": med("speech_density"),
        "cue_s_median": med("cue_s_median"),
        "cue_s_p90_median": med("cue_s_p90"),
        "gap_s_median": med("gap_s_median"),
        "gap_pct_over_1s_median": med("gap_pct_over_1s"),
    }
    (out / "pacing.json").write_text(
        json.dumps({"pooled": pooled, "per_video": results}, indent=2))

    print("\n" + "=" * 62)
    print("  POOLED REFERENCE PACING")
    print("=" * 62)
    for k, v in pooled.items():
        print(f"  {k:<26} {v}")
    print(f"""
  How to use these numbers
    - Time each beat from its narration line at ~{pooled['wpm_speaking_median']} wpm.
    - Expect only ~{(pooled['speech_density_median'] or 0)*100:.0f}% of runtime to carry speech; the rest is
      deliberate silence. Do not fill it with more animation.
    - One spoken unit runs ~{pooled['cue_s_median']}s. That is the natural length of one
      visual beat — beats much longer than this need a sub-beat.
    - Effective wall-clock rate is ~{pooled['wpm_wallclock_median']} wpm; use that to sanity check
      total runtime against total script length.

  Saved: {out / 'pacing.json'}
""")
    return 0


if __name__ == "__main__":
    sys.exit(main())
