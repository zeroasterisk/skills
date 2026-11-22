---
name: spec-kit-adlc
description: Plans and de-risks a large build by pairing GitHub spec-kit (spec.md, plan.md, tasks.md) with ADLC gates (spec-lint, premortem, rails-guard, prosecution) and, for parallel work, an agb fleet. Use when starting a new project or service, a feature that spans several PRs or weeks, or a risky migration or data, auth, or public-API change that is hard to revert. Don't use for a single-PR feature or a bug fix (use engineering-discipline), or for running one named ADLC gate on an existing spec (use adlc).
license: Apache-2.0
metadata:
  author: alanblount
  version: "1.0.0"
---

# Spec Kit + ADLC for Large Work

spec-kit writes the artifacts. ADLC checks them. agb fans them out when the work is parallel. `engineering-discipline` still governs each task.

> Uses [github/spec-kit](https://github.com/github/spec-kit) (MIT) and the [ADLC toolkit](https://github.com/voodootikigod/adlc) (`adlc`, `agb`).

## 0. Recommend, once

Tell the user in one or two sentences why this work is large and that you recommend spec-kit plus ADLC gates. If they decline, use the `engineering-discipline` short spec in `specs/<NNN-slug>/spec.md` and keep the ADLC gates in steps 3, 6, and 7. Do not raise it again.

Setup, once per machine and once per repo (the user runs installs):

```bash
uv tool install specify-cli
specify init . --integration opencode   # CloudCode; use --integration agy for Jetski
adlc --version && agb doctor            # gates and fleet available
```

`specify init` installs the `/speckit-*` commands for the agent. The user runs them in chat, or asks you to; then follow the matching command file the integration installed. Run one at a time and review each result before the next.

## 1. Constitution

`/speckit-constitution` once per repo. Seed it with the repo's lint and test commands and these principles, so the plan's "Constitution Check" enforces them:

- Every functional requirement and acceptance scenario ends in `Verify: <command or surface check>`.
- Tests and real-surface verification are required for every user story. (spec-kit's tasks template calls tests optional; this overrides it.)
- No suppressions or weakened tests. Fix the cause or report blocked.

## 2. Specify and clarify

1. `/speckit-specify <what and why>` writes `specs/<NNN-feature>/spec.md`.
2. `/speckit-clarify` resolves `[NEEDS CLARIFICATION]` markers. It replaces ad hoc interrogation. Answer from the codebase first; bring the user only what is left, with a recommended answer each.

## 3. Gate the spec (ADLC P1)

A raw spec-kit `spec.md` fails `spec-lint`: every `FR-*` line and every Given/When/Then acceptance scenario is parsed as a criterion, and none has a verification method. Add one to each:

```markdown
- **FR-001**: System MUST let a user export the visible table as CSV. Verify: `bun test export.test.ts`
1. **Given** an empty table, **When** the user clicks Export, **Then** "Nothing to export" shows. Verify: Playwright journey `export-empty`
```

Then:

```bash
adlc spec-lint specs/<NNN-feature>/spec.md                       # expect exit 0
adlc spec-lint specs/<NNN-feature>/spec.md --record --ticket <NNN>
adlc premortem specs/<NNN-feature>/spec.md --prompt-only           # answer the printed prompt yourself
```

Fold each real premortem failure mode back into `spec.md` as an edge case or a criterion, and re-run `spec-lint`. Ask the user to approve the spec before planning.

## 4. Plan and declare rails

1. `/speckit-plan <stack and constraints>` writes `plan.md` (plus `data-model.md`, `contracts/` as needed).
2. In `plan.md`, add a **Rails** section: the paths no build task may edit (contract tests, `contracts/`, frozen fixtures, CI config).
3. For a risky migration or a one-way design decision, get an independent review of `spec.md` and `plan.md` before tasks: `council`, or `adversarial-review --prompt-only`.

## 5. Tasks and readiness (ADLC P2)

1. `/speckit-tasks` writes `tasks.md`. `/speckit-analyze` checks spec, plan, and tasks agree. Fix what it reports.
2. Pick the execution path:
   - **One session**: work `tasks.md` in order. Each task runs under `engineering-discipline`; its criteria are the spec lines it implements.
   - **Parallel fleet** (3 or more tasks with disjoint file scopes): `agb plan specs/<NNN-feature>/tasks.md <repo>` compiles a `plan.json` (agb accepts any markdown file as the plan; if tickets come out thin, concatenate `plan.md` and `tasks.md` into one file first) and runs the overlap, coldstart, parallax, and premortem gates. Put the plan's Rails paths in every ticket's `rails`. Check with `agb validate plan.json`, then `agb run plan.json` (see `adlc-self-orchestrate` in Jetski).
   - Before a hand-written ticket runs, `adlc coldstart <ticket> --prompt-only` must find nothing a fresh agent would have to guess.

## 6. Build with rails (ADLC P3, P4)

- Commit the contract and acceptance tests first, then treat them as frozen.
- `adlc rails-guard --base <ref> --ticket <NNN>` must pass. Make it a required CI check.
- An agent that loops or drifts: `adlc flail-detector <log>`. A hard failing test: `adlc consensus-fix`.

## 7. Prosecute each PR (ADLC P5)

- `adlc hollow-test --test-cmd "<test command>"`: tests that pass without testing the behavior.
- `adlc-prosecutor` against the spec's criteria; record each surviving finding with `adlc prosecute --record-finding`.
- For a migration or behavior change, `adlc behavior-diff capture` before and `compare` after, for the human gate.
- For trust-critical code, a cross-model review (`council`, or `adversarial-review --providers A,B`).
- `/speckit-converge` until it reports converged. Re-run `spec-lint` after any spec change.

## 8. Distill (ADLC P7)

Findings that repeat across PRs become checks: `/adlc-distill`, or `codebase-gardening` for repo-wide rules.

## Mapping

| spec-kit artifact | ADLC / agb use |
|---|---|
| `constitution.md` | Standing rules the plan is checked against |
| `spec.md` (FR, scenarios, success criteria) | `spec-lint`, `premortem`, spec-approval record, prosecution charge sheet |
| `plan.md` Rails section | ticket `rails`, `rails-guard` in CI |
| `tasks.md` (`[P]`, file paths, story phases) | `agb plan` input; `[P]` tasks become parallel tickets, phases become edges; `coldstart` per ticket |
| `/speckit-converge` | re-check against the spec after each build round |
