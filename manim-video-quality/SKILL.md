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

## Scripts

Zero-dependency stdlib where possible; PEP 723 headers so `uv run` works too.

| Script | Does |
|---|---|
| `scripts/prep_corpus.py` | Cuts excerpts and normalizes every clip to an identical encode (720p30, no audio, opaque filenames + manifest). Prevents metadata leaking into judgments. Needs `ffmpeg`; `yt-dlp` only for remote refs. |
| `scripts/judge_ui.py` | Localhost pairwise judging UI. Randomized left/right, keyboard-driven, resumable, saves after every judgment. |
| `scripts/score_ranking.py` | Bradley-Terry ranking from the judgments, with honesty diagnostics: coverage, graph connectivity, intransitive triads, position bias. |
| `scripts/ablation_scene.py` | Dataset B generator — one scene, 8 injectable defects, one flag each. |
| `scripts/exp_metadata_leakage.py` | The metadata-leakage experiment. |
| `scripts/harvest_reference_pacing.py` | Measure narration pacing (wpm, speech density, beat length) from reference videos' subtitles. Downloads subtitles only — kilobytes, no video. |
| `scripts/variant_scene.py` | Narration-timed pacing x on-screen-text sweep, for finding the human optimum on choices that have no known-correct answer. |

```bash
# 1. build a blinded, normalized corpus
python3 scripts/prep_corpus.py --spec corpus_spec.json --out ./corpus

# 2. collect human ground truth  (~1 min/pair; 8 clips = 28 pairs)
python3 scripts/judge_ui.py --corpus ./corpus

# 3. rank + diagnose
python3 scripts/score_ranking.py ./corpus/judgments.json

# learn pacing from reference videos (subtitles only)
python3 scripts/harvest_reference_pacing.py --list refs.txt --out ./ref_pacing

# sweep pacing x text density (WPM 175|205|235, TEXT none|anchor|caption)
WPM=205 TEXT=anchor manim -qh --fps 60 scripts/variant_scene.py VariantScene

# ablations
ABLATION=none          manim -qh --fps 60 scripts/ablation_scene.py AblationScene
ABLATION=font_ttc_bug  manim -qh --fps 60 scripts/ablation_scene.py AblationScene
# flags: font_ttc_bug rushed_pacing card_itis color_spray
#        text_flood light_bg cut_not_morph overlap_nodes
```

**On sample size:** one judgment per pair is the minimum and is only
sufficient when items are clearly separated. Verified against synthetic data
with known ground truth: at ~3 comparisons per pair with close strengths the
fitted order is wrong; by ~40 it is exact. Practical approach — judge every
pair once, read the diagnostics, then add repeats only on the pairs that came
back close or intransitive.

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

## Narration is the timing source

Assume the video will be narrated unless told otherwise. That single fact
resolves the pacing argument, because a beat should last as long as its line
takes to say — which is measurable, not a matter of taste.

**Measured from 10 reference videos** (`scripts/harvest_reference_pacing.py`,
subtitles only, no video downloaded):

| quantity | measured | spread |
|---|---|---|
| speaking rate | **~205 wpm** | 188–222 |
| speech density | **~90% of runtime** | 87–93% |
| median spoken unit | **~3.5s** | p90 ≈ 4.5s |
| wall-clock rate | ~181 wpm | 179–183 |

**The trap this corrects.** The reference style *feels* unhurried, so the
intuitive move is "slow everything down and add silence." That is wrong about
the audio — it is near-continuous, fast narration with only ~10% silence.
What is slow is the *picture*: one object, held, while the voice works. Copy
the calm visuals but drop the narration and fixed 2–4s holds become dead air,
which viewers reliably report as "too slow" rather than "patient." A silent
render is an incomplete artifact; do not tune its pacing as if it were final.

### Recommended workflow (audio-first)

1. Write the narration script. It is the timing source, so it comes first.
2. Generate audio per line and **measure the actual duration** — do not trust
   a predicted wpm; observed TTS rate varied 134–148 wpm across identical
   default calls.
3. Time each animation beat to its measured audio length.
4. Mux. Keep un-narrated time near ~10% of runtime.

### TTS notes

Use **`gemini-3.1-flash-tts-preview`** via the **Cloud Text-to-Speech API**
(`google-cloud-texttospeech>=2.31.0`). Two reasons to prefer that surface over
the Vertex `generate_content` path: it takes `prompt` and `text` as separate
fields, so styling never leaks into what is spoken; and it returns real
encodings (LINEAR16/MP3) rather than headerless raw PCM you must wrap yourself.

Default delivery is far slower than the reference. Measured on one 20-word
line, voice Charon:

| | plain | "brisk" prompt | `[fast]` | `[extremely fast]` |
|---|---|---|---|---|
| **gemini-3.1-flash-tts-preview** | 159 | **204** | **204** | 233 |
| gemini-2.5-flash-tts | 148 | 194 | 143 | 119 |

Target is ~205 wpm. **3.1 honours inline pace markup; 2.5 does not** — on 2.5
the markup made delivery *slower*, so it is being mis-parsed. Prefer 3.1 with
either `[fast]` or a brisk style prompt.

### Audio-first pipeline

`scripts/narrate.py` synthesizes each line, measures what actually came back,
and writes `narration.json` (per-beat measured durations) plus a single
concatenated `narration.wav`. `variant_scene.py` reads that manifest via
`NARRATION=...` and times every beat to the measured audio.

```bash
python3 scripts/narrate.py --script script.json --out ./narration
NARRATION=./narration/narration.json TEXT=anchor \
  manim -qh --fps 60 scripts/variant_scene.py VariantScene
ffmpeg -i render.mp4 -i narration/narration.wav -c:v copy -c:a aac -shortest out.mp4
```

Do not predict durations from wpm and hope. Observed rate varied 171–216 wpm
across lines in a single run at one setting, so a predicted timeline drifts
audibly out of sync. Generate, measure, then animate to the measurement.

Verified end to end: generated narration came out at 197.8 wpm with 92% speech
density, against a reference of ~205 wpm and ~90% — i.e. this pipeline
reproduces the reference pacing profile.

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
