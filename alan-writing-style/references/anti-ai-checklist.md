# Anti-AI & Humanize Checklist (Alan Blount Standard)

Run this checklist on any draft before presenting it to Alan or publishing. A failure in Pass 1 is an immediate blocking defect.

---

## Pass 1: Deterministic Scan (Automated / Zero-Tolerance)

Scan the text mechanically. Any match requires an immediate rewrite.

- [ ] **Zero Em-Dashes or En-Dashes:** No em-dashes or en-dashes anywhere in prose, titles, or code comments. Use commas, colons, periods, or conversational parentheses.
- [ ] **No Banned AI Filler:**
  - High-frequency AI words: `delve`, `tapestry`, `crucial`, `pivotal`, `beacon`, `testament`, `foster`, `underscore`, `interplay`, `vibrant`, `groundbreaking`, `game-changer`, `seamless`, `seamlessly`, `supercharge`, `unleash`, `harness`, `revolutionize`, `elevate`, `dynamic`, `plethora`.
  - Corporate/throat-clearing openers: `In today's fast-paced landscape`, `In this article/post we will`, `It's important to remember/note`, `At its core`, `Fundamentally`, `Without further ado`.
- [ ] **No Staccato Triples:** No three consecutive ultra-short sentences (< 8 words) creating forced dramatic punchlines (e.g., *"Then everything changed. The model failed. A new era began."*).
- [ ] **No Verb Substitution for Simple Verbs:** No replacing *is*, *are*, or *has* with *serves as*, *stands as*, *features*, or *boasts*.
- [ ] **No "Not Only X, But Y" or Clipped Negative Endings:** Remove formulaic negations like *"It's not just a tool, it's a platform"* or *"no guessing"*.
- [ ] **No Forced Groups of Three:** Check lists and sentences; do not force items into neat triads.
- [ ] **No Decorative Emojis:** No 🚀, 💡, ✅, 🔥 in titles, headings, or bullet points.
- [ ] **No Bold Mini-Headings on Every Bullet:** Avoid vertical lists where every single bullet point starts with `**Topic Name:**`. Write fluent paragraphs or natural lists.
- [ ] **Sentence-Case Headings:** Use sentence case (`## Building resilient agent loops`), not title case (`## Building Resilient Agent Loops`).
- [ ] **Straight Quotes:** Use standard ASCII quotes (`"` and `'`), not curly quotes (`“`, `”`, `‘`, `’`).

---

## Pass 2: Judgment & Voice Calibration (Alan's Standard)

Evaluate the text through Alan's specific perspective as a 20-year engineer turned PM.

- [ ] **Sub-Surface "Muppet" Warmth:** Does the piece have earnest, nerdy warmth rather than sterile corporate distance? Is there a subtle winking parenthetical `(...)`, an observational smile, or a self-deprecating aside?
- [ ] **Is the Humor Muted?** Ensure the humor stays strictly below the surface. If it sounds like a standup routine, wacky marketing, or forced slang, dial it back. The baseline must remain an authoritative DevRel / technical architect voice.
- [ ] **"What with Why":** Does every technical description clearly articulate *why* it matters to the developer?
- [ ] **Altitudes Check:** Does the piece bridge the gap between high-level architectural intent (Altitude 3/2) and low-level protocol reality (Altitude 1/0: network timeouts, schema changes, event logs)?
- [ ] **No Demoware or Unearned Hype:** Are all performance claims, latency numbers, and architecture trade-offs honest? Are edge cases and messy failure modes acknowledged?
- [ ] **Concrete Proof of Depth:** Are named errors, actual protocol fields, and real system constraints cited?
- [ ] **Reader-Generous Takeaway ("How to Steal It"):** Does the piece give away the pattern so an engineer can implement it in their own stack without vendor lock-in?
- [ ] **Natural Burstiness:** Does sentence length vary visibly? Do short statements contrast with nuanced technical explanations?
- [ ] **No Generic Optimistic Wrap-Ups:** Cut vague inspirational sign-offs (*"The future of AI is bright!"*). End on a concrete technical move, a verification step, or a pragmatic builder kicker.
