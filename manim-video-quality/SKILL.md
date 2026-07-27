---
name: manim-video-quality
description: Define, create, and validly measure the quality of Manim explainer videos. Use when producing technical explainer videos, defining a visual style, reviewing a render, or building/validating an LLM-based video quality grader. Covers the 3Blue1Brown-inspired visual style system, shared storytelling vocabulary, a testable quality spec, and evaluation datasets that measure whether your grader can actually see what it claims to judge.
---

# Manim Video Quality

Creation craft and quality measurement for Manim explainer videos, kept in
**one** skill on purpose: the quality spec is a single list read two ways —
as creation rules when you build, and as review probes when you grade.

## When to use this

- Writing or reviewing a Manim explainer scene
- Defining or applying a visual style for technical video
- Reviewing a render, or deciding whether a render is shippable
- Building, fixing, or validating an LLM-based video grader
- Any time you are about to report a quality score for a video

## Read this first: the grader you have is probably not valid

This skill exists because a working, confident-looking two-pass Gemini QA
pipeline turned out to be measuring almost nothing. Measured failures:

| Failure | Evidence |
|---|---|
| **Metadata leakage** | Score moved **1.90 points on a byte-identical video** (7.56 → 5.66, within-condition SD ≈0.2) purely by changing the stated FPS/resolution text in the prompt. Repro: `scripts/exp_metadata_leakage.py` |
| **Cannot see motion** | Gemini samples video at **1 FPS** by default. Sub-second beats are never received. Judgments about frame rate, easing, and transition smoothness are confabulated. |
| **Ignored its own hard rule** | Rubric said mis-rendered glyphs force the dimension ≤4; a render with four mis-rendered words scored `text_readability: 9/10`. |
| **Score coaching** | Same video: 4.7 with no context file, 8.3 with one written *after* seeing the 4.7 containing "do not penalize…". |
| **Wrong tool for the job** | ~80% of the rubric (font, opacity, stroke width, run_times, colors/frame, overlap, on-screen duration) is deterministically computable from source or frames — it was never an LLM question. |

**Consequence:** treat any LLM video score as advisory until it has passed
the validation bars in `reference/gemini-video-analysis.md` §8.

## Reference files

| File | Use |
|---|---|
| `reference/quality-spec.md` | **The core.** Every quality rule with a check, typed `SRC`/`FRAME`/`OCR`/`LLM`/`HUMAN`. Read as creation rules when building; as probes when reviewing. |
| `reference/gemini-video-analysis.md` | How to run Gemini video analysis so the result is valid — 1 FPS limits, metadata stripping, forced choice, counterbalancing, blinding, banned context phrases, validation bars. |
| `reference/storytelling-vocabulary.md` | Shared terms: beat, vignette, pillar, aha moment, payoff, persistence contract, chaos-to-order arc, morph, camera reveal, reserved color, card-itis. Use these in feedback so iterations converge. |
| `reference/style-3b1b-google.visual-style.md` | A concrete `visual-style.md` instance: 3Blue1Brown grammar with Google brand colors reserved for semantic meaning. Swap for your own style file; the spec and datasets are style-agnostic. |

## Datasets

| File | Ground truth | Answers |
|---|---|---|
| `datasets/A_reference_corpus.md` | Human labels | Does the grader agree with a human ranking? Does real 3b1b even pass your rubric? |
| `datasets/B_ablation_pairs.md` | **By construction** | Can it tell a clean render from the same render with one injected defect? Chance = 50%. |
| `datasets/C_defect_probes.md` | Verifiable | Can it *see* specific objective defects? Includes a sycophancy probe. |

Generator: `scripts/ablation_scene.py` — one scene, 8 injectable defects, one
flag each. Baseline = all off.

```bash
ABLATION=none          manim -qh --fps 60 scripts/ablation_scene.py AblationScene
ABLATION=font_ttc_bug  manim -qh --fps 60 scripts/ablation_scene.py AblationScene
# flags: font_ttc_bug rushed_pacing card_itis color_spray
#        text_flood light_bg cut_not_morph overlap_nodes
```

## Workflow

**Creating**
1. Pick/author a style file. Pre-register intent (the one-sentence aha, per-beat
   ideas, licensed reserved colors, verbatim expected text) — frozen, before rendering.
2. Build to `reference/quality-spec.md`. Most rules are things you can just
   *do correctly* rather than check later.
3. Render `-ql` for layout/timing correctness only. **Do not judge visual
   quality from a `-ql` render** — and never let a grader see its metadata.

**Checking** — cheapest first, LLM last
1. `SRC` checks: static analysis of the scene `.py` (font, opacity, stroke,
   run_times, waits, colors). Exact, free, no model.
2. `OCR` check: transcribe rendered labels, diff against source string
   literals. Catches the phantom-gap class the LLM scored 9/10.
3. `FRAME` checks: overlap, negative-space ratio, colors-per-frame, contrast.
4. `LLM`: only narrative/perceptual questions (spec section E).
5. `HUMAN`: the actual ship decision.

## Hard-won facts

- **Font:** macOS `.ttc` collections (Helvetica Neue, Arial, Times) inject
  phantom spaces inside compound words in ManimCE/Pango at some size+weight
  combos — `LangChain` → `Lang Chain`, `Pydantic` → `Pyd antic`. **Roboto is
  clean.** Always spot-check a new font by rendering
  `LangChain Pydantic OpenClaw BigQuery Antigravity` at your actual node size
  and weight, at high resolution.
- **Pacing:** software-demo timing (0.2–0.6s) reads as frantic for idea-first
  explainer content. 1.5–3s for anything readable; 2–4s of stillness after a
  key beat.
- **Card-itis:** opaque, shadowed `RoundedRectangle`s make Manim look like a
  dashboard mockup. Keep `fill_opacity` ≤0.20 and let the background show.
- **`Transform` residue:** after `Transform(src, dst)`, `src` remains on
  screen. Include it in FadeOut groups.
- **Persistence contract:** if a later scene is meant to be "the same thing,
  transformed," `save_state()` + dim + `Restore()` the *same* mobjects. Never
  `FadeOut` and rebuild — the payoff reads as a new diagram instead.
- **Archive render + source together, per version.** A version whose source
  was overwritten cannot be re-measured.

## Anti-patterns

- Reporting a score from an unvalidated grader as if it means something
- Editing a context file after seeing a low score (that is p-hacking)
- Putting "do not penalize…" in a context file
- Asking an LLM to judge frame rate, easing, or sub-second timing
- Judging visual quality from a low-quality preview render
- A single score with no variance — always n≥3, report SD
