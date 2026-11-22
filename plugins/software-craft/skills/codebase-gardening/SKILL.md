---
name: codebase-gardening
description: Audits a whole repository and moves its rules down the trust order (structure, then verification, then prose) before agents write more code in it: lints with agent-actionable messages, directory boundaries, one blessed wrapper per nuance-heavy API, dead code and comment slop removed, a feature map, and a reusable verification driver. Use when preparing a repo for heavy agent use or an autonomous loop, when the same review finding or correction keeps coming back, or when asked to garden, de-slop, or harden a codebase. Don't use for a single feature or bug fix (use engineering-discipline), for slimming AGENTS.md alone (use checkup), or for reviewing one diff (use adlc-prosecutor).
license: Apache-2.0
metadata:
  author: alanblount
  version: "1.0.0"
---

# Codebase Gardening

Agents copy whatever patterns the codebase already has. At high change volume, one anti-pattern spreads into hundreds of files, and prose rules do not stop it. Gardening puts each rule at the lowest layer that can hold it, then removes the weeds the agents would otherwise copy.

> Based on Lauren Tan, "All Code Is Slop (Except Mine)" (Grok Bot: about 11,000 PRs a month, daily releases, about 0.5% revert rate), and her [pstack](https://github.com/cursor/plugins/tree/main/harness/pstack) skills `principle-encode-lessons-in-structure`, `no-comments`, and `create-verification-skill` (MIT).

## Foundations before factories

Do not automate the outer loop (scheduled agents, auto-PR, auto-merge, fuzz-and-fix) on a repo whose inner loop still produces slop. Automation multiplies whatever the inner loop produces, and fixing slop with more tokens is expensive. Run this skill first. The gate at the end says when the repo is ready.

## Trust order

| Layer | Examples | Use for |
|---|---|---|
| 1. Structure | types, compiler, lint rules, import boundaries, CI scripts | every rule a machine can check |
| 2. Verification | unit and property tests, a scripted driver, model checks, proofs | behavior and intent |
| 3. Prose | `AGENTS.md`, skills, comments | judgment that no check can hold |

Work bottom up. Every rule that moves down a layer is one less sentence an agent can ignore.

## Procedure

Work in one change per step so each is easy to review and revert. Record counts as you go for the final report.

### 1. Inventory the corrections

Collect the rules the repo already depends on:

- Every bullet in `AGENTS.md`, `CLAUDE.md`, `GEMINI.md`, `.cursor/rules`, and repo-local skills.
- Repeated review findings (PR comments, prosecutor records, `adlc lesson-foundry` clusters).
- Existing suppressions: `rg -n "eslint-disable|@ts-(ignore|expect-error)|# type: ignore|noqa|nolint|#\[allow\(|@SuppressWarnings|\.skip\(|xit\(|@pytest.mark.skip"`.

Classify each item as **encodable** (a machine can detect a violation), **verifiable** (a test or driver can prove it), or **judgment** (neither).

### 2. Encode the encodable

For each encodable item, add the cheapest check that catches it: a type, an existing lint rule, a custom lint rule, or a small CI script. Then delete the prose it replaces. A rule stated in both places drifts.

Write every lint message for an agent reader:

```
<what is banned>: <one-sentence reason>. Use <blessed API / file / directory> instead.
```

Example: `setTimeout is banned in product code: timers race with React rendering and leak on unmount. Use useScheduledEffect from src/platform/scheduling instead.`

A message that only says "not allowed" invites the agent to find an escape hatch. A message that names the fix gets the fix.

Fix or delete each suppression found in step 1. Keep one only when it covers code you cannot change (generated or vendored code), and then scope it to that path in the lint config, not inline.

### 3. Ban nuance

List the APIs that need judgment to use well. Common candidates:

- React `useEffect`, raw `setTimeout`, `setInterval`, `requestAnimationFrame`, `requestIdleCallback`.
- Raw SQL string building, manual locks and mutexes, unbounded goroutines or tasks, ad hoc retries.
- Direct `fetch`/HTTP clients, direct environment variable reads, global mutable singletons.

For each one the repo uses: write or pick one blessed wrapper with a narrow API, migrate the callers, then ban the raw form everywhere except inside the wrapper. Migrate callers before you delete or ban the legacy form, so the tree is green at every step.

### 4. Put architecture in the filesystem

Make the dependency graph visible in the directory tree, and fail CI on illegal imports. Split runtime boundaries at the top level: `server/` and `client/`, `electron-main/` and `electron-renderer/`, `domain/` and `adapters/`.

Enforcement by ecosystem:

| Ecosystem | Tool |
|---|---|
| TypeScript/JS | `no-restricted-imports`, `eslint-plugin-boundaries`, or `dependency-cruiser` |
| Python | `import-linter` contracts |
| Go | `internal/` packages, `depguard` in golangci-lint |
| Elixir | `boundary` library |
| Bazel/Blaze | `visibility` attributes |

The directory name gives an agent context before it reads a line. The import rule stops it when the context was not enough.

### 5. Pull the weeds

- **Dead code.** Run the ecosystem's finder (`knip` or `ts-prune`, `vulture`, Go `deadcode`, `mix xref`). Delete what is unused. Dead code is a pattern agents will copy.
- **Deprecated patterns.** If two ways exist to do one thing, migrate to one and delete the other.
- **Comment slop.** Delete comments that restate the code, narrate history, or justify a workaround. For a justification comment, fix the root cause. For a constraint comment ("do not remove", "keep in sync with X"), encode the constraint as a type, test, or lint (for example an IFTTT or sync check), then delete the comment. Keep a comment only for a fact the code cannot express: an external contract, a spec or bug reference, or a surprising choice no check can enforce.

### 6. Build the verification layer

Every repo with a UI, CLI, or multi-step flow needs one scripted way to drive the real app. A reused driver costs fewer tokens than a fresh harness per task, and the driver itself is tested.

1. **Driver.** One command each to launch from an empty data dir, check health (`doctor`), drive a feature, capture evidence, and clean up. Prefer the repo's existing harness (Playwright, a PTY or tmux helper, curl). Never drive or kill an instance the run did not start.
2. **Feature map.** A user-perspective index of every feature, so humans and agents use the same names for the same screens. Shape: [`references/feature-map.md`](references/feature-map.md).
3. **Deeper checks, where they pay:** property-based tests for state machines and UIs (for example `fast-check`, Hypothesis, or a UI property tester such as Bombadil); model checking (TLA+) for flows across devices or services; proofs (Lean) only for small, critical algorithms.
4. **Reviewable evidence.** A screenshot, video, terminal transcript, or statechart lets a human review behavior without reading every line of the diff. Make the driver write these to a fixed path that cleanup does not delete.

### 7. Slim the prose

Re-read the instruction files. For each bullet: if a check now enforces it, delete it. If it duplicates the tool's own help or another file, delete it. What remains should be judgment calls, each with one example of the failure it prevents. A short `AGENTS.md` that points at `verify` and the feature map beats a long one that restates the linter. If prose rules remain, keep them in one `Rule | Enforced by | Level` table so a prose-only row that gets violated again is visibly the next one to encode.

## Gate: ready for automation

Report each line as PASS or FAIL with evidence (a command and its output):

- [ ] Lint, typecheck, and boundary checks run in CI and pass with zero inline suppressions outside generated or vendored code.
- [ ] Each banned nuance API has a blessed wrapper and a lint ban.
- [ ] Dead-code finder reports zero findings, or each finding is listed with a reason.
- [ ] One driver command launches, checks, drives, captures evidence for, and cleans up the app. You ran it end to end once.
- [ ] A feature map exists and the driver covers at least the top three features.
- [ ] Instruction files contain no rule that a check already enforces.

Only after every line passes, build loops on top.

## Report

End with counts: rules encoded, prose bullets deleted, suppressions removed, nuance APIs banned, boundary rules added, dead-code items deleted, comments deleted, features mapped. List the judgment rules that stay as prose and the work left open.
