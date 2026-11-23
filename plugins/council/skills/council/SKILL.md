---
name: council
description: >-
  Convenes three independent, cold-start subagent delegates in parallel (using configured multi-model seats in ~/.config/council/roster.json with automatic fallback, or pro-tier council-delegate subagents) with isolated context, read-only tools, and findings-first adversarial scoring, looping by default until all three delegates score >= 9/10 while fighting scope creep. Trigger on "/council", "c9" (shorthand for "keep working until 9/10 from the council"), "/council <N>", "/council once", "council", "the council", "ask the council", or common misspellings ("counsil", "coucil", "concil", "councel"). Use only when the user asks for the council or a multi-model review loop. Don't use for an ordinary code review (core rules) or a single refute pass of a diff against its spec (use adlc-prosecutor), or for persona onboarding walkthroughs (use developer-friction-reviewer).
license: Apache-2.0
compatibility: Designed for Jetski / Antigravity (run_workflow, define_subagent, invoke_subagent, declarative model-pinned agent.json) with fallback to T3 Code and standard subagent harnesses.
metadata:
  author: alanblount
  version: "1.1.0"
---

# Council

Convene three independent delegates in parallel to evaluate the user's request (typically a code review, RFC/design critique, or architectural exploration) using **isolated subagents with zero shared context and zero shared mutable state**.

Adapted from [`t3dotgg/tstack`'s `council` skill](https://github.com/t3dotgg/tstack/blob/main/skills/council/SKILL.md) for the Jetski / Antigravity harness.

## Default Configuration

Unless the user overrides a setting in their prompt, run with these defaults:

| Setting | Default | Override Behavior |
| :--- | :--- | :--- |
| **Delegates** | `3` neutral delegates (`seats[0..2]`) | Identical prompt, zero persona framing unless the user names council members or focus roles. |
| **Model Roster** | `~/.config/council/roster.json` -> `pro` fallback | When `~/.config/council/roster.json` exists, runs its 3 model-pinned subagents (`seats[0..2]`, substituting `fallback` if any primary seat fails or is unavailable). Otherwise runs `council-delegate` on `model="pro"` (or 3 flagship providers in T3 Code). |
| **Tools & State** | Read-only (`commandExecutionPolicy: off`) | No `write_file`, `edit_file`, `run_command`, or subagent tools; `Workspace: "inherit"`, isolated `<appDataDir>/brain/<subConvID>/`. Uses `Workspace: "branch"` only when executing tests or competing prototypes. |
| **Context** | Cold start every round | `Fork: false`, no `swarm` board, no author rationale, fresh conversations every round. |
| **Scoring Rubric** | Findings-first adversarial (`10.0` minus deductions) | Delegates generate `findings` (`blocker` = `-2.0`, `major` = `-1.0`, `minor` = `-0.5`) *before* `score` to prevent 1-round `10/10` rubber-stamping. |
| **Convergence Gate** | All `3` score `>= 9/10` & satisfied | Default for scored reviews (`/council` or `c9`). Override with `/council <N>` (supports half-points such as `/council 9.5`), `c<N>`, or `/council once` for a single pass. Non-scored ideation runs `1` round. |
| **Max Rounds** | `5` rounds safety cap | Stops early and reports to the user if scores plateau or remaining asks are out-of-scope scope creep. |

### Shorthand Triggers

* **`/council`** or **`c9`**: Run pre-audit checks, convene the 3-delegate council, and keep fixing in-scope issues across fresh cold-start rounds until all 3 delegates score **`>= 9/10`** (`satisfied: true`).
* **`/council <N>`** or **`c<N>`** (e.g., `/council 8`, `/council 9.5`, `/council 10`, `c10`): Same convergence loop with target score bar set to `N/10`.
* **`/council once`** (or `"one round"`): Run a single 3-delegate review pass and report scores/findings without looping.

## 1. Pre-Audit Hygiene

Before convening the council on an implementation or specification:
1. Address outstanding PR/CL or document comments, fix issues you already know about, and run relevant local checks (build, typecheck, lint, tests, link/anchor checks).
2. Give the council the updated, verified artifact; do not defer known fixes until reviews return.
3. **Exception**: If the user wants to discard the current implementation and explore new ideas, skip fixing code that is being replaced.

## 2. Isolation Invariants (Mandatory)

Every council round must preserve three strict isolation boundaries so delegates cannot anchor on you or on each other:

* **Context isolation (cold start, no rationale)**:
  * Never use shared message boards (`swarm`) or conversation forking (`Fork: true`).
  * Every delegate starts in a fresh, single-round conversation and sees **only** the objective brief: the user's request, target file paths / diff snapshot, and verification status.
  * Do **not** include your own defensive rationale, excuses, prior scores, or prior delegates' opinions.
* **Neutrality by default**:
  * Unless the user explicitly names focus personas, give all three delegates the **exact same neutral prompt** with zero persona roleplay. Diversity comes from distinct models (`roster.json`) and independent cold-start exploration paths.
* **State & tool isolation**:
  * **Review / feedback (default)**: Keep delegates strictly **read-only** at the tool boundary (no write, edit, shell, or subagent tools). Each delegate gets its own isolated conversation and `<appDataDir>/brain/<subConvID>/` state directory, and cannot mutate files or run shell commands.
  * **Competing prototypes or test execution (only when required)**: If delegates must execute commands or prototype competing approaches, define a separate worker subagent and spawn each with `Workspace: "branch"` (`workspace="branch"` in `run_workflow`) so each delegate gets an isolated workspace clone and independent environment ID.

## 3. Multi-Model Roster, Pinning & Fallback Rules

1. **Check `~/.config/council/roster.json` first**:
   * Read `~/.config/council/roster.json` if present on the local machine. It defines `seats` (3 entries with `label`, `type_name`, and `agent_json`) plus an optional `fallback` seat.
   * **How model pinning works in Jetski**: Request-time `Model` strings in `invoke_subagent` / `run_workflow` only accept tier names (`pro`, `inherit`, `flash`, `flash_lite`), *not* arbitrary model slugs. To pin distinct models on read-only council delegates, Jetski uses declarative `~/.gemini/config/agents/<type_name>/agent.json` specs setting `"disableModelSelection": true` and `"cascadeConfig": {"plannerConfig": {"planModel": "<MODEL_ENUM>"}}`. When invoked by `type_name` (omitting `model` in `agent()` or passing `Model="inherit"`), the harness keeps each subagent's pinned `planModel`.
   * **Zero-restart staging**: If a model-pinned `agent.json` was added mid-session after the current conversation started (agents added later are not visible until staged), copy each seat's `agent_json` into `<artifactDir>/.agents/agents/<type_name>/agent.json` (with `_agents -> .agents` symlink) before running `run_workflow`.
   * **Automatic fallback seat**: If a requested model is unavailable in the harness's model list or errors out at runtime (e.g., quota/capacity exhaustion), substitute the `fallback` seat from `roster.json` and label the delegate row transparently with the actual model that ran.
2. **Default fallback when no `roster.json` exists**:
   * **Jetski / Antigravity**: Run three isolated `council-delegate` subagents on `model="pro"`.
   * **T3 Code**: Use `orchestrator_capabilities` + `delegate_task` to pick three flagship models across providers at high reasoning effort.
3. **Never fake or silently substitute**: Always verify live availability when configuring new models and label every row in `## Council review` with the exact model or delegate type that actually executed.

## 4. Running a Council Round in Jetski

See [`references/jetski-harness.md`](references/jetski-harness.md) for copy-pasteable `roster.json`, declarative `agent.json`, and `run_workflow` templates.

1. **Ensure read-only subagent types exist**:
   * Load `~/.config/council/roster.json` if present (ensuring each seat's `agent.json` is registered or staged under `<artifactDir>/.agents/agents/`), or fall back to `council-delegate`.
2. **Prepare an objective, pointer-based brief**:
   * State the user's goal/requirement, list target files (or write a clean diff/document snapshot to your conversation `scratch/` directory, never inside the repository working tree), and state what checks already passed.
   * Explicitly instruct each delegate to follow the **findings-first adversarial rubric**: list concrete findings (`blocker` = `-2.0`, `major` = `-1.0`, `minor` = `-0.5`) *first*, then compute `score` out of 10 (`N/10`, starting from `10.0` minus deductions) and `satisfied` (`true/false`).
   * Ask each finding to carry an `encode` field: the lint rule, type, or test that would catch this class of defect mechanically, or `none` if it needs judgment.
   * Do **not** tell delegates what target score bar the user set (e.g., `9/10` or `9.5/10`), or they may grade-inflate to stop the loop.
3. **Fan out 3 isolated delegates in parallel**:
   * **Preferred (`run_workflow` enabled)**: Run a single `run_workflow` call using `from advanced import parallel` (`return_exceptions=True`) over the 3 seats, retrying any failed primary seat once on `fallback` when configured. Place `findings` *before* `score` in the `finish` JSON schema `properties` and `required` list so structured decoding generates findings before committing to a score.
   * **Fallback (`invoke_subagent`)**: Emit three `invoke_subagent` calls in the **same turn** (`TypeName` set to each seat's `type_name`), then end your turn and wait reactively for their completion messages (do not poll).

## 5. Synthesis, Target Score Loops & Scope Defense

1. **Synthesize honestly**: Collect all three delegate responses and summarize:
   * **High-value findings** backed by concrete file/line or architectural evidence.
   * **Disagreements** across delegates (surface split opinions explicitly rather than averaging them away).
   * **Recommended next steps**.
   * **Checks to add**: findings with a non-`none` `encode` field, and any finding that repeats across rounds or delegates. Add the check with the fix, so the next round (and the next agent) cannot repeat the defect. A finding fixed twice by hand is a missing lint.
2. **Treat 1-round `10/10` as a sycophancy smell & fight scope creep**:
   * Enforce the findings-first rubric so genuine flaws deduct points (`blocker` `-2.0`, `major` `-1.0`, `minor` `-0.5`).
   * At the same time, reject out-of-scope features, speculative abstractions, stylistic churn, and nits that do not materially improve correctness, clarity, or safety. Your job as orchestrator is to fix every real in-scope defect while keeping scope tight.
3. **Multi-round convergence & target score gates**:
   * Each full 3-delegate pass counts as **one round**.
   * **Stopping rule**:
     * **Default (scored reviews, `/council`, or `c9`)**: Every delegate scores **`>= 9/10`** and is satisfied (`satisfied: true`), with no valid in-scope blockers remaining.
     * **Custom score bar (`/council <N>`, `c<N>`, or `"until 9.5/10"`)**: Every delegate scores **`>= N/10`** (`float(score) >= float(N)`) and `satisfied: true`, with no valid in-scope blockers remaining.
     * **Single-pass override (`/council once` or exploratory `no score` prompts)**: Stop after Round 1 and present the synthesized findings.
   * When valid in-scope fixes remain (or scores are below the user's bar for valid reasons): implement the fixes, re-run verification checks, write a fresh clean snapshot for the new round (without prior round scores or excuses), and launch **three brand-new cold-start delegates** (`Round 2`, `Round 3`, ..., capped at `5` rounds max unless the user asks for more).
   * If a delegate withholds points solely for out-of-scope scope creep or scores plateau at the round cap, stop, decline the scope creep explicitly, and report the honest scores to the user.

## 6. Scorecard Output Placement

For scored reviews, track every round in this exact Markdown table:

```markdown
## Council review

Rounds: 2

| Delegate | Round 1 | Round 2 |
| --- | --- | --- |
| Seat 1 (<Actual Model 1>) | 7.5/10 | 9.5/10 |
| Seat 2 (<Actual Model 2>) | 8/10 | 9.5/10 |
| Seat 3 (<Actual Model 3>) | 7/10 | 10/10 |
```

* **Honest labels & scores**: Replace the `Delegate` column names with the exact models that ran (including any fallback substitution). If a delegate gives no score, write `no score`. Do not invent one.
* **Chat-only by default**: Show the `## Council review` scorecard in your chat response only. Do **not** insert `## Council review` scorecards or internal agent process artifacts into PR/CL descriptions or published documents unless the user or the target repository's `AGENTS.md` explicitly asks for it.
