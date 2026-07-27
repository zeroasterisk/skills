#!/usr/bin/env python3
# /// script
# requires-python = ">=3.9"
# dependencies = []
# ///
"""Measure on-screen text density by OCRing sampled frames.

Answers, from data rather than opinion: how much text does a video actually
put on screen, and how does that compare to what its narrator is saying?

The point is to avoid asking a human a question the reference already
answers. If you want to know "should on-screen text be sparse anchors or
full captions", do not run a preference study first — measure what the
target style does, and only escalate to a human for what measurement cannot
settle.

Metrics per video:
  words_on_screen_median  typical word count visible in a frame
  text_frame_pct          share of frames carrying any text at all
  onscreen_to_spoken      on-screen words per spoken word, when a subtitle
                          file is supplied. ~1.0 means the screen is
                          duplicating the narration (verbatim captions);
                          well under 1.0 means anchors/labels.

Deterministic: tesseract only, no model, no API, no variance.

Usage:
    python3 measure_text_density.py --videos ref/*.mp4 --out density.json
    python3 measure_text_density.py --videos a.mp4 --subs a.vtt
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import statistics
import subprocess
import sys
import tempfile
from pathlib import Path

TS = re.compile(r"(\d{2}):(\d{2}):(\d{2})[.,](\d{3})\s*-->")
WORD = re.compile(r"[A-Za-z][A-Za-z'\-]{1,}")


def need(binary: str) -> None:
    if not shutil.which(binary):
        sys.exit(f"{binary} not found on PATH")


def sample_frames(video: Path, workdir: Path, every: float) -> list[Path]:
    out = workdir / "f_%04d.png"
    subprocess.run(
        ["ffmpeg", "-v", "error", "-i", str(video),
         "-vf", f"fps=1/{every},scale=1280:-1", str(out)],
        check=False, capture_output=True)
    return sorted(workdir.glob("f_*.png"))


def ocr_words(frame: Path) -> list[str]:
    r = subprocess.run(["tesseract", str(frame), "stdout", "--psm", "11"],
                       capture_output=True, text=True)
    # psm 11 = sparse text; suited to a few labels scattered on a dark frame.
    return WORD.findall(r.stdout)


def spoken_words(vtt: Path) -> int:
    txt, count = vtt.read_text(errors="ignore"), 0
    prev = ""
    for line in txt.splitlines():
        s = line.strip()
        if not s or TS.search(s) or s.upper().startswith(
                ("WEBVTT", "KIND:", "LANGUAGE:", "NOTE")):
            continue
        s = re.sub(r"<[^>]+>", "", s).strip()
        if not s or s == prev or s in prev:
            continue
        count += len(s.split())
        prev = s
    return count


def duration(video: Path) -> float:
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries",
                        "format=duration", "-of", "default=nw=1:nk=1",
                        str(video)], capture_output=True, text=True)
    try:
        return float(r.stdout.strip())
    except ValueError:
        return 0.0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--videos", nargs="+", type=Path, required=True)
    ap.add_argument("--subs", type=Path, default=None,
                    help="optional .vtt for the single video given")
    ap.add_argument("--every", type=float, default=1.0,
                    help="seconds between sampled frames")
    ap.add_argument("--out", type=Path, default=None)
    args = ap.parse_args()

    need("ffmpeg"); need("ffprobe"); need("tesseract")

    results = []
    for v in args.videos:
        if not v.exists():
            print(f"  missing {v}", file=sys.stderr)
            continue
        with tempfile.TemporaryDirectory() as td:
            frames = sample_frames(v, Path(td), args.every)
            if not frames:
                print(f"  no frames from {v.name}", file=sys.stderr)
                continue
            counts = [len(ocr_words(f)) for f in frames]

        dur = duration(v)
        with_text = [c for c in counts if c > 0]
        rec = {
            "video": v.name,
            "duration_s": round(dur, 1),
            "frames": len(counts),
            "text_frame_pct": round(100 * len(with_text) / len(counts), 1),
            "words_on_screen_median": (
                round(statistics.median(with_text), 1) if with_text else 0),
            "words_on_screen_p90": (
                sorted(with_text)[int(len(with_text) * 0.9)] if with_text else 0),
            "words_on_screen_max": max(counts) if counts else 0,
        }
        if args.subs and args.subs.exists() and len(args.videos) == 1:
            sw = spoken_words(args.subs)
            osw = sum(counts)          # summed across sampled frames
            rec["spoken_words"] = sw
            rec["onscreen_to_spoken"] = round(osw / sw, 3) if sw else None
        results.append(rec)
        print(f"  {v.name:<22} text in {rec['text_frame_pct']:>5.1f}% of frames | "
              f"median {rec['words_on_screen_median']:>4} words | "
              f"p90 {rec['words_on_screen_p90']:>3}")

    if not results:
        sys.exit("nothing measured")

    pooled = {
        "n": len(results),
        "text_frame_pct_median": round(
            statistics.median(r["text_frame_pct"] for r in results), 1),
        "words_on_screen_median": round(
            statistics.median(r["words_on_screen_median"] for r in results), 1),
        "words_on_screen_p90_median": round(
            statistics.median(r["words_on_screen_p90"] for r in results), 1),
    }
    print("\n  POOLED")
    for k, val in pooled.items():
        print(f"    {k:<28} {val}")

    m = pooled["words_on_screen_median"]
    print(f"""
  Interpretation
    A frame carrying ~{m:.0f} words is a LABEL/ANCHOR regime, not captions.
    A verbatim caption of narration at ~205 wpm would put roughly 10-14
    words on screen at once. If the measured median is far below that, the
    reference style is anchoring terms, not transcribing speech.""")

    if args.out:
        args.out.write_text(json.dumps(
            {"pooled": pooled, "per_video": results}, indent=2))
        print(f"\n  saved {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
