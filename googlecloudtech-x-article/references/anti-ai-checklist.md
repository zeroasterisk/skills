# Anti-AI Checklist (Alan Blount / @GoogleCloudTech Edition)

Run this checklist on every draft before presenting it to Alan. Fix all failures and re-run.

The standard: *"Reads like a seasoned Google Cloud systems engineer wrote it, delivers genuine architectural depth, avoids all AI writing tells, and makes a skeptical developer nod and think: 'Yeah, that is exactly how it breaks in production.'"*

---

## Pass 1: Deterministic Scan (Zero Tolerance)

Grep the draft mechanically. Any match is an immediate blocking failure.

- [ ] **Zero Em-Dashes or En-Dashes:** No em-dashes or en-dashes anywhere in prose, headers, or code comments. Use commas, colons, periods, or parentheses.
- [ ] **No Banned AI Filler Words:**
  - `delve`, `tapestry`, `crucial`, `pivotal`, `beacon`, `testament`, `foster`, `underscore`, `interplay`, `vibrant`, `groundbreaking`, `game-changer`, `seamless`, `seamlessly`, `supercharge`, `unleash`, `harness`, `revolutionize`, `elevate`, `dynamic`, `plethora`.
- [ ] **No Corporate Throat-Clearing Openers:**
  - `In today's fast-paced AI landscape`, `In this article/post we will`, `It is important to note`, `At its core`, `Fundamentally`, `Without further ado`.
- [ ] **No Staccato Triples:** No three consecutive short (< 8 words) sentences creating artificial drama.
- [ ] **No Verb Inflation for Simple Verbs:** No *serves as*, *stands as*, *features*, or *boasts* where *is*, *are*, or *has* belongs.
- [ ] **No "Not Only X, But Y" or Clipped Negation:** Cut *not only... but also* or clipped tails like *no guessing*.
- [ ] **No Forced Groups of Three:** Check lists and sentences; do not artificially group ideas in triads.
- [ ] **No Decorative Emojis:** No 🚀, 💡, ✅, 🔥 in titles, headings, or bullet items.
- [ ] **No Bold Mini-Headings on Every Bullet:** Avoid lists where every bullet begins with `**Label:**`.
- [ ] **Correct Byline:** Must be placed mid-intro, bolded: `By Alan Blount (@zeroasterisk)`.
- [ ] **Collective Voice (Not Diary):** Channel voice is collective `we` (the team) + `you` (the developer). No personal diary voice (`"I installed it on my Mac"`).
- [ ] **Sentence-Case Headings:** Use sentence case (`## Building resilient agent loops`), not title case.
- [ ] **Straight Quotes:** Standard ASCII quotes (`"` and `'`), not curly quotes.

---

## Pass 2: Judgment & Voice Calibration

Evaluate the draft against Alan's Pragmatic Builder perspective.

- [ ] **Cold Open Kills an Assumption:** The opening 1-2 sentences immediately challenge a common naive belief or highlight a real production tension.
- [ ] **Muted "Muppet" Warmth:** Does the draft contain subtle, earnest builder warmth? Are there 1-2 understated parenthetical asides `(...)` or self-deprecating touches that make it unmistakably human?
- [ ] **Is the Humor Sub-Surface?** The humor must stay strictly below the surface. The baseline tone is that of a serious, highly capable DevRel technical architect.
- [ ] **Proof-of-Depth Specifics Are Real:** Grounded in real protocol fields, exact error names, concrete token numbers, or firsthand dogfooding data.
- [ ] **"What with Why":** Every architecture decision explains why it matters to the developer.
- [ ] **Altitude Transitions:** Smooth movement between high-level developer objectives and low-level protocol reality.
- [ ] **Every Section Ends with "How to Steal It":** Hands the reader a concrete, sized pattern they can apply in their own stack.
- [ ] **Synthesis Beat Outranks the List:** The article elevates above a simple listicle to reveal a unifying architectural insight.
- [ ] **No Overclaiming:** Unconfirmed numbers are marked "illustrative". Nuances and compromises are stated plainly.
- [ ] **Actionable Closer:** Closes with a runnable verification command, a repo link, or a pragmatic builder kicker, never generic optimism.
