# Dataset A — Reference corpus with human ground truth

Purpose: **calibration anchors.** Establish what the top and bottom of the
scale actually look like, and provide human-labeled items to validate the
grader's ranking against.

We have never scored a real 3Blue1Brown video. Until we do, we do not know
whether our rubric would even pass the thing we are trying to imitate — and
a rubric that fails its own exemplar is measuring the wrong thing.

---

## A1. Positive anchors — real 3Blue1Brown

Licensing: fetch for **local, internal evaluation only.** Do not
redistribute, do not commit the media files, do not upload to shared
buckets. Keep under `eval/corpus/3b1b/` (gitignored).

Use **60–90 second excerpts**, not full videos — cheaper, and matches the
length of what we produce. Prefer excerpts that are pure visual explanation
(skip intros/sponsor reads).

| id | source | why chosen | excerpt |
|---|---|---|---|
| `3b1b-linalg-vectors` | Essence of Linear Algebra, Ch.1 "Vectors" | canonical morph-driven geometry; minimal text | 02:00–03:30 |
| `ref-clip-2` | "But what *is* a neural network?" Ch.1 | node/edge network diagrams — closest structural analogue to our agent-topology scenes | 03:00–04:30 |
| `3b1b-fourier` | "But what is a Fourier series?" | dense simultaneous motion done well; tests our "one thing at a time" assumption | 01:30–03:00 |
| `3b1b-eulers-formula` | "Euler's formula with introductory group theory" | abstract concept made concrete via a single sustained visual metaphor | 04:00–05:30 |

Fetch (requires `yt-dlp`; run manually, not committed):

```bash
mkdir -p eval/corpus/3b1b && cd eval/corpus/3b1b
# resolve URLs from https://www.3blue1brown.com/ ; then per clip:
yt-dlp -f "bestvideo[height<=1080]+bestaudio" --merge-output-format mp4 \
       --download-sections "*02:00-03:30" -o "3b1b-linalg-vectors.mp4" "<URL>"
```

**Normalize before use** so encode settings can't leak (see METHODOLOGY §2):

```bash
ffmpeg -i in.mp4 -vf "scale=1920:1080,fps=60" -c:v libx264 -crf 20 -an out.mp4
```

Audio: strip it (`-an`). Our videos have none; leaving narration in gives
3b1b an unfair channel and confounds the comparison.

## A2. Negative & mid anchors — your own renders

**Your existing accept/reject history is free ground truth.** Every render a
human already rejected, revised, or shipped is a labeled datapoint. Harvest
these before generating anything new.

The consuming project owns this table — keep it in the project repo, not in
this skill. Schema:

| field | meaning |
|---|---|
| `id` | stable short id, e.g. `ours-v2` |
| `path` | path to the render, relative to the project repo |
| `human_verdict` | verbatim human reaction — do not paraphrase into a score |
| `band` | coarse bucket: `LOW` / `MID` / `HIGH` |

Include *rejected* work. A corpus of only good renders cannot show that a
grader discriminates.

> **Archive render + source together, per version.** A version whose source
> was overwritten cannot be re-rendered or re-measured, and if it was the one
> with detailed human feedback, that is the most expensive item to lose.

### Known ordering constraints (partial ground truth)

Write down the orderings the human's own statements already imply, e.g.:

```
reference-*   >  our-first-attempt-at-reference-style
our-latest    >  our-earlier-rejected-versions
our-shipped   >  our-rejected
```

Any valid grader must reproduce these. **Check this first** — it is nearly
free and it is where graders most often fail. A grader whose top score goes
to a render the human immediately sent back for rework is anti-correlated
exactly where it matters.

The grader must reproduce these. **It currently does not:** v4 scored 9.0/10
— higher than anything else measured — despite the human immediately listing
kerning, animation, and timing defects. A grader whose top score goes to a
video the human then sends back is anti-correlated where it matters most.

## A3. Human ranking task *(the one irreplaceable input)*

Ask the human reviewer for **forced-choice pairwise judgments**, not scores. Humans are
unreliable at absolute scoring and reliable at comparison.

Protocol:
- 8 clips → present ~15 pairs (not all 28; use a sorting-efficient subset).
- Randomize order and left/right position.
- One question only: *"Which is closer to the target: a patient, idea-first
  technical explainer in the 3Blue1Brown tradition?"*
- Allow "too close to call."
- ~20 minutes total.

Derive a Bradley-Terry / Elo ranking from the pairs. That ranking is ground
truth for Phase 3's Spearman ρ.

**Store results in** `datasets/A_human_ranking.json` (create when collected):

```json
{
  "collected": "YYYY-MM-DD",
  "judge": "<reviewer-id>",
  "pairs": [
    {"a": "ours-v4", "b": "3b1b-nn-what-is", "winner": "3b1b-nn-what-is",
     "note": "optional free text"}
  ]
}
```

## A4. What we learn from this dataset

1. **Where does real 3b1b score on our rubric?** If it fails the 6.5 gate,
   the rubric is invalid — full stop. This is the single most informative
   number we can collect and it costs one API call.
2. **Does the grader reproduce the known ordering?** (Spearman ρ ≥ 0.7)
3. **Does it put v4 above or below a12/pilot?** Currently it ranks v4 top,
   which contradicts the human.
4. **What is the actual score range?** If everything lands 7–9, the
   instrument has no resolution and the thresholds are meaningless.
