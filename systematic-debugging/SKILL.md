---
name: systematic-debugging
description: Four-phase root cause debugging process. Prevents fix-by-guessing and ensures the actual cause is found before the fix is applied.
---

# Systematic Debugging

Find the root cause before applying a fix. Never guess at fixes — trace the data flow, form hypotheses, test one variable at a time.

> Adapted from [obra/superpowers](https://github.com/obra/superpowers) systematic-debugging skill (Apache 2.0).
> Additional patterns from [Intelligent-Internet/zenith](https://github.com/Intelligent-Internet/zenith) engineering-mission-playbook (Apache 2.0).

## Four Phases

### Phase 1: Root Cause Investigation

Trace the data flow through every component boundary. At each boundary, log what enters and what exits.

```
Input → Component A → [boundary] → Component B → [boundary] → Component C → Output
         ↑ log here      ↑ log here      ↑ log here      ↑ log here
```

Find the first boundary where the data is wrong. That's where the bug lives.

### Phase 2: Pattern Analysis

Compare a working case with the broken case:
- What's different in the input?
- What's different in the environment?
- What changed since it last worked? (git log, deploy history, config changes)

### Phase 3: Hypothesis and Testing

Form ONE hypothesis. Test it by changing ONE variable. Observe the result.

- If the hypothesis was correct: you found the bug. Proceed to fix.
- If the hypothesis was wrong: form a NEW hypothesis. Do NOT layer fixes on top of a wrong diagnosis.

**Critical rule: change ONE variable at a time.** Multiple changes at once make it impossible to know which one fixed (or broke) things.

### Phase 4: Implementation

Fix the root cause, not the symptom. Then verify the fix through the real surface (see: verification-before-completion skill).

## Escalation Rules

- **3+ failed fix attempts** → Stop fixing symptoms. Question the architecture. The bug may be a design problem, not a code problem.
- **Fix works locally but not in CI/prod** → Environment difference. Compare: versions, config, dependencies, OS, network.
- **Fix works sometimes** → Race condition or state-dependent bug. Add logging at boundaries and reproduce under load.

## Multi-Component Evidence Gathering

For distributed systems (like A2A message relays), log what data enters and exits each component:

```
Client request → API endpoint → Router → Controller → Context module → DB
                 ↑ request body  ↑ params  ↑ changeset  ↑ query result
```

The first point where data diverges from expectation is the bug location.

## Common Rationalizations

| Rationalization | Reality |
|----------------|---------|
| "Let me just try this fix" | That's guessing, not debugging. Trace the data first. |
| "I think I know what's wrong" | Thinking is not tracing. Verify your assumption with evidence. |
| "I'll add some error handling" | Error handling hides bugs. Find the root cause first. |
| "It's probably a race condition" | Probably is not evidence. Add timestamps to your boundary logs. |
