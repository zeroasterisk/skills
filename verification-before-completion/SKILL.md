---
name: verification-before-completion
description: Verify outcomes through real surfaces before claiming completion. Prevents false confidence from code review alone.
---

# Verification Before Completion

No completion claims without fresh verification evidence. Run it, read the output, then claim the result.

> Adapted from [obra/superpowers](https://github.com/obra/superpowers) verification-before-completion skill (Apache 2.0).
> Additional patterns from [Intelligent-Internet/zenith](https://github.com/Intelligent-Internet/zenith) user-testing-validator (Apache 2.0).

## The Rule

**Before declaring any task complete, you MUST have fresh evidence from the real surface** — not from reading the code, not from "I'm confident," not from "the tests should cover it."

Evidence means: command output, HTTP response, browser screenshot, test results, or deployed service verification that you collected THIS session.

## Two-Lane Validation

Every completion claim needs BOTH lanes:

1. **Scrutiny lane** — code compiles, tests pass, linter clean, no warnings
2. **Real-surface lane** — actually exercise the feature through its real interface (API call, browser, CLI command)

If either lane fails, the task is not complete.

## Surface Types and Minimum Evidence

| Surface | Minimum Evidence |
|---------|-----------------|
| HTTP API | Request + response with status code and relevant body |
| Web UI | Browser verification of the golden path + one edge case |
| CLI tool | Command + actual output (not expected output) |
| Database | Query showing the data is correct |
| Deployed service | Health check + one real operation |

## Common Rationalizations (Red Flags)

When you think any of these, STOP — you're about to skip verification:

| Rationalization | Reality |
|----------------|---------|
| "I'm confident this works" | Confidence is not evidence. Run the verification. |
| "The tests cover this" | Tests verify code correctness, not feature correctness. Check the real surface. |
| "It's a simple change" | Simple changes break things. Verify. |
| "I already verified something similar" | Similar is not same. Verify this specific change. |
| "I'll verify later" | Later never comes. Verify now. |
| "The CI will catch it" | CI catches syntax and unit test failures. It doesn't check if the feature works for a user. |
| "I just need to push and deploy" | Push and deploy are transport, not verification. |

## How to Apply

1. Make your change
2. Run scrutiny lane (compile, test, lint)
3. Run real-surface lane (exercise the actual feature)
4. Record the evidence (paste output, screenshot, response)
5. THEN claim completion, citing the evidence
