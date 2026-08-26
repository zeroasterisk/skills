# Methodology — running Gemini video analysis so the result is valid

> Read before writing any code that asks a model to judge a video.
> Every rule here exists because we violated it and got a wrong answer.

---

## 1. Know what the model can actually see

**Gemini samples video at 1 frame per second by default.** The official docs
state: *"The File API service extracts image frames from videos at 1 frame
per second… the details of fast action sequences may be lost at the 1 FPS
frame sampling rate."* Independently confirmed by frame-extraction testing
([s-anand.net](https://www.s-anand.net/blog/how-does-gemini-process-videos/)).

Consequences, all of which we got wrong:

| You want to judge | At 1 FPS the model… | Do this instead |
|---|---|---|
| Playback frame rate (15 vs 60fps) | **cannot see it at all** | `ffprobe`, deterministic |
| Easing / motion curve quality | cannot see it | `SRC` check on `rate_func` |
| Sub-second beats (`run_time` 0.2–0.5) | never receives those frames | `SRC` check on `run_time` |
| Transition smoothness | sees before/after, not the transition | `SRC` check on animation type |
| Whether text was on screen long enough | may miss short text entirely | `SRC` timeline computation |
| Layout, composition, color, legibility | **sees these fine** | LLM is appropriate |
| Narrative arc across a whole video | sees these fine | LLM is appropriate |

**Raise the sampling rate when motion actually matters.** `video_metadata`
accepts an `fps` argument (0.1–60). Cost scales linearly with it: 10s at
30fps costs the same visual tokens as 5min at 1fps. Use targeted
high-fps analysis on a short clip, not the whole video.

```python
types.Part(
    file_data=types.FileData(file_uri=uri, mime_type="video/mp4"),
    video_metadata=types.VideoMetadata(fps=10),   # for a short motion probe
)
```

## 2. Never leak quality metadata into the prompt

**Measured effect: 1.90 points on a byte-identical video** (see
the SKILL.md summary table and `scripts/exp_metadata_leakage.py`).

Rules:

- Strip FPS, resolution, bitrate, file size, and filename from the prompt.
- If you must include duration (for pacing context), include it for *all*
  compared items, identically.
- When comparing two videos, **render them with identical encode settings**
  so no perceptible or stated difference exists other than the variable
  under test.
- Never include the file path — `.../480p15/...` leaks quality in the name.

## 3. The context file is a pre-registration, not a lever

- Write it **before** the render. Freeze it.
- It may state *intent* ("this scene is meant to feel overwhelming").
- It may **not** state *scores* ("do not penalize this", "score this highly",
  "this is intentional so it's fine").
- If you find yourself editing the context after seeing a low score, stop.
  That is p-hacking. Log it as a protocol violation.

**Banned phrases:** "do not penalize", "this is intentional, so", "should
score well", "evaluate favorably", "this is not a defect".

## 4. Prefer forced choice to absolute scoring

Absolute 1–10 scores are noisy, drift with prompt phrasing, and have no
anchor. Pairwise comparison is markedly more reliable and is the natural
form for ablation pairs.

```
Here are two videos, A and B. They differ in exactly one respect.
Which better exhibits <specific property>? Answer A or B, then explain
in one sentence what you observed that decided it.
```

**Counterbalance order.** Run every pair twice, A/B and B/A. If the answer
flips, record it as *undecided* — do not average. Position-bias flip rate is
itself a metric worth tracking (bar: ≤10%).

## 5. Blind the grader

- Strip filenames and paths.
- Do not reveal which video is "ours" and which is the reference.
- Do not reveal which is baseline and which is ablated.
- Do not reveal the hypothesis.

## 6. Separate verifiable detection from opinion

Two different prompts, two different trust levels:

**Detection** (objective, has a right answer):
> "Transcribe every text label visible in this video, exactly as rendered,
> preserving spacing."
Then diff against expected strings. This catches the phantom-gap bug the
holistic rubric scored 9/10.

**Opinion** (perceptual, no right answer):
> "Which of these two feels more patient?"

Never mix them in one call — the opinion contaminates the detection.

## 7. Report variance, always

- `temperature=0` (current tool uses 0.1).
- Minimum **n=3** runs per condition; n=5 for anything load-bearing.
- Report mean **and** SD. A single number with no SD is not a measurement.
- Measured baseline for reference: SD ≈ 0.16–0.29 at temp 0.1 on a 35s clip.
  So a difference under ~0.5 points is noise.

## 8. Validate before trusting

A grader is admissible only after demonstrating, on this content domain:

| Metric | Bar |
|---|---|
| Pairwise accuracy on known ablations | ≥ 85% |
| Spearman ρ vs human ranking | ≥ 0.7 |
| Test-retest SD (n=5) | ≤ 0.5 |
| Metadata sensitivity | ≤ 0.3 |
| Order-flip rate | ≤ 10% |
| Real 3b1b reference lands in top band | yes |

Until then: **advisory only.** No gate, no "APPROVED".

## 9. Per-defect blindness is expected — map it

Do not expect the grader to catch everything. Expect it to be blind to
whole categories (anything sub-second; anything requiring pixel precision).
The deliverable of Phase 3 is a **blindness map**: which defects it reliably
catches (use LLM), which it misses (use a deterministic check instead).

A grader that catches 4 of 8 defect types but is *honest and consistent
about which 4* is far more useful than one that claims to catch all 8.

## 10. Checklist before reporting any score

- [ ] Metadata stripped or held constant
- [ ] Context file pre-registered, no banned phrases
- [ ] Filenames/paths blinded
- [ ] n ≥ 3, SD reported
- [ ] Pairwise counterbalanced if comparative
- [ ] Detection separated from opinion
- [ ] Deterministic checks run first — LLM only for what it can actually see
- [ ] Stated as advisory unless validation bars are met
