# Manim Video Quality

You have access to the manim-video-quality skill: creation craft and quality
measurement for Manim explainer videos.

## When to Use

- Writing or reviewing a Manim explainer scene
- Defining or applying a visual style for technical video
- Building or validating an LLM-based video quality grader
- Before reporting any quality score for a video

## Critical

**Do not trust an LLM video score that has not been validated.** Measured on a
real pipeline: a 1.90-point swing on a byte-identical video from prompt
metadata alone; Gemini samples video at 1 FPS and cannot see sub-second
motion; ~80% of a typical rubric is deterministically computable from the
scene source instead.

Read `SKILL.md`, then `reference/quality-spec.md` (rules + checks) and
`reference/gemini-video-analysis.md` (valid measurement protocol).

## Order of Checks

Cheapest and most exact first: static source analysis → OCR → frame analysis
→ LLM (narrative only) → human.
