# Dataset B — Ablation minimal pairs (ground truth by construction)

Purpose: **discriminative validity.** Can the grader tell a clean render
from the same render with exactly one known defect injected?

This is the strongest dataset we can build, because **we control the
renderer.** There is no labeling ambiguity: the defect is either injected or
it is not. Chance performance is exactly 50%.

Generator: `../scripts/ablation_scene.py`
Baseline = all flags off. Each ablation = exactly one flag on.

---

## The pairs

Each row yields one pair: `(baseline, ablated)`. The grader must prefer
`baseline` on the named property.

| id | flag | Defect injected | Spec rule violated | Model can see it at 1 FPS? |
|---|---|---|---|---|
| `B1-font` | `font_ttc_bug` | Helvetica Neue @ size 15 BOLD → phantom word gaps ("LangChain"→"Lang Chain") | C1, C2 | **Yes** (static text) |
| `B2-pacing` | `rushed_pacing` | all `run_time`×0.25, all `wait`×0.2 | D1, D2, D3 | Partly — via text-on-screen duration |
| `B3-cards` | `card_itis` | `fill_opacity` 0.12→0.95, add stroke weight → opaque UI cards | A2, A3 | **Yes** (static appearance) |
| `B4-color` | `color_spray` | 8 unreserved hues, Google Green used decoratively | B1, B2, B3 | **Yes** |
| `B5-text` | `text_flood` | 5 simultaneous labels, appearing with the visual not after | C3, C4, C6 | **Yes** |
| `B6-bg` | `light_bg` | background → `#F8F9FA`, text → dark | A1 | **Yes** |
| `B7-cuts` | `cut_not_morph` | every `Transform` → `FadeOut`+`FadeIn` | D4 | Marginal — likely blind |
| `B8-overlap` | `overlap_nodes` | two labeled nodes overlap by ~40% | A7 | **Yes** |

Deliberately included: `B2-pacing` and `B7-cuts` are the two we **expect the
grader to fail** on, because they are temporal and the model samples at
1 FPS. Including expected-failures is the point — the deliverable is a
*blindness map*, not a pass mark.

## Render protocol

All 9 renders (1 baseline + 8 ablations) must be **encode-identical**:

```bash
manim -qh --fps 60 ablation_scene.py AblationScene   # per flag via env var
ffmpeg -i in.mp4 -vf "scale=1920:1080,fps=60" -c:v libx264 -crf 20 -an out.mp4
```

Duration will differ for `B2-pacing` by construction (that *is* the defect).
For every other pair, pad the shorter to match so duration cannot be used as
a shortcut cue. Filenames must be opaque (`clip_a7f3.mp4`), not descriptive.

## Scoring protocol

Forced choice, counterbalanced (see `../reference/gemini-video-analysis.md` §4):

```
Two videos, A and B, differ in exactly one respect.
Which one better exhibits: <property>?
Answer "A" or "B", then one sentence naming what you observed.
```

Property phrasing per pair (do **not** name the defect):

| id | property asked |
|---|---|
| `B1-font` | "correct, unbroken text rendering" |
| `B2-pacing` | "pacing that lets a viewer absorb each idea" |
| `B3-cards` | "a minimal, idea-first visual style rather than a software-UI look" |
| `B4-color` | "disciplined, meaningful use of color" |
| `B5-text` | "restraint in on-screen text" |
| `B6-bg` | "conformance to a dark, theatrical explainer aesthetic" |
| `B7-cuts` | "visual continuity between related ideas" |
| `B8-overlap` | "clean layout with no colliding elements" |

Run each pair **twice** (A/B and B/A) × **3 seeds** = 6 calls/pair,
48 calls total. Cheap.

## Metrics

- **Per-pair accuracy** = fraction of counterbalanced runs preferring
  baseline. Order-inconsistent → `undecided`, not averaged.
- **Overall pairwise accuracy** — bar: ≥85%.
- **Blindness map** — any pair <60% ⇒ grader is blind to that defect class;
  route that rule to a deterministic `SRC`/`FRAME`/`OCR` check instead.
- **Order-flip rate** — bar: ≤10%.

## Expected outcome (pre-registered prediction)

Recording this *before* running, so the result can falsify it:

| pair | predicted |
|---|---|
| B1-font | high (≥90%) — static and visually obvious |
| B3-cards | high |
| B4-color | high |
| B5-text | high |
| B6-bg | very high — trivially visible |
| B8-overlap | high — though it scored 9/10 on a render with real overlaps, so possibly not |
| B2-pacing | **low (<60%)** — temporal, 1 FPS sampling |
| B7-cuts | **low (<60%)** — temporal |

If B1-font comes out low, that is decisive: it means the grader cannot
detect the exact defect class it already missed on v4, and all text-quality
judgments must move to OCR.

## Results

Record in `B_ablation_results.json` when run. Do not edit predictions above
after seeing results — add a "reconciliation" section instead.
