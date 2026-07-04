---
name: engineering-discipline
description: Full engineering lifecycle — define what done means, debug systematically, verify through real surfaces before claiming completion.
---

# Engineering Discipline

The full engineering lifecycle in one process: define → build → debug → verify. Follow this for every non-trivial task.

> Distilled from [obra/superpowers](https://github.com/obra/superpowers) (Apache 2.0) and [Intelligent-Internet/zenith](https://github.com/Intelligent-Internet/zenith) (Apache 2.0).

---

## 1. Before You Build — Define What Done Means

Write a **VAL-* assertion** for each capability before writing code. If you can't specify what evidence proves it works, you don't know what "done" means.

```
VAL-001: <capability name>
  Surface:  <where to test it — API, browser, CLI>
  Needs:    <prerequisites — running server, test data, auth token>
  Behavior: <what should happen — specific, observable, falsifiable>
  Evidence: <what constitutes proof — request/response, screenshot, test output>
```

A good assertion is **falsifiable** (it can fail), **observable** (no source code reading), and **specific** (names the surface, inputs, and expected output). One assertion per user-observable capability. A typical feature needs 3–7. Every capability needs at least one failure-path assertion.

**Proportionality**: For trivial changes (typo fixes, version bumps), a single VAL assertion and a quick smoke test suffice. Scale assertions to risk.

## 2. When It Breaks — Debug Systematically

Never guess at fixes. Find the root cause first.

### Phase 0: Reproduce
Read the complete error message and stack trace. Create a minimal, reliable reproduction — one command if possible. If you cannot reproduce, you cannot verify any fix. Stop and get repro info first.

### Phase 1: Trace Boundaries
Log what data enters and exits each component boundary:
```
Client → Gateway → Service → Data layer
         ↑ input    ↑ transformed   ↑ stored
```
The first point where data diverges from expectation is where the bug lives.

### Phase 2: Compare
What's different between a working case and the broken case? Check: input, environment, and what changed since it last worked (git log, deploy history, config).

### Phase 3: Hypothesize with Prediction
Form ONE hypothesis. **Before testing**, write down what you predict you'll observe if correct, and what you'd observe if wrong. THEN run the test. If you didn't predict the outcome before observing it, you're rationalizing, not testing.

If the prediction was wrong: form a NEW hypothesis. Do NOT layer fixes on top of a wrong diagnosis. Change ONE variable at a time.

### Phase 4: Fix the Root Cause
Fix the cause, not the symptom. Then verify through the real surface (see section 3).

### Escalation Rules
- **3+ failed fix attempts** → question the architecture, not the code
- **Works locally but not in CI/prod** → environment difference (versions, config, deps)
- **Works sometimes** → race condition; add timestamps to boundary logs

## 3. Before You Claim Done — Verify Through Real Surfaces

**No completion claims without fresh verification evidence.** Run it, read the output, then claim the result.

### Two-Lane Validation
Every completion needs BOTH lanes:

1. **Scrutiny lane** — compiles, tests pass, linter clean, no new warnings
2. **Real-surface lane** — exercise the feature through its actual interface

If either lane fails, the task is not complete.

### Minimum Evidence by Surface

| Surface | Minimum Evidence |
|---------|-----------------|
| HTTP API | Request + response with status code and relevant body |
| Web UI | Browser verification of golden path + one edge case |
| CLI tool | Command + actual output (not expected output) |
| Database | Query showing the data is correct |
| Deployed service | Health check + one real operation |

### Freshness Rule
Evidence is fresh only if collected AFTER the last code change. Any edit — including "trivial" ones — invalidates prior evidence. Re-verify.

### When Verification Is Impossible
If real-surface verification is impossible (no creds, no running env, prod-only behavior):

> "Implemented, UNVERIFIED. Blocked by: [specific reason]. To verify: [exact commands/steps for a human]."

An honest "unverified" beats a false "done." Never convert "I couldn't test it" into "it works."

### Evidence Format
Paste **raw output**, not summaries. "Tests passed" without counts is a claim, not evidence.

## Honest Failure

If an assertion fails — or can't be run — report it as FAILED or BLOCKED with specifics. A documented failure is more valuable than a fabricated pass.

---

## Anti-Rationalization Table

When you think any of these, STOP — you're about to skip a step:

| Thought | Reality |
|---------|---------|
| "I'm confident this works" | Confidence is not evidence. Run the verification. |
| "The tests cover this" | Existing tests weren't written for this change. Check the real surface. |
| "It's a simple change" | Simple changes break things. Verify. |
| "I'll verify later" | Later never comes. Verify now. |
| "The CI will catch it" | CI catches syntax failures, not feature correctness. Run the real-surface check. |
| "Let me just try this fix" | That's guessing, not debugging. Trace the data first. |
| "I think I know what's wrong" | Thinking is not tracing. Verify with evidence. |
| "I'll add some error handling" | Adding error handling without knowing the root cause converts a loud bug into a silent one. |
| "I don't have access to the environment" | Then it's "unverified," not "complete." Say so explicitly. |
| "The user can test it themselves" | Delegating verification is not performing it. Provide exact steps AND mark unverified. |
| "I verified against the mock" | Mocks verify your assumptions, not the surface. State the limitation. |
| "This is too simple for assertions" | Simple capabilities are the easiest to assert. No excuse. |
