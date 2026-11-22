---
name: engineering-discipline
description: Core engineering loop for any code change bigger than a trivial edit. Picks a size tier, writes a short spec whose acceptance criteria each end in "Verify:" for medium work, debugs from root cause, never weakens tests or adds suppressions, and verifies through the real surface before claiming done. Use for a multi-file feature, a bug or ticket whose cause you still have to find, a refactor, or an unclear request, and load it together with any specialized skill (UI, Elixir, security). Don't use for a new project, a multi-PR build, or a risky migration (use spec-kit-adlc), or for repo-wide cleanup (use codebase-gardening).
license: Apache-2.0
metadata:
  author: alanblount
  version: "2.0.0"
---

# Engineering Discipline

The per-task loop: size it, spec it if needed, build in small verified steps, debug from root cause, prove it works. Specialized skills (UI, Elixir, security) add domain rules on top of this loop. They never replace it.

> Distilled from [obra/superpowers](https://github.com/obra/superpowers) (Apache 2.0), [Intelligent-Internet/zenith](https://github.com/Intelligent-Internet/zenith) (Apache 2.0), Lauren Tan's [pstack](https://github.com/cursor/plugins/tree/main/harness/pstack) principles (MIT), Addy Osmani's [agent-skills](https://github.com/addyosmani/agent-skills) (MIT), and the [ADLC](https://github.com/voodootikigod/adlc) doctrine.

## 1. Pick the tier

State it in one line before the first edit: `Tier: medium (3 files, sharing rules unclear)`. Pick by blast radius and clarity, not line count.

| Tier | Signal | Process |
|---|---|---|
| Trivial / small | One place, clear ask, easy to revert | Core rules only. No spec. |
| Medium | Several files, new behavior, unclear ask, or a bug with no known cause | Short spec (section 2), then sections 3-5 |
| Large | New project, several PRs, risky migration, or a data, auth, or public-API change that is hard to revert | Stop and load `spec-kit-adlc` |

When in doubt between two tiers, pick the higher one and keep its artifacts short.

## 2. Medium: write a short spec first

Show the spec before code. Fill it from the codebase and the request; do not interrogate the user. Ask only what the code, docs, or a quick experiment cannot answer, in one message, each question with your recommended answer. Then continue on your assumptions unless the user objects.

```markdown
## Goal
<one or two sentences: who gets what>

## Non-goals
- <what this change will not do>

## Assumptions
- <each guess you made; the user corrects these>

## Acceptance criteria
- AC-1: <observable behavior>. Verify: `<command>` or <surface check>
- AC-2: <failure or edge path>. Verify: ...
```

Rules for criteria:

- Each one is observable (no source reading), falsifiable (it can fail), and ends in `Verify:` with a command or a surface check. One per user-visible capability, usually 3-7, with at least one failure path.
- This format passes `adlc spec-lint`. Run `adlc spec-lint <file>` when the spec lives in a file; exit 0 means every criterion has a verification method.
- Put the spec in the PR description, or in `specs/<slug>/spec.md` if it should outlive the PR. The same layout grows into a spec-kit spec if the work turns large.
- If the user says to skip the spec, say once what the risk is, then do what they ask.

## 3. Build in small verified steps

- Make the smallest change that meets the goal. Delete before you add. Do not add layers, flags, or abstractions the spec does not need.
- Split the work into units that each end in a state you can check. Check each unit before you start the next.
- Stay in scope. Report nearby problems; do not fix them unasked.
- Name the data shape before you write logic that depends on it.

## 4. Debug from root cause

Never guess at fixes.

1. **Reproduce.** Read the full error and stack trace. Get one command that shows the failure. If you cannot reproduce it, you cannot verify a fix; get repro information first.
2. **Trace boundaries.** Log what enters and leaves each component. The first point where data diverges from expectation is where the bug lives.
3. **Compare.** What differs between a working case and the broken one: input, environment, recent changes (`git log`, deploys, config)?
4. **Predict, then test.** Write down one hypothesis and what you expect to see if it is right and if it is wrong. Then run it. Change one variable at a time.
5. **Fix the cause, not the symptom.** A guard is a fix only when the state it handles is legitimate. If this class of bug can recur, add the check that would have caught it (section 6).

Escalate: after two failed fixes that share one premise, write the premise down and test it directly. After three, question the design. "Works locally, fails in CI" means an environment difference. "Works sometimes" means a race; timestamp the boundary logs.

## 5. Verify through the real surface

No completion claim without fresh evidence. Name the success signal before you run the check, then point at it in the output.

Every change needs both lanes:

1. **Scrutiny**: builds, tests pass, lint clean, no new warnings.
2. **Real surface**: exercise the feature through its actual interface.

| Surface | Minimum evidence |
|---|---|
| HTTP API | Request and response with status and relevant body |
| Web UI | Golden path and one edge case in a browser |
| CLI | The command and its actual output |
| Database | A query that shows the data is right |
| Deployed service | Health check and one real operation |

- **Freshness.** Evidence counts only if collected after the last edit. Any edit, even a "trivial" one, invalidates it.
- **Reuse the driver.** Use the repo's `verify` script or verification skill instead of a fresh harness. If none exists for a UI or multi-step flow, propose one (codebase-gardening).
- **Raw output.** "Tests passed" without counts is a claim, not evidence.
- **When you cannot verify**, end with: `Implemented, UNVERIFIED. Blocked by: <reason>. To verify: <exact steps>.` An honest "unverified" beats a false "done".

Before you call it done:

- Check each acceptance criterion against its `Verify:` line.
- For a risky diff (shared code, data, auth, concurrency), find what it could break outside the diff. Name the one fact that makes it safe and prove that fact by running code.
- For a high-stakes change, offer an independent review: `adlc-prosecutor` (one refute pass against the spec) or `council` (multi-model loop).
- Report the outcome as done, partial, failed, or blocked, with evidence.

## 6. Put rules in structure, not prose

Agents copy the patterns in front of them, and prose rules need judgment. Put each rule at the lowest layer that holds it: structure (types, lint, import boundaries, CI), then verification (tests, a driver), then prose (AGENTS.md, skills, comments).

- **Encode the second correction.** When the same mistake is corrected twice, add a lint, type, test, or script that catches it, then delete the prose that described it. Prove the new check fails on the real past mistake. If the pattern is widespread, fail only on new occurrences first, then clean up the old ones.
- **Lint messages name the fix**: what is banned, why in one sentence, and the blessed replacement.
- **Never lower the bar to get green.** No `eslint-disable`, `@ts-ignore`, `# type: ignore`, `noqa`, `nolint`, skipped or weakened tests, or lowered thresholds. If a rule is wrong, change the rule in its own change.
- **No justification comments.** A comment that explains a workaround marks a root cause you did not fix. Keep comments only for facts the code cannot express.
- **One blessed way.** Wrap a nuance-heavy API (React `useEffect`, raw timers, manual locks) in a narrow wrapper and ban the raw form.

## 7. Inside an ADLC ticket

In an ADLC ticket (an `agb` fleet run, or a ticket with declared `scope` and `rails`), the ticket governs scope and completion. These rules hold whether or not `adlc-doctrine` is loaded, and it wins where it says more:

- The ticket's acceptance criteria are the spec. Do not write a second set.
- Edit only files inside `scope`. Never edit a `rails` path or weaken a test to pass a gate.
- Do not add checks outside scope. Record a finding that needs one with `adlc prosecute --record-finding`.
- End with `TICKET-DONE` (every gate green, run by you) or `TICKET-BLOCKED: <reason>`, not "UNVERIFIED".

## Anti-rationalization

| Thought | Reality |
|---|---|
| "It's a simple change" / "The tests cover this" | Existing tests were not written for this change. Check the real surface. |
| "Let me just try this fix" | That is guessing. Trace the data first. |
| "I verified against the mock" | Mocks check your assumptions, not the surface. Say so. |
| "A quick disable gets this green" | A suppression hides the root cause. Fix it or report blocked. |
| "I'll add a note to AGENTS.md" | If a check can enforce it, write the check. |
| "This needs a spec, I'll ask ten questions" | Draft the spec from the code, list assumptions, ask only what is left. |
