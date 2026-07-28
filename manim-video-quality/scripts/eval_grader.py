#!/usr/bin/env python3
# /// script
# requires-python = ">=3.9"
# dependencies = ["google-genai"]
# ///
"""Meta-eval: measure whether an LLM video grader can actually see defects.

Ground truth is by construction — each pair is the same scene with exactly
one injected defect — so this produces a real detection score rather than a
self-assessment. Chance is 50%.

The output that matters is not a single accuracy number but a BLINDNESS MAP:
which defect classes the model reliably catches, and which it cannot see. A
grader that catches five of eight and is honest about which five is far more
useful than one claiming to catch all eight.

Protocol follows ../reference/gemini-video-analysis.md:
  - forced choice, never absolute scoring
  - every pair run in BOTH orders; a preference that flips with position is
    recorded as undecided rather than averaged away
  - clips are encode-identical and referred to only as A and B
  - no filenames, durations, or technical metadata reach the model
  - n seeds per order, variance reported

Usage:
  GOOGLE_CLOUD_PROJECT=... GOOGLE_CLOUD_LOCATION=global \
  GOOGLE_GENAI_USE_ENTERPRISE=true \
  python3 eval_grader.py --corpus DIR --out results.json [--seeds 2]
"""

from __future__ import annotations

import argparse
import json
import statistics
import sys
from pathlib import Path

MODEL = "gemini-3.1-flash-lite"

# defect -> the property the CLEAN clip should exhibit more of.
# Phrased so it never names the defect: naming it turns a perception test
# into a reading-comprehension test.
PAIRS = {
    "font_ttc_bug":  "correct, unbroken rendering of words",
    "rushed_pacing": "pacing that lets a viewer absorb each idea",
    "card_itis":     "a minimal, idea-first visual style rather than a software-UI look",
    "color_spray":   "disciplined, restrained use of colour",
    "text_flood":    "restraint in the amount of on-screen text",
    "light_bg":      "conformance to a dark, theatrical explainer aesthetic",
    "cut_not_morph": "visual continuity between related ideas",
    "overlap_nodes": "a clean layout with no colliding elements",
}

PROMPT = """You are shown two short videos, A and B.

They are the same animation and differ in exactly one respect.

Which one better exhibits: {prop}?

Reply with strict JSON and nothing else:
{{"choice": "A" or "B", "because": "<one sentence naming what you observed>"}}"""


def ask(client, types, prop: str, first: bytes, second: bytes, seed: int) -> tuple:
    parts = [
        types.Part.from_bytes(data=first, mime_type="video/mp4"),
        types.Part.from_bytes(data=second, mime_type="video/mp4"),
        PROMPT.format(prop=prop),
    ]
    r = client.models.generate_content(
        model=MODEL, contents=parts,
        config=types.GenerateContentConfig(temperature=0.0, seed=seed,
                                           max_output_tokens=300),
    )
    txt = (r.text or "").strip().removeprefix("```json").removeprefix("```")
    txt = txt.removesuffix("```").strip()
    try:
        d = json.loads(txt[txt.index("{"):txt.rindex("}") + 1])
        return d.get("choice", "").strip().upper()[:1], d.get("because", "")
    except Exception:
        return "", txt[:90]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--corpus", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--seeds", type=int, default=2)
    args = ap.parse_args()

    from google import genai
    from google.genai import types
    client = genai.Client()

    clean = (args.corpus / "none.mp4").read_bytes()
    results, rows = {}, []

    for defect, prop in PAIRS.items():
        vp = args.corpus / f"{defect}.mp4"
        if not vp.exists():
            print(f"  skip {defect}: missing", file=sys.stderr)
            continue
        bad = vp.read_bytes()

        correct = undecided = 0
        trials = 0
        notes = []
        for seed in range(args.seeds):
            # order 1: clean is A          -> correct answer "A"
            c1, w1 = ask(client, types, prop, clean, bad, seed)
            # order 2: clean is B          -> correct answer "B"
            c2, w2 = ask(client, types, prop, bad, clean, seed)
            trials += 1
            if not c1 or not c2:
                undecided += 1
                continue
            picked_clean_1 = (c1 == "A")
            picked_clean_2 = (c2 == "B")
            if picked_clean_1 != picked_clean_2:
                undecided += 1          # position-dependent: no real preference
            elif picked_clean_1:
                correct += 1
            notes.append(w1 or w2)

        decided = trials - undecided
        acc = (correct / decided) if decided else None
        results[defect] = {
            "trials": trials, "decided": decided, "undecided": undecided,
            "correct": correct, "accuracy": acc,
            "sample_reason": notes[0] if notes else "",
        }
        rows.append((defect, acc, undecided, trials, notes[0] if notes else ""))
        a = "n/a" if acc is None else f"{acc:.0%}"
        print(f"  {defect:<16} acc {a:>5}  undecided {undecided}/{trials}")

    decided_accs = [r["accuracy"] for r in results.values()
                    if r["accuracy"] is not None]
    overall = statistics.mean(decided_accs) if decided_accs else 0.0

    print("\n" + "=" * 66)
    print("  BLINDNESS MAP — which defects this grader can actually see")
    print("=" * 66)
    print(f"  {'defect':<16}{'acc':>6}  verdict")
    for defect, acc, und, tot, _ in sorted(
            rows, key=lambda r: (r[1] is None, -(r[1] or 0))):
        if acc is None:
            v = "NO SIGNAL (all position-dependent)"
        elif acc >= 0.85:
            v = "reliable — LLM is fine here"
        elif acc >= 0.6:
            v = "weak — corroborate"
        else:
            v = "BLIND — use a deterministic check"
        a = "n/a" if acc is None else f"{acc:.0%}"
        print(f"  {defect:<16}{a:>6}  {v}")
    print(f"\n  mean accuracy over decided pairs: {overall:.0%}   (chance 50%)")
    print(f"  bar for using this grader as a gate: 85%\n")

    args.out.write_text(json.dumps(
        {"model": MODEL, "seeds": args.seeds,
         "mean_accuracy": overall, "per_defect": results}, indent=2))
    print(f"  saved {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
