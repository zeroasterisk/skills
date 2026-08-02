#!/usr/bin/env python3
# /// script
# requires-python = ">=3.9"
# dependencies = ["google-genai"]
# ///
"""Meta-eval: measure LLM video grader validity two ways.

MODE 1 — defect detection (--corpus with ablation clips):
  Forced choice between clean and defected clip. Ground truth by
  construction. Produces a blindness map: which defect classes the model
  reliably catches vs. cannot see. Chance is 50%.

MODE 2 — reference ranking (--ref-corpus with 3b1b clips + --our-clips):
  Forced choice between a 3b1b clip and one of our renders. Ground truth
  by domain expertise: the reference should consistently win. Tests:
    - Does the grader agree the reference is better? (calibration)
    - Does it rate our best work higher than our worst? (discrimination)
    - Is the preference stable across clips from different 3b1b videos?
    - How much position bias remains after counterbalancing?

Protocol (both modes) — ../reference/gemini-video-analysis.md:
  - forced choice, never absolute 1-10 scoring
  - both orders A/B and B/A; flip = undecided, not averaged
  - clips identical encode, referred to only as A and B
  - no filenames, durations, metadata in the prompt
  - n seeds, SD reported

Usage:
  # Mode 1: defect detection
  python3 eval_grader.py --corpus DIR_with_ablations --out det.json

  # Mode 2: reference ranking (sample 20 ref clips, compare to our renders)
  python3 eval_grader.py --ref-corpus DIR_3b1b --our-clips a.mp4 b.mp4 \\
      --out rank.json --ref-sample 20
"""

from __future__ import annotations

import argparse
import json
import random
import statistics
import sys
from pathlib import Path

MODEL = "gemini-2.5-flash-lite"  # 2.5-flash truncates JSON at 300 tokens; lite is complete

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

DETECT_PROMPT = """You are shown two short silent videos, A and B.

They show the same animation and differ in exactly one respect.

Which better exhibits: {prop}?

Reply with strict JSON only — no markdown, no explanation outside the JSON:
{{"choice": "A" or "B", "because": "<one sentence: what you observed that decided it>"}}"""

RANK_PROMPT = """You are shown two short videos, A and B. Both are technical
explainer animations. Neither has audio.

Which is closer to the quality and style of a 3Blue1Brown educational video —
patient pacing, one clear idea per beat, minimal on-screen text, restrained
colour, clean layout?

Reply with strict JSON only:
{{"choice": "A" or "B", "because": "<one sentence naming what decided it>"}}"""


def _parse(txt: str) -> tuple[str, str]:
    txt = txt.strip().removeprefix("```json").removeprefix("```")
    txt = txt.removesuffix("```").strip()
    try:
        i, j = txt.index("{"), txt.rindex("}") + 1
        d = json.loads(txt[i:j])
        return d.get("choice", "").strip().upper()[:1], d.get("because", "")
    except Exception:
        return "", txt[:90]


def ask(client, types, prompt: str, a: bytes, b: bytes, seed: int) -> tuple[str, str]:
    import time
    for attempt in range(5):
        try:
            r = client.models.generate_content(
                model=MODEL,
                contents=[types.Part.from_bytes(data=a, mime_type="video/mp4"),
                          types.Part.from_bytes(data=b, mime_type="video/mp4"),
                          prompt],
                config=types.GenerateContentConfig(
                    temperature=0.0, seed=seed, max_output_tokens=600),
            )
            return _parse(r.text or "")
        except Exception as e:
            if "429" in str(e) or "RESOURCE_EXHAUSTED" in str(e):
                wait = 20 * (2 ** attempt)
                print(f"    429 rate limit, sleeping {wait}s (attempt {attempt+1}/5)...",
                      file=__import__("sys").stderr, flush=True)
                time.sleep(wait)
            else:
                raise
    return "", "rate-limit-exhausted"


def run_pair(client, types, prompt: str, first: bytes, second: bytes,
             seeds: int) -> dict:
    """Both orders, n seeds each.

    correct   = both orders picked FIRST (first is always the positive clip)
    inverted  = both orders picked SECOND (consistently wrong)
    position_a = always picked A regardless of which was first
    position_b = always picked B regardless
    undecided = parse failure or mixed
    """
    correct = inverted = position_a = position_b = undecided = 0
    reasons = []
    for s in range(seeds):
        c1, w1 = ask(client, types, prompt, first, second, s)   # first = A
        c2, w2 = ask(client, types, prompt, second, first, s)   # first = B
        if not c1 or not c2:
            undecided += 1
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


# ---------------------------------------------------------------------------
# Mode 1 — defect detection
# ---------------------------------------------------------------------------

def mode_detect(client, types, args) -> int:
    clean = (args.corpus / "none.mp4").read_bytes()
    results = {}
    print(f"\n  defect-detection  model={MODEL}  seeds={args.seeds}")
    print(f"  {'defect':<16}{'acc':>6}  {'undecided':>9}  reason")
    for defect, prop in PAIRS.items():
        vp = args.corpus / f"{defect}.mp4"
        if not vp.exists():
            print(f"  {defect:<16}  skip (missing)")
            continue
        prompt = DETECT_PROMPT.format(prop=prop)
        r = run_pair(client, types, prompt, clean, vp.read_bytes(), args.seeds)
        results[defect] = r
        a = "n/a" if r["accuracy"] is None else f"{r['accuracy']:.0%}"
        print(f"  {defect:<16}{a:>6}  {r['undecided']:>4}/{r['seeds']}  "
              f"{r['sample_reason'][:70]}")

    decided = [r["accuracy"] for r in results.values() if r["accuracy"] is not None]
    overall = statistics.mean(decided) if decided else 0.0
    print(f"\n  mean accuracy (decided pairs): {overall:.0%}  chance=50%")
    print(f"\n  BLINDNESS MAP")
    print(f"  {'defect':<16}{'acc':>6}{'corr':>6}{'inv':>5}{'pos_A':>6}{'und':>5}")
    for defect, r in sorted(results.items(),
                             key=lambda x: (x[1]["accuracy"] is None,
                                            -(x[1]["accuracy"] or 0))):
        a = r["accuracy"]
        if a is None:
            tag = "parse failure"
        elif a >= 0.85:
            tag = "reliable"
        elif a >= 0.60:
            tag = "weak"
        elif r["inverted"] > r["correct"]:
            tag = "INVERTED (prefers defect)"
        elif r["position_a"] + r["position_b"] > r["correct"]:
            tag = "POSITION BIAS"
        else:
            tag = "BLIND"
        print(f"  {defect:<16}"
              f"{'n/a' if a is None else f'{a:.0%}':>6}"
              f"{r['correct']:>6}{r['inverted']:>5}"
              f"{r['position_a']:>6}{r['undecided']:>5}"
              f"  {tag}")

    out = {"mode": "detect", "model": MODEL, "seeds": args.seeds,
           "mean_accuracy": overall, "per_defect": results}
    args.out.write_text(json.dumps(out, indent=2))
    print(f"\n  saved {args.out}")
    return 0


# ---------------------------------------------------------------------------
# Mode 2 — reference ranking
# ---------------------------------------------------------------------------

def mode_rank(client, types, args) -> int:
    clips = sorted(args.ref_corpus.glob("*.mp4"))
    if not clips:
        sys.exit(f"no .mp4 in {args.ref_corpus}")

    rng = random.Random(args.seed)
    sample = rng.sample(clips, min(args.ref_sample, len(clips)))
    our = [Path(p) for p in args.our_clips]

    print(f"\n  reference-ranking  model={MODEL}  seeds={args.seeds}")
    print(f"  {len(sample)} ref clips  x  {len(our)} our renders  "
          f"= {len(sample)*len(our)} pairs")

    rows = []
    for ref_path in sample:
        ref = ref_path.read_bytes()
        for our_path in our:
            our_b = our_path.read_bytes()
            r = run_pair(client, types, RANK_PROMPT, ref, our_b, args.seeds)
            r["ref"] = ref_path.name
            r["ours"] = our_path.name
            rows.append(r)
            a = "n/a" if r["accuracy"] is None else f"{r['accuracy']:.0%}"
            print(f"  {ref_path.stem:<30}  vs {our_path.stem:<22}  {a}")

    accs = [r["accuracy"] for r in rows if r["accuracy"] is not None]
    overall = statistics.mean(accs) if accs else 0.0
    decided_n = len(accs)
    total_n = len(rows)

    # stability: SD of per-ref-clip accuracy (high = the grader's judgment
    # shifts depending on which 3b1b clip it sees, not just our render)
    per_ref: dict[str, list] = {}
    for r in rows:
        per_ref.setdefault(r["ref"], []).append(r["accuracy"])
    per_ref_means = [
        statistics.mean([a for a in v if a is not None])
        for v in per_ref.values()
        if any(a is not None for a in v)
    ]
    ref_sd = statistics.stdev(per_ref_means) if len(per_ref_means) > 1 else 0.0

    print(f"\n  ref-wins {overall:.0%} of decided pairs  "
          f"({decided_n}/{total_n} decided)  "
          f"per-ref-clip SD {ref_sd:.2f}")
    if overall >= 0.80:
        print("  CALIBRATED — grader consistently prefers the reference")
    elif overall >= 0.60:
        print("  WEAK — marginal preference for reference")
    else:
        print("  UNCALIBRATED — reference does not consistently win")
    if ref_sd > 0.20:
        print("  WARNING — high per-clip SD: verdict varies with which 3b1b clip is used")

    out = {"mode": "rank", "model": MODEL, "seeds": args.seeds,
           "ref_sample": len(sample), "our_clips": [p.name for p in our],
           "ref_wins_pct": overall, "decided": decided_n, "total": total_n,
           "per_ref_sd": ref_sd, "rows": rows}
    args.out.write_text(json.dumps(out, indent=2))
    print(f"\n  saved {args.out}")
    return 0


# ---------------------------------------------------------------------------

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--corpus", type=Path, default=None,
                    help="dir with none.mp4 + defect clips (mode 1)")
    ap.add_argument("--ref-corpus", type=Path, default=None,
                    help="dir with 3b1b reference clips (mode 2)")
    ap.add_argument("--our-clips", nargs="+", type=Path, default=[],
                    help="our render clips to compare (mode 2)")
    ap.add_argument("--ref-sample", type=int, default=20,
                    help="how many ref clips to sample (mode 2)")
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--seeds", type=int, default=3)
    ap.add_argument("--seed", type=int, default=42,
                    help="RNG seed for ref-clip sampling")
    args = ap.parse_args()

    try:
        import os
        from google import genai
        from google.genai import types
    except ImportError:
        sys.exit("pip install google-genai")

    if os.environ.get('GOOGLE_APPLICATION_CREDENTIALS'):
        client = genai.Client(vertexai=True, project="alanblount-sandbox", location="us-central1")
    else:
        client = genai.Client()

    if args.corpus:
        return mode_detect(client, types, args)
    elif args.ref_corpus:
        if not args.our_clips:
            sys.exit("--our-clips required in rank mode")
        return mode_rank(client, types, args)
    else:
        sys.exit("--corpus or --ref-corpus required")


if __name__ == "__main__":
    sys.exit(main())
