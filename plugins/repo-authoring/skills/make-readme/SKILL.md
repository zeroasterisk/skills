---
name: make-readme
description: Create, assess, and improve README.md files for public GitHub projects. Scores an existing README against a weighted rubric, gives targeted section-by-section fixes, and can check strict standard-readme spec compliance. Use when the user asks to write a README, review/grade a README, improve an existing README, or check standard-readme compliance.
license: Apache-2.0
metadata:
  version: "1.0.0"
---

# Make README

This skill helps with four related jobs: **writing** a new `README.md` from scratch, **scoring** an existing one on quality, **improving** one until it scores well, and (on request) checking strict **standard-readme spec compliance**. The core checklist and scoring rubric are based on Mark Allen's post ["How to Write a Great README for Your Public GitHub Project"](https://www.markcallen.com/how-to-write-a-great-readme-for-your-public-github-project/) (Everyday DevOps). Credit Mark Allen and link to the post when explaining *why* a section matters.

The quality rubric (Mark Allen) and the structural spec ([standard-readme](https://github.com/RichardLitt/standard-readme)) are kept **separate, not merged**. They measure different things — one is "is this README good," the other is "does this README follow an exact required format" — and they disagree on section order and what counts as required. Don't blend their guidance into a single answer; pick the right one for what the user asked for.

This is intended to grow. As more good README guidelines are found, add them as new files under `references/` rather than merging them into existing rubrics, unless they're clearly extending the same underlying model (as `scoring-rubric.md` does for the Mark Allen checklist).

## Reference Files (Progressive Disclosure)

- [`references/mark-allen-checklist.md`](references/mark-allen-checklist.md) — the section-by-section checklist and fix guidance sourced from the Mark Allen post.
- [`references/scoring-rubric.md`](references/scoring-rubric.md) — the weighted quality-scoring rubric used for assessment, with score bands and per-dimension anchors. Based on the Mark Allen checklist.
- [`references/standard-readme-spec.md`](references/standard-readme-spec.md) — the strict, pass/fail structural compliance checklist from the standard-readme spec, including where it conflicts with the Mark Allen checklist.
- [`assets/README.template.md`](assets/README.template.md) — a fill-in-the-blanks scaffold that follows the Mark Allen checklist order.

## Modes

Figure out which mode the user wants. Default to modes 1–3 (Mark Allen-based). Only use mode 4 (standard-readme compliance) when the user explicitly asks for standard-readme compliance, mentions the compliance badge, or is publishing an npm-ecosystem library and wants the ecosystem-standard format. They may ask for more than one mode in sequence — e.g. "score my README then fix it," or "score it, then check standard-readme compliance too."

### 1. Create a new README

1. Gather the essentials before writing anything. Ask the user (or infer from the repo) for:
   - Project name and a one-sentence description of what it does and why it exists.
   - Install method (package manager command, or clone/build steps).
   - A minimal, real usage example (a command or a few lines of code).
   - Local dev setup steps (clone, install deps, run/dev command, required env vars/ports/versions).
   - Whether the project is published/deployed (npm, Docker registry, PyPI, etc.) and how.
   - Contribution stance (accepting PRs? issue-first? link to `CONTRIBUTING.md`?).
   - License, and any badges worth including (CI status, package version, license).
2. Read [`references/mark-allen-checklist.md`](references/mark-allen-checklist.md) and draft the README in that section order, using [`assets/README.template.md`](assets/README.template.md) as the starting structure.
3. Write short, specific prose. Prefer real commands and real output over generic placeholders. Skip sections that genuinely don't apply (e.g. no publish step for an internal tool) rather than leaving boilerplate.
4. Before presenting the draft as final, run it through **Assess** (below) and fix anything that scores below "Good" on any dimension.

### 2. Assess / score an existing README

1. Read the target `README.md` in full.
2. Score it against [`references/scoring-rubric.md`](references/scoring-rubric.md): one score per dimension, with a one-line justification citing what is present or missing.
3. Present a table: dimension, score, justification. Sum the total and report the band (Excellent / Good / Needs Improvement / Poor).
4. Call out the single highest-impact fix first — usually the one that most affects a first-time visitor: is the project description clear, and can a stranger install and run something in under a minute?

### 3. Improve an existing README

1. Run **Assess** first so there's a baseline score to compare against.
2. For every dimension scoring below full marks, apply the matching fix guidance from [`references/mark-allen-checklist.md`](references/mark-allen-checklist.md). Make the edits directly in the file rather than only describing them.
3. Re-run **Assess** on the edited version and show the before/after score table so the user can see the delta.
4. Iterate until the README lands in the "Good" or "Excellent" band, or the user says it's fine as-is.

### 4. Check standard-readme compliance (opt-in, on request only)

1. Read [`references/standard-readme-spec.md`](references/standard-readme-spec.md) in full before assessing — it has exact section names, required order, and per-rule details that matter for an accurate pass/fail call.
2. Read the target `README.md` and check it against every rule in that file: required sections present, correct order, exact heading names (`Maintainer`/`Maintainers`, `Thanks`/`Credits`/`Acknowledgements`), Short Description under 120 characters, Table of Contents present if the file is 100+ lines, License last.
3. Report as pass/fail/partial per rule (not a 0–5 score), using the reporting table format in that file, then give an overall compliant/non-compliant verdict.
4. If the user wants fixes applied, make them structurally per the spec — don't reach for Mark Allen checklist fixes here (e.g. don't add a "Local Development Setup" heading; fold that content into `Install` or an `Extra Sections` entry instead, per the spec's own guidance).
5. If the user asks for both a quality score (mode 2) and standard-readme compliance, present them as two distinct, clearly labeled results. Don't average or combine them into one number.

## Guiding Principle

Mark Allen's closing question is the standard to hold every README to: *"Would I know what to do if I saw this for the first time?"* A README is a pitch, a tutorial, and an invitation — not just documentation. Optimize for a stranger with zero context getting from "what is this" to "it's running on my machine" as fast as possible.

## Sources

- Mark Allen, "How to Write a Great README for Your Public GitHub Project" (Everyday DevOps, 04 May 2025) — https://www.markcallen.com/how-to-write-a-great-readme-for-your-public-github-project/
- Richard Littauer, "Standard Readme" (MIT licensed spec) — https://github.com/RichardLitt/standard-readme
