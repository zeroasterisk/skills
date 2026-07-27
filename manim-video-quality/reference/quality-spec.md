# Quality Spec — one source for creation rules and review probes

> Companion to the active style file (prose/intent) and
> `../reference/storytelling-vocabulary.md` (vocabulary). **This file is the testable
> version.** Every rule here has a check. If a rule cannot be checked, it is
> not in this file.

## The central insight

Most of what we have been asking a flaky LLM to judge is **deterministically
checkable from the Manim source or from extracted frames.** Font, fill
opacity, stroke width, background color, `run_time` values, `wait()`
durations, colors-per-frame, text overlap, negative-space ratio, and even
the phantom-word-gap bug (via OCR round-trip) are all exact computations.

Reserve the LLM for the small set of genuinely perceptual judgments. Use
deterministic checks for everything else — they are cheaper, exact, cannot
be talked out of a verdict by a context file, and have no variance.

**Check types**

| Type | Meaning | Trust |
|---|---|---|
| `SRC` | Static analysis of the scene `.py` | Exact |
| `FRAME` | Pixel/CV analysis of extracted frames | Exact-ish |
| `OCR` | Text extracted from frames, compared to expected strings | High |
| `LLM` | Gemini perceptual judgment | Low until validated |
| `HUMAN` | Alan | Ground truth |

**Severity**

- `BLOCK` — ship-stopper; objectively wrong
- `WARN` — probably wrong; needs a reason to override
- `INFO` — style drift signal; track over time

---

## A. Canvas & composition

| ID | Rule (creation) | Check (review) | Type | Sev |
|---|---|---|---|---|
| A1 | Background is `#0E0E10` (or true black) | `config.background_color` literal equals approved value | `SRC` | BLOCK |
| A2 | No opaque "card" shapes — **card-itis** | Every `fill_opacity` on a `RoundedRectangle`/`Rectangle` ≤ 0.20 | `SRC` | BLOCK |
| A3 | Thin strokes | Every `stroke_width` in 2–3 (titles/emphasis may reach 4) | `SRC` | WARN |
| A4 | No drop shadows / gradients | No shadow or gradient constructs present | `SRC` | BLOCK |
| A5 | Generous negative space | ≥ 60% of pixels equal background color, median across sampled frames | `FRAME` | WARN |
| A6 | One focal object per beat | ≤ 3 top-level mobject groups added per beat | `SRC` | WARN |
| A7 | No node/label overlap | No two text bounding boxes intersect in any sampled frame | `FRAME` | BLOCK |

## B. Color

| ID | Rule (creation) | Check (review) | Type | Sev |
|---|---|---|---|---|
| B1 | Palette is the approved set only | Every color literal ∈ the active style file palette | `SRC` | BLOCK |
| B2 | ≤ 3 accent colors visible at once | Distinct non-background, non-greyscale hues per frame ≤ 3 | `FRAME` | WARN |
| B3 | **Reserved colors**: Google Green only = confirmed/success; Google Red only = blocked/denied; Google Blue only = the product itself | Each reserved hex appears only in beats tagged with its licensed meaning (tag in scene source via comment/marker) | `SRC` | BLOCK |
| B4 | One concept = one color, consistently | A given semantic label keeps the same hex across all its appearances | `SRC` | WARN |

## C. Typography & text

| ID | Rule (creation) | Check (review) | Type | Sev |
|---|---|---|---|---|
| C1 | Font is Roboto (never a macOS `.ttc`: Helvetica Neue, Arial, Times) | Every `Text(font=…)` equals approved font | `SRC` | BLOCK |
| C2 | **No phantom word gaps** | OCR each rendered label; normalized OCR text == source string (whitespace-sensitive) | `OCR` | BLOCK |
| C3 | ≤ 1 text element introduced per beat | Count `Text` mobjects added per `self.play` | `SRC` | WARN |
| C4 | Text appears *after* its visual resolves, never simultaneously | No `play()` containing both a `Text` creation and a non-text creation | `SRC` | WARN |
| C5 | Any text on screen ≥ 1.5s | Per-text on-screen duration from source timeline | `SRC` | BLOCK |
| C6 | Short phrases only | Any single `Text` string ≤ 12 words | `SRC` | WARN |
| C7 | Contrast sufficient | Text luminance vs local background ≥ WCAG AA (4.5:1) | `FRAME` | BLOCK |

## D. Motion & pacing

> This is the block the LLM grader is *least* able to see (1 FPS sampling).
> It is also almost entirely computable from source. Do not ask the LLM.

| ID | Rule (creation) | Check (review) | Type | Sev |
|---|---|---|---|---|
| D1 | Readable beats ≥ 1.5s | Every `run_time` on an animation involving `Text` ≥ 1.5 | `SRC` | BLOCK |
| D2 | No sub-second micro-transitions | No `run_time` < 0.5 anywhere | `SRC` | WARN |
| D3 | Stillness after each key beat | A `self.wait(≥2.0)` follows each tagged key beat | `SRC` | WARN |
| D4 | Prefer morph over cut | Ratio of `Transform`/`ReplacementTransform` to `FadeOut`+`FadeIn` pairs ≥ 1.0 | `SRC` | WARN |
| D5 | Smooth easing only | `rate_func` ∈ {smooth, linear, ease_in/out}; no bounce/elastic/wiggle | `SRC` | WARN |
| D6 | One thing moves at a time | ≤ 2 concurrent animations in any `self.play` (excluding `LaggedStart`) | `SRC` | WARN |
| D7 | Generous stagger | `LaggedStart` `lag_ratio` ≥ 0.25 | `SRC` | INFO |
| D8 | Total duration is honest | Rendered duration matches sum of source timeline (catches silent drops) | `SRC`+`FRAME` | INFO |

## E. Narrative *(the genuinely perceptual layer)*

These cannot be computed. This is where — and **only** where — the LLM and
human belong.

| ID | Rule (creation) | Check (review) | Type | Sev |
|---|---|---|---|---|
| E1 | Exactly one aha moment per video, nameable in one sentence | Ask grader to state the single main point; compare to pre-registered intent | `LLM` | WARN |
| E2 | The visual carries the idea; text is caption not message | Ask grader to describe the idea from *muted, text-masked* frames | `LLM` | WARN |
| E3 | Tension precedes release | Ask grader to identify where the problem is posed and where resolved | `LLM` | INFO |
| E4 | Payoff reuses the setup object (persistence contract) | Ask grader: "is the clean diagram the same objects transformed, or new ones?" | `LLM` | WARN |
| E5 | Pacing reads as patient, not merely slow | Forced-choice vs reference clip | `LLM`+`HUMAN` | INFO |
| E6 | It is actually compelling | — | `HUMAN` | BLOCK |

---

## How this maps to the old rubric

The current 6 LLM dimensions map onto this spec as follows — note how much
of what we were asking the LLM was never an LLM question:

| Old LLM dimension | Should actually be |
|---|---|
| `visual_clarity` | A5, A6, A7 (`FRAME`) + E2 (`LLM`) |
| `timing_pacing` | D1–D3, D6 (`SRC`) — **not** LLM; it can't see sub-second beats |
| `color_discipline` | B1–B4 (`SRC`/`FRAME`) — fully deterministic |
| `text_readability` | C1, C2, C5, C7 (`SRC`/`OCR`/`FRAME`) — fully deterministic; this is the dimension that scored 9/10 on a render with four mis-rendered words |
| `transition_quality` | D4, D5 (`SRC`) |
| `professional_polish` | A2–A4, A7, C2 (`SRC`/`FRAME`) — and it is the dimension most contaminated by metadata leakage |

**Roughly 80% of the current rubric is deterministically checkable and should
never have been an LLM judgment call.**

---

## Pre-registration requirement

Before rendering anything for review, write a frozen intent file containing:

1. The one-sentence aha (tests E1)
2. Per-beat: what idea it carries, and which reserved colors are licensed in
   that beat (tests B3)
3. Expected on-screen text strings verbatim (tests C2 via OCR)
4. Expected total duration (tests D8)

This file is written **before** the render and is not edited afterward. It is
the pre-registration. Any edit to it after seeing a score is a protocol
violation and must be logged as such.
