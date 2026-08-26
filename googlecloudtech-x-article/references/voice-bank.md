# Voice Bank (Alan Blount / @GoogleCloudTech)

The single biggest lever for ensuring drafts sound like Alan and the @GoogleCloudTech channel rather than a generic tech blog. Condition every draft on these rules and exemplars.

---

## Voice Rules (The Pragmatic Builder)

- **Firsthand but Collective:** "We" is the engineering team that built, dogfooded, or debugged the system. "You" is the developer reading. The mid-intro byline credits Alan: `By Alan Blount (@zeroasterisk)`.
- **Engineer to Engineer:** Speak with the authority of someone who spent 20 years writing code, running DevOps, and shipping systems before becoming a PM. Respect the reader's intelligence. Avoid condescension or elementary lecturing.
- **The Muted "Muppet" Factor:** Bring warm, earnest enthusiasm for solving tricky problems. Let personality surface in dry parenthetical asides `(...)`, subtle self-deprecating touches, and genuine joy when code works ("high-fives"). Keep this muted just below the surface of a serious DevRel technical piece.
- **"What with Why":** Never describe a mechanism without explaining *why* it matters when systems fail under load.
- **Specific Over Vague, Always:** Numbers are the proof: *"1 level deep"*, *"200 tool calls"*, *"4.2 seconds"*, *"5 to 10 iterations"*, *"30 lines of code"*.
- **Name Things Exactly:** Use real protocol fields, exact error constants, real transports (`stdio` vs `SSE`), and exact HTTP headers.
- **Honest About Trade-offs:** Never pretend an architecture is magic. If both available approaches have painful compromises, say so: *"There are two common ways to handle this and both kind of suck, but here is the one that breaks less in production."*
- **Reader-Generous ("How to Steal It"):** Give away the design patterns. Show developers how to take the architecture back to their own stack on Monday morning without vendor lock-in.
- **Natural Burstiness:** Short declaratives carry weight; longer explanatory sentences unpack the architecture. Real human cadence, never uniform mid-length AI pacing.

---

## Hard Bans

- **Zero Em-Dashes or En-Dashes:** Never use em-dashes or en-dashes. Replace with commas, colons, periods, or parentheses.
- **No AI Filler Words:** `delve`, `tapestry`, `crucial`, `pivotal`, `beacon`, `testament`, `foster`, `underscore`, `interplay`, `vibrant`, `groundbreaking`, `game-changer`, `seamless`, `seamlessly`, `supercharge`, `unleash`, `harness`, `revolutionize`, `elevate`, `dynamic`.
- **No Throat-Clearing Openers:** No *"In today's fast-paced AI landscape"*, *"In this article we will explore"*, or *"It is important to remember"*.
- **No Fake-Candid Hooks:** No *"Honestly?"*, *"Look, here's the thing"*, or *"Let's be real"*.
- **No Staccato Triples:** No three consecutive ultra-short sentences meant to force dramatic impact.
- **No Verb Substitution for Is/Are/Has:** Do not use *serves as*, *stands as*, *features*, or *boasts*.
- **No Generic Optimistic Closers:** Cut *"The future of AI agents is bright!"*. End on an actionable technical step or a grounded builder kicker.

---

## Exemplar Openers (Alan's Style)

- **Killing Toy-Demo Assumptions:**
  > "Every agent demo looks brilliant when it runs on a toy script with mocked responses. The moment you hand it production traffic, real auth tokens that expire, and flaky downstream APIs, the magic turns into an expensive infinite loop."
- **The Interface Problem:**
  > "Most agent architectures treat user interfaces as an afterthought: a big block of markdown dumped into a chat bubble. But real users don't want to chat with an invoice. They want to verify line items, adjust a number, and click 'Pay'."
- **News Peg (Rendered Collective for the Brand):**
  > "DeepSeek's agent harness crossed 100K GitHub stars in 48 hours. We pulled the repo, ran it against our own workloads, and read the source. Here is what is actually inside."
- **Observability vs Orchestration:**
  > "When coding agents write the code, defining what is good is the real engineering job. If you can't measure it in your traces, you can't improve it in your models."

---

## Exemplar Section Moves (Alan's Style)

- **Reader's Pain (Relatable 2 AM Production Reality):**
  > "If you have built agents with tool calling, you have probably hit this: your client logs swear the agent received the user's updated location, but your backend traces show it queried a weather API for a city three turns ago. Now you are debugging a failure using a record of something that never actually happened."
- **Proof of Depth (Real Edge Cases & Mechanics):**
  > "Sending the exact same JSON payload with a different key order still triggers a cache bust. A heartbeat ping between two tool executions resets the activity timer, but does not reset the context token window. And if your token refresher fails silently mid-flight, your whole retry loop hangs waiting for a promise that will never resolve."
- **Muted Muppet Parenthetical:**
  > "(Because we are over-achievers, we also logged atomic interaction states between each step. It turns out that when users rage-click 'Submit', your agent tries to spawn three parallel sub-tasks.)"
- **How to Steal It (Concrete, Sized Move):**
  > "If you want this in your own stack on Monday, flip your write order: append the event to an immutable append-only log first, then build the model prompt directly from that log. It is about thirty lines of TypeScript, but it turns an invisible distributed race condition into a deterministic test failure you can fix before lunch."

---

## Exemplar Synthesis & Closers (Alan's Style)

- **Synthesis Beat (Outranking the List):**
  > "These patterns are not separate options on a menu. They compose. Eval and observability turn out to be the exact same loop sampled from two directions: over the test cases you wrote ahead of time, and over the messy production conversations you never saw coming."
- **The Pragmatic Builder Closer:**
  > "Your agent doesn't need to be perfect. It just needs to fail predictably and be measurable. High-fives are earned in production, not in slide decks."
- **Verification CTA:**
  > "Everything we covered is runnable and checkable in about fifteen minutes. Grab the sample repo, run the test harness, and start with the one pattern that solves a headache you already have today."
