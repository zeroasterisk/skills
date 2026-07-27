#!/usr/bin/env python3
# /// script
# requires-python = ">=3.9"
# dependencies = []
# ///
"""Turn pairwise judgments into a ranking (Bradley-Terry, MM algorithm).

Input: judgments.json from judge_ui.py
Output: a ranked table of clips with strength scores, plus diagnostics that
tell you whether the ranking is trustworthy yet.

Bradley-Terry models P(i beats j) = s_i / (s_i + s_j) and fits the strengths
s by maximum likelihood. Ties count as half a win to each side. Fitted with
the standard minorize-maximize iteration, so no scipy needed.

Diagnostics reported, because a ranking without them is not evidence:
  - coverage: fraction of possible pairs actually judged
  - connectivity: whether the comparison graph is connected (if it splits
    into components, cross-component ordering is not identified at all)
  - transitivity violations: A>B>C>A cycles, which indicate either a noisy
    judge or a genuinely multi-dimensional quality space

Usage:
    python3 score_ranking.py judgments.json
    uv run score_ranking.py judgments.json --json
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from itertools import combinations
from pathlib import Path


def fit_bradley_terry(items, wins, iters=2000, tol=1e-10):
    """MM algorithm. wins[(i,j)] = times i beat j (ties add 0.5 each way)."""
    s = {i: 1.0 for i in items}
    total_wins = {i: sum(wins.get((i, j), 0.0) for j in items if j != i)
                  for i in items}
    played = defaultdict(float)
    for (i, j), w in wins.items():
        played[(i, j)] += w
        played[(j, i)] += w

    for _ in range(iters):
        prev = dict(s)
        for i in items:
            denom = 0.0
            for j in items:
                if i == j:
                    continue
                n_ij = played.get((i, j), 0.0)
                if n_ij:
                    denom += n_ij / (s[i] + s[j])
            if denom > 0 and total_wins[i] > 0:
                s[i] = total_wins[i] / denom
        # normalize (scale is unidentified)
        gm = sum(s.values()) / len(s)
        if gm > 0:
            s = {k: v / gm for k, v in s.items()}
        if max(abs(s[k] - prev[k]) for k in s) < tol:
            break
    return s


def connected_components(items, edges):
    parent = {i: i for i in items}

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    for a, b in edges:
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[ra] = rb
    groups = defaultdict(list)
    for i in items:
        groups[find(i)].append(i)
    return list(groups.values())


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("judgments", type=Path)
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    data = json.loads(args.judgments.read_text())
    js = data.get("judgments", [])
    if not js:
        sys.exit("No judgments yet.")

    items = sorted({j["left_id"] for j in js} | {j["right_id"] for j in js})
    wins: dict[tuple, float] = defaultdict(float)
    edges = set()
    n_tie = 0

    for j in js:
        a, b = j["left_id"], j["right_id"]
        edges.add((a, b))
        if j["choice"] == "tie":
            wins[(a, b)] += 0.5
            wins[(b, a)] += 0.5
            n_tie += 1
        else:
            w = j["winner_id"]
            l = b if w == a else a
            wins[(w, l)] += 1.0

    strengths = fit_bradley_terry(items, wins)
    ranked = sorted(items, key=lambda i: -strengths[i])

    # --- diagnostics -------------------------------------------------------
    judged_pairs = {tuple(sorted((j["left_id"], j["right_id"]))) for j in js}
    possible = list(combinations(items, 2))
    coverage = len(judged_pairs) / len(possible) if possible else 0.0
    comps = connected_components(items, edges)

    # transitivity: count cycles among decided head-to-heads
    def beats(a, b):
        wa, wb = wins.get((a, b), 0), wins.get((b, a), 0)
        return wa > wb
    cycles = 0
    for a, b, c in combinations(items, 3):
        for x, y, z in ((a, b, c), (a, c, b)):
            if beats(x, y) and beats(y, z) and beats(z, x):
                cycles += 1
    n_triads = len(list(combinations(items, 3)))

    # position bias: how often did the left-hand clip win?
    decided = [j for j in js if j["choice"] != "tie"]
    left_wins = sum(1 for j in decided if j["choice"] == "left")
    left_rate = left_wins / len(decided) if decided else 0.0

    out = {
        "n_judgments": len(js),
        "n_items": len(items),
        "coverage": round(coverage, 3),
        "ties": n_tie,
        "components": len(comps),
        "cycles": cycles,
        "triads": n_triads,
        "left_win_rate": round(left_rate, 3),
        "ranking": [{"rank": r + 1, "id": i, "strength": round(strengths[i], 4)}
                    for r, i in enumerate(ranked)],
    }

    if args.json:
        print(json.dumps(out, indent=2))
        return 0

    print(f"\n  Bradley-Terry ranking   ({len(js)} judgments, "
          f"{len(items)} clips, {coverage:.0%} pair coverage)\n")
    width = max(len(i) for i in items)
    top = strengths[ranked[0]] or 1.0
    for r, i in enumerate(ranked, 1):
        bar = "█" * max(1, round(20 * strengths[i] / top))
        print(f"  {r:>2}. {i:<{width}}  {strengths[i]:>7.3f}  {bar}")

    print("\n  Diagnostics")
    print(f"    pair coverage      {coverage:.0%}"
          f"   {'ok' if coverage >= 0.5 else 'LOW — ranking is under-determined'}")
    print(f"    graph components   {len(comps)}"
          f"   {'ok' if len(comps) == 1 else 'SPLIT — cross-group order not identified'}")
    print(f"    ties               {n_tie}")
    print(f"    intransitive triads {cycles}/{n_triads}"
          f"  {'ok' if cycles <= max(1, n_triads * 0.1) else 'HIGH — noisy or multi-dimensional'}")
    print(f"    left-win rate      {left_rate:.0%}"
          f"   {'ok' if 0.35 <= left_rate <= 0.65 else 'SKEWED — possible position bias'}")
    print()
    print("  Use this ranking as ground truth for grader validation")
    print("  (Spearman rho >= 0.7 — see reference/gemini-video-analysis.md §8).\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
