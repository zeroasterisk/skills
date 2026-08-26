---
name: technical-post-editorial
description: Edit and review technical blog posts, specs, and engineering write-ups to ensure clean house-style conformity and pitch-appropriate readability. Use as a post-hoc acceptance gate or review tool.
license: Apache-2.0
metadata:
  version: "1.1.0"
  trigger: Reviewing, auditing, or editing a technical post draft
---

# Technical Post Editorial

Review and refine technical prose to adhere to crisp, authentic engineering editorial standards.

> **Design Role:** Use this skill as a **post-hoc acceptance gate** during review, editing, or CI/CD verification rather than an in-loop generative dial during drafting. Write or edit first for technical substance, then audit and lint with the two-axis scorecard.

## The Core Tension (from Ruth Starkman)

The problem with model prose isn't the devices themselves — em dashes can be precise, contrast can clarify, a rule of three can organize. The problem is using them before you've specified the actor, the relation, the limit, or the claim. A model produces the *rhetoric* of argument before the argument exists.

Two failure modes:
1. **Lazy use**: device before substance (the diagnosis)
2. **Overcorrection**: removing every marked choice because a model might have used it (let the model set the terms anyway)

The test for any device: does this clarify a specific claim, or does it signal that a claim is about to appear?

---

## Automated Acceptance Gating (docstats MCP)

When the `readability-docstats` MCP server is available, invoke `analyze_document` to inspect the text along both axes:

```json
// MCP Tool: analyze_document
{
  "text": "<draft content>"
}
```

### The Two-Axis Scorecard

Format the output into a clear, unified two-axis scorecard:

```
DOCUMENT: migration-guide.md   (target audience: Developer Blog)

Axis A  Readability (Audience Fit)
  text_standard: grade 11     band: Dense (Target: Accessible-Dense)     [PASS]
  flesch_reading_ease: 42.3   flesch_kincaid_grade: 11.2   word_count: 1840

Axis B  House-Style Conformity
  ai_tell_score: 6.4 / 10     floor: >= 7.0                              [WARN]
  em dashes: 3    throat-clearing: 2    binary contrasts: 4    adverb rate: 3.1/100w
  rhythm indicator (advisory): sentence-length CV 0.18

VERDICT: REVISE FOR VOICE
  Axis A acceptable. Axis B below floor (6.4 < 7.0): remove 3 em dashes,
  cut 2 throat-clearing openers, rewrite 4 binary-contrast frames.
```

### Combined Verdict Matrix & Provenance Guidance

| Axis A (Audience Fit) | Axis B (Style Score) | Verdict | Provenance-Aware Action |
|---|---|---|---|
| **Pass** | **Pass (≥ 7.0)** | **Ship** | Ready to publish. Prose is well-calibrated and authentic. |
| **Pass** | **Warn / Fail (< 7.0)** | **Revise for Voice** | **Raw AI Draft:** Aggressively restructure to remove synthetic tropes.<br>**Human Text:** Apply light-touch linting on specific flags; preserve authorial voice. |
| **Warn / Fail** | **Pass (≥ 7.0)** | **Revise for Complexity** | Adjust sentence length / vocabulary for target audience without altering voice. |
| **Fail** | **Fail (< 7.0)** | **Full Rewrite** | **Raw AI Draft:** Overhaul complexity and style.<br>**Human Text:** Refactor dense sections for clarity; address style lints. |

---

## Rules & House-Style Linting

### 1. No em dashes in prose
Em dashes in prose frequently signal synthetic drama.
- No `—` in prose sentences. Use a comma, a colon, a period, or a parenthetical.
- Exception: code blocks, tables, and markdown list item separators.

### 2. Active voice, named actors
Every sentence needs a human or a named system doing something. Passive voice and false agency hide the actor.

| Avoid | Fix |
|---|---|
| "The migration is loud about what broke" | "We've covered what broke" |
| "The config was changed" | "We changed the config" |
| "The data tells us" | "The numbers show" |

### 3. No non-technical filler adverbs
Kill all non-technical -ly words. No softeners, intensifiers, or hedges.
- Specific offenders: "notably," "genuinely," "silently," "actually," "simply," "truly," "deeply," "fundamentally."
- Exception: technical adverbs that carry mathematical/system precision: "atomically," "synchronously," "recursively," "concurrently," "deterministically."

### 4. No throat-clearing openers
Cut the announcement before the point.
- "Here's the thing:" → cut, state the thing
- "Here's what we found:" → cut, state what you found
- "It's worth noting that" → cut, state the note
- "It turns out" → cut
- "The payoff:" as a standalone label → merge into the sentence

### 5. No binary contrasts as the frame
"Not X, it's Y" and "X isn't the problem, Y is" manufacture synthetic drama. State Y.
- "Not `click_at`. Just `click`." → "The model emits `click` now, not `click_at`."
- "`Environment` isn't documentation, it's behavior." → "`Environment` changes model behavior."
- "Migrating isn't only about not breaking." → "Migration adds capabilities too."

### 6. No staccato fragmentation
Sentence fragments for emphasis read as manufactured profundity. "That's it. That's the thing." — write complete sentences.

### 7. No Wh- sentence starters
Sentences starting with What, When, Where, Which, Who, Why, How tend to become rhetorical.
- "What cost us the extra day was..." → "The extra day came from..."
- "What makes this hard is..." → "The constraint is..."

### 8. Vary rhythm (Advisory)
Vary sentence lengths naturally across paragraphs.
- Two items beat three; avoid metronomic lists of three.
- *Note:* Sentence length CV (~0.20–0.40) is an advisory indicator. **Do not** optimize numeric CV targets directly in generation prompts.

### 9. No vague declaratives
A sentence that announces significance without naming the specific thing is empty.
- "This is the single decision that made the migration painless" → show the decision, skip the annotation
- "The implications are significant" → name the implication

### 10. Trust the reader
Skip hand-holding, softening, meta-commentary, and permission-granting. State the facts and let readers conclude.

---

## Technical Writing-Specific Exceptions

The following are acceptable in technical posts:
- Em dashes as separators inside bulleted lists (markdown convention)
- Three-item lists when the items are genuinely enumerable and distinct (not rhetorical)
- Passive voice in code comments where the actor is genuinely unspecified
- Technical adverbs on the allowlist ("atomically", "synchronously", "recursively", etc.)

---

## Qualitative Rubric (Human Review Dimensions)

Rate 1–10 on each:

| Dimension | Question | Scored By |
|---|---|---|
| Directness | Statements, not announcements? | docstats Axis B + Human |
| Rhythm | Varied, not metronomic? | docstats Axis B (advisory) + Human |
| Density | Anything cuttable? | docstats Axis B + Human |
| Authenticity | Sounds like a person who did the thing? | Human only |
| Trust | Respects reader intelligence? | Human primary |

Below 35/50: revise.

---

## Common Patterns in Technical Posts

| Pattern | Fix |
|---|---|
| "Worth noting:" | Cut. State the note. |
| "Worth confirming rather than assuming" | "Confirm, don't assume." |
| "Cheap insurance against..." | State what it prevents, specifically. |
| "The obvious fix is X. We did something better." | State the approach directly. |
| Italicizing a word for emphasis ("it mattered *more*") | Remove. Rewrite if emphasis is needed. |
| "The lesson that cost us the most time" | Fine as a heading, but the paragraph should open with the lesson, not with the meta-commentary about it costing time. |

---

## Sources

- stop-slop skill (hardikpandya/stop-slop) — pattern rules
- Ruth Starkman, "Model Style Is So Cringe" (Substack, March 2026) — nuance on device vs lazy use
- docstats (ghchinoy/docstats) — two-axis acceptance gating and deterministic house-style linting

