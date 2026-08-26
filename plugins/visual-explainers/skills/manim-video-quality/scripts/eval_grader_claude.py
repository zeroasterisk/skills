#!/usr/bin/env python3
# /// script
# requires-python = ">=3.9"
# dependencies = ["anthropic", "pillow"]
# ///
"""Keyframe-based visual grader using Anthropic Claude on Vertex AI.

Extracts keyframes from videos and uses Claude 3.5 Sonnet / Claude 3 Opus to grade
A/B pairs. Enforces strict position counterbalancing (A/B and B/A trials) to
measure and eliminate position bias.
"""

from __future__ import annotations

import argparse
import base64
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from anthropic import AnthropicVertex

# Credentials setup for Vertex AI
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = '/secrets/credentials/alanblount-sandbox.json'
PROJECT_ID = 'alanblount-sandbox'
REGION = 'global'

PAIRS = {
    "font_ttc_bug":  "correct, unbroken rendering of every word",
    "rushed_pacing": "pacing that gives a viewer time to absorb each idea",
    "card_itis":     "a minimal idea-first visual style rather than a software-UI look",
    "color_spray":   "disciplined, restrained use of colour",
    "text_flood":    "restraint in the amount of on-screen text",
    "light_bg":      "conformance to a dark, theatrical explainer aesthetic",
    "cut_not_morph": "visual continuity when one idea becomes another",
    "overlap_nodes": "a clean layout with no colliding or overlapping elements",
}

DETECT_PROMPT = """You are shown keyframes from two technical explainer videos, A and B.

They show the same animation and differ in exactly one respect.

Which better exhibits: {prop}?

Reply with strict JSON only — no markdown, no explanation outside the JSON:
{{"choice": "A" or "B", "because": "<one sentence: what you observed that decided it>"}}"""

def extract_keyframes(video_path: Path, workdir: Path) -> list[Path]:
    """Sample 3 frames evenly across the video duration."""
    # Scale to 640px wide to reduce token size and cost while retaining high resolution
    cmd = [
        "ffmpeg", "-v", "error", "-y", "-i", str(video_path),
        "-vf", "fps=1/5,scale=640:-1",
        str(workdir / "f_%04d.png")
    ]
    subprocess.run(cmd, check=False)
    return sorted(workdir.glob("f_*.png"))

def to_base64_image(image_path: Path) -> str:
    with open(image_path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")

def _parse(txt: str) -> tuple[str, str]:
    txt = txt.strip().removeprefix("```json").removeprefix("```")
    txt = txt.removesuffix("```").strip()
    try:
        i, j = txt.index("{"), txt.rindex("}") + 1
        d = json.loads(txt[i:j])
        return d.get("choice", "").strip().upper()[:1], d.get("because", "")
    except Exception:
        return "", txt[:90]

def query_claude(client, model_name: str, prompt: str, a_frames: list[Path], b_frames: list[Path]) -> tuple[str, str]:
    content = []
    
    # Add A's keyframes
    content.append({"type": "text", "text": "--- KEYFRAMES FOR VIDEO A ---"})
    for p in a_frames:
        content.append({
            "type": "image",
            "source": {
                "type": "base64",
                "media_type": "image/png",
                "data": to_base64_image(p)
            }
        })
        
    # Add B's keyframes
    content.append({"type": "text", "text": "--- KEYFRAMES FOR VIDEO B ---"})
    for p in b_frames:
        content.append({
            "type": "image",
            "source": {
                "type": "base64",
                "media_type": "image/png",
                "data": to_base64_image(p)
            }
        })
        
    content.append({"type": "text", "text": prompt})
    
    try:
        response = client.messages.create(
            model=model_name,
            max_tokens=600,
            messages=[{"role": "user", "content": content}]
        )
        text_resp = ""
        for block in response.content:
            if getattr(block, 'type', None) == 'text':
                text_resp += block.text
        return _parse(text_resp)
    except Exception as e:
        return "", str(e).split('\n')[0]

def run_pair(client, model_name: str, prompt: str, first_frames: list[Path], second_frames: list[Path], seeds: int) -> dict:
    correct = inverted = position_a = position_b = undecided = 0
    reasons = []
    
    for s in range(seeds):
        # Trial 1: first is A, second is B
        c1, w1 = query_claude(client, model_name, prompt, first_frames, second_frames)
        # Trial 2: second is A, first is B (counterbalanced)
        c2, w2 = query_claude(client, model_name, prompt, second_frames, first_frames)
        
        if not c1 or not c2:
            undecided += 1
            if w1:
                reasons.append(w1)
            continue
            
        chose_first_1 = (c1 == "A")
        chose_first_2 = (c2 == "B")
        
        if chose_first_1 and chose_first_2:
            correct += 1
        elif not chose_first_1 and not chose_first_2:
            inverted += 1
        elif c1 == "A" and c2 == "A":
            position_a += 1
        elif c1 == "B" and c2 == "B":
            position_b += 1
        else:
            undecided += 1
            
        if w1:
            reasons.append(w1)
            
    decided = seeds - undecided
    return {
        "seeds": seeds, "decided": decided, "undecided": undecided,
        "correct": correct, "inverted": inverted,
        "position_a": position_a, "position_b": position_b,
        "accuracy": (correct / decided) if decided else None,
        "sample_reason": reasons[0] if reasons else "",
    }

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--corpus", type=Path, required=True, help="dir with none.mp4 + defect clips")
    ap.add_argument("--out", type=Path, required=True, help="output JSON")
    ap.add_argument("--seeds", type=int, default=1, help="seeds to run per pair")
    ap.add_argument("--model", type=str, default="claude-sonnet-5", help="claude-sonnet-5 or claude-opus-5")
    args = ap.parse_args()
    
    client = AnthropicVertex(project_id=PROJECT_ID, region=REGION)
    
    # Temp dir for frame extraction
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        
        # 1. Extract frames for clean baseline (none.mp4)
        clean_mp4 = args.corpus / "none.mp4"
        if not clean_mp4.exists():
            sys.exit(f"none.mp4 not found in {args.corpus}")
            
        clean_dir = tmp_path / "none"
        clean_dir.mkdir()
        clean_frames = extract_keyframes(clean_mp4, clean_dir)
        
        results = {}
        print(f"\n  Claude Grader  model={args.model}  seeds={args.seeds}")
        print(f"  {'defect':<16}{'acc':>6}  {'undecided':>9}  reason")
        
        for defect, prop in PAIRS.items():
            defect_mp4 = args.corpus / f"{defect}.mp4"
            if not defect_mp4.exists():
                print(f"  {defect:<16}  skip (missing)")
                continue
                
            defect_dir = tmp_path / defect
            defect_dir.mkdir()
            defect_frames = extract_keyframes(defect_mp4, defect_dir)
            
            prompt = DETECT_PROMPT.format(prop=prop)
            r = run_pair(client, args.model, prompt, clean_frames, defect_frames, args.seeds)
            results[defect] = r
            
            a = "n/a" if r["accuracy"] is None else f"{r['accuracy']:.0%}"
            print(f"  {defect:<16}{a:>6}  {r['undecided']:>4}/{r['seeds']}  {r['sample_reason'][:70]}")
            
        decided = [r["accuracy"] for r in results.values() if r["accuracy"] is not None]
        overall = sum(decided) / len(decided) if decided else 0.0
        
        # Save output
        out_data = {
            "mode": "detect_claude", "model": args.model, "seeds": args.seeds,
            "mean_accuracy": overall, "per_defect": results
        }
        args.out.write_text(json.dumps(out_data, indent=2))
        print(f"\n  Saved results to {args.out}")
        
    return 0

if __name__ == "__main__":
    sys.exit(main())
