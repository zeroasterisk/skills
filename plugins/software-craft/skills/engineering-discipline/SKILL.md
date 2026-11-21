---
name: engineering-discipline
description: Per-task engineering lifecycle. Define what done means, debug from root cause, encode recurring corrections as lints or types instead of prose, and verify through real surfaces before claiming completion. Use for any non-trivial build, fix, or refactor. Don't use for repo-wide cleanup before scaling agent output (use codebase-gardening).
license: Apache-2.0
---

# Engineering Discipline

The full engineering lifecycle in one process: define → build → debug → verify. Follow this for every non-trivial task.

> Distilled from [obra/superpowers](https://github.com/obra/superpowers) (Apache 2.0), [Intelligent-Internet/zenith](https://github.com/Intelligent-Internet/zenith) (Apache 2.0), and Lauren Tan's talk "All Code Is Slop (Except Mine)" with her [pstack](https://github.com/cursor/plugins/tree/main/harness/pstack) principles (MIT).

---

## 0. Trust Order: Structure, Then Verification, Then Prose

Agents copy the patterns in front of them. Prose rules need judgment, and judgment is where slop comes from. Put each constraint at the lowest layer that can hold it:

1. **Structure** (cheapest to obey, impossible to skip): types, compiler errors, lint rules, directory boundaries, import restrictions, CI checks.
2. **Verification**: tests, runtime drivers, property-based tests, model checks. These prove intent.
3. **Prose** (last resort): `AGENTS.md`, skills, comments. Only for rules that need judgment and cannot be checked.

Rules that follow from this order:

- **Encode the second correction.** When you correct the same mistake twice (yours, a reviewer's, or another agent's), add a lint, type, test, or script that catches it. Then delete the prose that described it. If it truly cannot be encoded, make the prose prominent and add an example of the failure.
- **Write lint messages for agents.** Name the banned pattern, give the reason in one sentence, and name the blessed replacement (API, file, or directory). A message that only says "not allowed" invites an escape hatch.
- **Fix the root cause, not the check.** Never add a lint suppression, `@ts-ignore`, `# type: ignore`, `nolint`, or skipped test to get green. If the rule is wrong, change the rule in its own change.
- **No justification comments.** A comment that explains a workaround ("we need this because X is flaky") marks a root cause you did not fix. Fix it, or encode the constraint as a check. Keep comments only for facts the code cannot express: an external contract, a spec reference, or a surprising choice that a check cannot enforce.
- **Prefer one blessed way.** When a feature needs nuance to use well (for example React `useEffect`, raw timers, manual locks), use or create a wrapper with a narrow API and ban the raw form outside it.

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
Fix the cause, not the symptom. Then verify through the real surface (see section 3). If this class of bug can recur, add the check that would have caught it (section 0).

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

### Reuse the Driver
Verify through the project's scripted driver (a `verify` script, CLI, or project-local verification skill) instead of writing a fresh harness each time. A reused driver costs fewer tokens and is itself tested. If none exists and the surface is a UI or a multi-step flow, propose one (see codebase-gardening). Name features with the words in the project's feature map, so you and the user mean the same screen.

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

## Inside an ADLC Ticket

When you work an ADLC ticket (an `agb` fleet run, or a ticket with declared `scope` and `rails`), `adlc-doctrine` wins on scope, rails, and completion. Specifically:

- **Acceptance criteria are your VAL-\* assertions.** Do not write a second set.
- **Do not add checks outside scope.** If a lint, type, or test would prevent a recurring defect but lives outside the ticket's scope or in a rail (CI config, contracts, frozen tests), record it with `adlc prosecute --record-finding`. P7 (`lesson-foundry`) turns it into a check.
- **End with the doctrine's markers.** Where this skill says "Implemented, UNVERIFIED", end with `TICKET-BLOCKED: <reason>` instead. Use `TICKET-DONE` only when every gate is green and you ran it.

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
| "I'll add a note to AGENTS.md" | If a check can enforce it, write the check. Prose is the last resort. |
| "A quick disable comment gets this green" | A suppression hides the root cause. Fix it or block. |
| "I'll leave a comment explaining the workaround" | The comment documents a bug you chose not to fix. Fix it. |
