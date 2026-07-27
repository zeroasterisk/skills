#!/usr/bin/env python3
"""Experiment: does stated FPS metadata move the QA score on an IDENTICAL video?

Hypothesis (H1): video_qa.py's build_context() appends auto-detected metadata
(FPS, resolution, file size) to the grader prompt. Gemini samples video at
1 FPS regardless, so it CANNOT perceive 15fps-vs-60fps playback smoothness.
Therefore any score difference attributable to the stated FPS is confabulated
from reading the number, not from observing the video.

Design: one video file, one prompt, N runs per condition. Conditions differ
ONLY in the metadata text block. If scores move, metadata leaks into the grade.

  cond_A_true60   — metadata says FPS: 60   (true)
  cond_B_false15  — metadata says FPS: 15   (false; same 60fps file)
  cond_C_none     — no metadata block at all

Usage:
  GOOGLE_CLOUD_PROJECT=... GOOGLE_CLOUD_LOCATION=global \
  GOOGLE_GENAI_USE_ENTERPRISE=true \
  python exp_metadata_leakage.py VIDEO.mp4 --runs 3
"""

from __future__ import annotations

import argparse
import json
import re
import statistics
import sys
from pathlib import Path

PASS1_PROMPT = (
    Path.home()
    / "Workspaces/open-source/OpenMontage/.claude/skills/video-qa/prompts/pass1_visual_designer.md"
)

BASE_CONTEXT = """Title: Workload Identity Ceremony (style pilot)
Target audience: Developers and architects evaluating AI agent platforms.
Purpose / intended message: Show that an agent's workload identity is issued
at process start, before any request arrives.
Visual style: Dark background minimalist technical explainer; thin stroked
geometry; sparse text; deliberate pacing."""

CONDITIONS = {
    "A_true60": BASE_CONTEXT + """

Auto-detected video metadata:
Duration: 35.1
Codec: h264
Width: 1920
Height: 1080
FPS: 60.0
File size (MB): 2.1""",
    "B_false15": BASE_CONTEXT + """

Auto-detected video metadata:
Duration: 35.1
Codec: h264
Width: 480
Height: 270
FPS: 15.0
File size (MB): 0.4""",
    "C_none": BASE_CONTEXT,
}


def parse_scores(raw: str) -> dict:
    text = re.sub(r"^```(?:json)?\s*\n?", "", raw.strip(), flags=re.MULTILINE)
    text = re.sub(r"\n?```\s*$", "", text.strip(), flags=re.MULTILINE)
    m = re.search(r"\{.*\}", text, re.DOTALL)
    if not m:
        return {}
    try:
        data = json.loads(m.group(0))
    except json.JSONDecodeError:
        return {}
    dims = data.get("dimensions", {})
    out = {}
    for k, v in dims.items():
        if isinstance(v, dict) and "score" in v:
            try:
                out[k] = int(v["score"])
            except (TypeError, ValueError):
                pass
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("video", type=Path)
    ap.add_argument("--runs", type=int, default=3)
    args = ap.parse_args()

    from google import genai
    from google.genai import types

    client = genai.Client()
    prompt_tpl = PASS1_PROMPT.read_text()

    # Vertex/enterprise client has no Files API — use inline bytes, same as
    # video_qa.py's fallback path. Identical bytes every request.
    print(f"Loading {args.video.name} ({args.video.stat().st_size/1e6:.1f} MB) "
          f"as inline bytes…", file=sys.stderr)
    video_bytes = args.video.read_bytes()
    video_part = types.Part.from_bytes(data=video_bytes, mime_type="video/mp4")

    results: dict[str, list[dict]] = {k: [] for k in CONDITIONS}

    for cond, ctx in CONDITIONS.items():
        prompt = prompt_tpl.replace("{{ CONTEXT }}", ctx)
        for i in range(args.runs):
            resp = client.models.generate_content(
                model="gemini-3.1-flash-lite",
                contents=[video_part, prompt],
                config=types.GenerateContentConfig(
                    temperature=0.1, max_output_tokens=2048
                ),
            )
            scores = parse_scores(resp.text)
            if scores:
                avg = round(sum(scores.values()) / len(scores), 2)
                scores["_avg"] = avg
                results[cond].append(scores)
                print(f"  {cond} run{i+1}: avg={avg}  "
                      f"polish={scores.get('professional_polish')}  "
                      f"transition={scores.get('transition_quality')}",
                      file=sys.stderr)
            else:
                print(f"  {cond} run{i+1}: PARSE FAIL", file=sys.stderr)

    print("\n" + "=" * 68)
    print("RESULT — identical video, metadata text varied")
    print("=" * 68)
    print(f"{'condition':<14} {'n':>2} {'avg':>6} {'sd':>6} "
          f"{'polish':>7} {'trans':>6}")
    summary = {}
    for cond, runs in results.items():
        if not runs:
            continue
        avgs = [r["_avg"] for r in runs]
        pol = [r.get("professional_polish", 0) for r in runs]
        tra = [r.get("transition_quality", 0) for r in runs]
        sd = round(statistics.stdev(avgs), 3) if len(avgs) > 1 else 0.0
        summary[cond] = {
            "mean_avg": round(statistics.mean(avgs), 2),
            "sd_avg": sd,
            "mean_polish": round(statistics.mean(pol), 2),
            "mean_transition": round(statistics.mean(tra), 2),
            "n": len(runs),
        }
        print(f"{cond:<14} {len(runs):>2} {summary[cond]['mean_avg']:>6} "
              f"{sd:>6} {summary[cond]['mean_polish']:>7} "
              f"{summary[cond]['mean_transition']:>6}")

    if "A_true60" in summary and "B_false15" in summary:
        delta = summary["A_true60"]["mean_avg"] - summary["B_false15"]["mean_avg"]
        within = max(s["sd_avg"] for s in summary.values())
        print(f"\nΔ(stated 60fps − stated 15fps) = {delta:+.2f} points")
        print(f"max within-condition SD          = {within:.3f}")
        if abs(delta) > max(0.3, 2 * within):
            print("\n=> METADATA LEAKAGE CONFIRMED. The grader's score moves on")
            print("   an identical artifact when only the stated FPS/resolution")
            print("   changes. Gemini samples at 1 FPS and cannot perceive")
            print("   playback frame rate — this difference is confabulated.")
        else:
            print("\n=> No significant leakage detected at this n.")

    out = Path(__file__).parent / "exp_metadata_leakage_results.json"
    out.write_text(json.dumps({"summary": summary, "raw": results}, indent=2))
    print(f"\nSaved: {out}")


if __name__ == "__main__":
    main()
