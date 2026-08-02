#!/usr/bin/env python3
# /// script
# requires-python = ">=3.9"
# dependencies = []
# ///
"""Regression test: does the checker still detect each injected defect?

Ground truth is by construction — every fixture in fixtures/ contains exactly
one known defect, so this is a real detection score, not a self-assessment.

It also guards the two things most likely to rot silently:
  - false positives on the clean baseline
  - a check that stops firing because the scene was written slightly
    differently (a documented helper, a comprehension, an imported constant
    — each of these caused a real miss during development)

Run:  python3 tests/test_detection.py
Exit: 0 if detection matches expectations, 1 otherwise.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CHECK = ROOT / "scripts" / "check_quality.py"
FIX = Path(__file__).resolve().parent / "fixtures"

# fixture -> rule that MUST fire (None = clean baseline)
EXPECT = {
    "none": None,
    "font_ttc_bug": "C2",
    "rushed_pacing": "D2",
    "card_itis": "A2",
    "color_spray": "B1",
    "text_flood": "C3",
    "light_bg": "A1",
    "cut_not_morph": "D4",
    # A7 (spatial overlap) is a documented gap: not statically checkable.
    # Listed so the omission stays visible rather than being quietly dropped.
    "overlap_nodes": None,
}
KNOWN_GAPS = {"overlap_nodes": "A7 — needs layout simulation or frame CV"}

# The clean baseline legitimately warns C2: Roboto at 15/BOLD measures 0.64 of
# a space, which is visibly loose (confirmed at 4K). A true positive, not noise.
BASELINE_ALLOWED = {"C2"}


def fired(fixture: Path) -> set[str]:
    r = subprocess.run([sys.executable, str(CHECK), "--scene", str(fixture),
                        "--json"], capture_output=True, text=True)
    try:
        text = r.stdout
        if "{" in text:
            text = text[text.find("{"):]
        d = json.loads(text)
    except json.JSONDecodeError:
        print(f"DEBUG: JSONDecodeError on {fixture.name}. Raw stdout:\n{r.stdout}")
        return set()
    return {f["rule"] for f in d["findings"]
            if f["severity"] in ("BLOCK", "WARN")}


def main() -> int:
    if not FIX.exists():
        sys.exit(f"no fixtures at {FIX} — run tests/materialize_ablations.py")

    detected = total = 0
    failures: list[str] = []
    print(f"\n  {'fixture':<16}{'expect':<8}{'fired':<26}verdict")
    for name, rule in EXPECT.items():
        fp = FIX / f"abl_{name}.py"
        if not fp.exists():
            failures.append(f"{name}: fixture missing")
            continue
        got = fired(fp)
        shown = ",".join(sorted(got)) or "-"

        if rule is None:
            if name in KNOWN_GAPS:
                verdict = "known gap"
            else:
                extra = got - BASELINE_ALLOWED
                verdict = "clean" if not extra else f"FALSE POSITIVE {sorted(extra)}"
                if extra:
                    failures.append(f"{name}: unexpected {sorted(extra)}")
        else:
            total += 1
            if rule in got:
                detected += 1
                verdict = "CAUGHT"
            else:
                verdict = "MISSED"
                failures.append(f"{name}: {rule} did not fire")
        print(f"  {name:<16}{rule or '-':<8}{shown:<26}{verdict}")

    print(f"\n  detection: {detected}/{total} injected defects")
    for g, why in KNOWN_GAPS.items():
        print(f"  known gap: {g} — {why}")
    if failures:
        print("\n  FAILURES")
        for f in failures:
            print(f"    {f}")
        return 1
    print("  all expectations met\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
