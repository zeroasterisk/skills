#!/usr/bin/env python3
# /// script
# requires-python = ">=3.9"
# dependencies = []
# ///
"""Build a normalized, blinded clip corpus for pairwise judging.

Takes reference videos (fetched from URLs) and local renders, cuts a short
excerpt from each, and normalizes every clip to an IDENTICAL encode so that
neither a human nor a model can infer quality from resolution, frame rate,
bitrate, duration, or filename.

Why this matters: an unnormalized corpus leaks. We measured a 1.90-point
score swing on a byte-identical video caused purely by stated FPS/resolution
metadata. See ../reference/gemini-video-analysis.md §2.

Clips are written with opaque names (clip_01.mp4 …) plus a manifest.json
mapping opaque name -> true id. The judge UI reads the manifest; the grader
should be given only the opaque names.

Requires: ffmpeg (always), yt-dlp (only if fetching remote refs).

Usage:
    python3 prep_corpus.py --spec corpus_spec.json --out ./corpus
    uv run prep_corpus.py --spec corpus_spec.json --out ./corpus
"""

from __future__ import annotations

import argparse
import json
import random
import shutil
import subprocess
import sys
from pathlib import Path

# Every clip is forced to exactly this. No exceptions — this is the point.
NORM = {
    "width": 1280,
    "height": 720,
    "fps": 30,
    "crf": 22,
    "seconds": 25,
}


def run(cmd: list[str], **kw) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, capture_output=True, text=True, **kw)


def have(binary: str) -> bool:
    return shutil.which(binary) is not None


def probe_duration(path: Path) -> float:
    r = run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
             "-of", "default=nw=1:nk=1", str(path)])
    try:
        return float(r.stdout.strip())
    except ValueError:
        return 0.0


def normalize(src: Path, dst: Path, start: float, seconds: int) -> bool:
    """Cut [start, start+seconds] and force the canonical encode.

    Audio is stripped: reference videos usually have narration and ours do
    not, which would otherwise be an obvious tell and an unfair channel.
    """
    vf = (f"scale={NORM['width']}:{NORM['height']}"
          f":force_original_aspect_ratio=decrease,"
          f"pad={NORM['width']}:{NORM['height']}:(ow-iw)/2:(oh-ih)/2:black,"
          f"fps={NORM['fps']},setsar=1")
    r = run([
        "ffmpeg", "-y", "-ss", str(start), "-t", str(seconds), "-i", str(src),
        "-vf", vf, "-c:v", "libx264", "-crf", str(NORM["crf"]),
        "-preset", "medium", "-pix_fmt", "yuv420p",
        "-movflags", "+faststart", "-an", str(dst),
    ])
    if r.returncode != 0:
        print(f"    ffmpeg failed: {r.stderr.strip().splitlines()[-1:]}",
              file=sys.stderr)
    return r.returncode == 0 and dst.exists()


def fetch_remote(query_or_url: str, dst: Path, start: str, seconds: int) -> bool:
    """Fetch a section of a remote video. Accepts a URL or 'ytsearch1:...'."""
    if not have("yt-dlp"):
        print("    yt-dlp not installed — skipping remote fetch",
              file=sys.stderr)
        return False
    end = f"{int(start.split(':')[0])*60 + int(start.split(':')[1]) + seconds + 5}"
    r = run([
        "yt-dlp", "-q", "--no-warnings",
        "-f", "bestvideo[height<=1080][ext=mp4]/bestvideo[height<=1080]/best",
        "--merge-output-format", "mp4",
        "--download-sections", f"*{start}-{end}s",
        "--force-keyframes-at-cuts",
        "-o", str(dst), query_or_url,
    ])
    if r.returncode != 0:
        print(f"    yt-dlp failed: {r.stderr.strip().splitlines()[-3:]}",
              file=sys.stderr)
    return dst.exists()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--spec", type=Path, required=True,
                    help="JSON list of corpus entries")
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--seed", type=int, default=1337,
                    help="controls opaque-name shuffle (record it)")
    args = ap.parse_args()

    if not have("ffmpeg"):
        sys.exit("ffmpeg is required and was not found on PATH")

    spec = json.loads(args.spec.read_text())
    out = args.out
    out.mkdir(parents=True, exist_ok=True)
    raw = out / "_raw"
    raw.mkdir(exist_ok=True)

    entries = list(spec["clips"])
    rng = random.Random(args.seed)
    rng.shuffle(entries)   # opaque index order is randomized, then frozen

    manifest = {"seed": args.seed, "normalization": NORM, "clips": []}
    ok = 0

    for i, e in enumerate(entries, 1):
        opaque = f"clip_{i:02d}.mp4"
        dst = out / opaque
        print(f"[{i}/{len(entries)}] {e['id']} -> {opaque}")

        if dst.exists():
            print("    already present, skipping")
            manifest["clips"].append({**e, "file": opaque})
            ok += 1
            continue

        if e.get("source") == "local":
            src = Path(e["path"]).expanduser()
            if not src.exists():
                print(f"    MISSING local file: {src}", file=sys.stderr)
                continue
            dur = probe_duration(src)
            start = e.get("start")
            if start is None:
                # default: begin ~20% in, so we skip title cards
                start = max(0.0, min(dur * 0.2, max(0.0, dur - NORM["seconds"])))
            if not normalize(src, dst, float(start), NORM["seconds"]):
                continue
        else:
            tmp = raw / f"{e['id']}.mp4"
            if not tmp.exists():
                if not fetch_remote(e["query"], tmp, e.get("start", "0:30"),
                                    NORM["seconds"]):
                    continue
            if not normalize(tmp, dst, float(e.get("trim", 2)), NORM["seconds"]):
                continue

        manifest["clips"].append({**e, "file": opaque})
        ok += 1

    (out / "manifest.json").write_text(json.dumps(manifest, indent=2))
    print(f"\n{ok}/{len(entries)} clips ready in {out}")
    print(f"manifest: {out / 'manifest.json'}")
    if ok < 2:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
