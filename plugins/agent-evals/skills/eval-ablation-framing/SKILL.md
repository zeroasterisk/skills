---
name: eval-ablation-framing
description: >-
  Frames agent evaluations, benchmarks and leaderboards as held-constant
  ablations across three factors: Model, Harness, and Task Adaptation (none,
  pre-baked skill, or self-customization where the agent builds its own tools
  first). Use when deciding which eval cells to run next, designing a
  benchmark matrix, writing an eval report, or laying out a leaderboard UI so
  each product category gets a clear story without overwhelming viewers.
  Don't use for writing a single grader or task (build those first), or for
  generic statistics questions unrelated to agent evals.
license: Apache-2.0
metadata:
  author: alanblount
  version: "1.0.0"
---

# Eval Ablation Framing

Agent results mix three causes: the model, the harness around it, and how the
setup was adapted to the task. A single leaderboard number hides which one
produced the result. Report deltas between cells that differ in exactly one
factor, and choose which cells to run by the claims they support.

## The three factors

| Factor | Levels | Question it answers |
|---|---|---|
| **Model** | Each model, at a pinned version, thinking level and temperature | Which engine is strongest? |
| **Harness** | *Thin loop* (fixed prompt in, action out, no general tools) or a general agent harness (shell, files, context management) | What does the harness add over the bare model? |
| **Task adaptation** | *None* / *pre-baked skill* (human-authored task knowledge or tools injected) / *self-customization* (the agent builds its own tools, plugins or notes for the task before doing it) | Does packaged expertise help? Can the agent build that expertise itself? |

The four views people usually ask for are paths through this grid:

1. **Model**: thin loop, no adaptation. Raw capability.
2. **Harness**: general harness, no adaptation. Harness lift = (2) - (1).
3. **Harness + pre-baked skill**. Skill lift = (3) - (2).
4. **Harness + self-customization**. Self-customization lift = (4) - (2).

(3) and (4) are siblings off (2), not rungs on a ladder. Their head-to-head,
(4) vs (3), is often the most interesting result: can an agent author what a
human would have packaged, and at what cost? A thin loop with a skill (model +
skill, no harness) is a valid extra cell. Label it as such and do not count it
as level (3).

## Hold everything else constant

A delta is only valid when these match between the two cells. When one cannot
match, report it next to the number:

- Task set, seeds and difficulty strata
- Model version, thinking level, temperature
- Budgets: wall clock, tokens, and **action caps** (previews, retries, turns)
- Task interface: the same environment API or CLI for every cell
- Grader, which reads environment state only, never the agent's claims
- Isolation level, trials per seed, and infrastructure error handling

Self-customization needs an extra setup phase. Give it a separate,
disclosed time budget, and report its cost (time, tokens) as part of the
result, not as overhead.

## Choosing what to run

The full grid is too large to fill. Run the cells that support a claim:

1. **Pick anchors.** One cheap, stable anchor model and one or two anchor
   harnesses. Most cells vary one factor away from the anchors.
2. **Plus-shaped sweeps.** Run every model at one fixed harness and
   adaptation level (the model leaderboard). Run every harness with the anchor
   model (the harness leaderboard). Run every adaptation level with the anchor
   model and harnesses (the adaptation story).
3. **One interaction check.** Run a weak and a strong model across the
   adaptation levels. Whether scaffolding helps weaker models more than strong
   ones is a story either way.
4. **Fill by information gain.** Next, run a cell that completes a delta a
   headline needs, or one whose confidence interval still overlaps the claim it
   supports. A new product release adds its cells to the plus. Skip cells that
   feed no claim.
5. **Minimum evidence per cell.** At least 3 trials per seed. Report
   per-difficulty breakdowns and confidence intervals (Wilson for rates).

## Reporting: progressive disclosure

Do not put the whole matrix in front of a first-time viewer.

- **Layer 1, the headline.** One question and one chart, at most about five
  series. Good defaults: "One model, four ways to run it" (the four views
  above), or one leaderboard with every factor but one locked.
- **Layer 2, the ablation explorer.** The viewer picks the factor to vary.
  The UI locks the other factors and shows deltas with intervals. Offer
  presets for each product story ("what this harness adds", "what this skill
  adds") instead of free-form filters first.
- **Layer 3, the evidence.** The full matrix, cost and time per success,
  tokens, per-seed results, trajectories and replays, the artifacts each agent
  built, and integrity flags.

Each product category gets one story slot. A model story compares models with
the harness and adaptation fixed. A harness story fixes the model. A skill
story is a skill-lift delta. A self-customizing harness story is a
self-customization-lift delta plus its cost. Keep the default view neutral, and
put product-specific framing in presets.

## Metrics

- **Primary:** task success rate, by difficulty stratum.
- **Efficiency:** cost per success, wall time per success, tokens. Agent
  setups can cost 10-100x a thin loop, so always show cost next to success.
- **Behavior:** give-ups, loops and thrash, invalid actions; for
  self-customization, tools built and how often the agent used them.
- **Integrity:** attempts to probe the environment, rule violations, and
  infrastructure errors (kept separate from agent failures).

## Integrity checklist

Learned the hard way. Check these before trusting any new cell:

- [ ] **No answer leaks in environment responses.** Audit every field the
      environment returns. A move history that includes the scramble, a debug
      field, or a seed that maps to a public generator are all leaks. A sign of
      one: solves that match the reference answer exactly.
- [ ] **Action-budget parity.** If one setup caps previews or turns, cap the
      others the same way. Without caps, agents brute-force through
      "non-destructive" preview or undo calls, even when the prompt forbids it.
- [ ] **Isolation from the host.** Agents with a shell will read process
      tables, `/proc`, sibling trial outputs, source code and grader inputs.
      Run each trial in a sandbox or container that hides other trials, the
      runner's process, results directories and environment source.
- [ ] **Grade from state, not claims.** Agents report tool output they never
      got, or a "solved" that did not happen.
- [ ] **Separate infrastructure errors.** Rate limits and quota errors are
      not agent failures. Mark them, retry them, and keep them out of rates.
- [ ] **Disclose every parity break** (budget, isolation, version) next to
      the numbers it affects.

## Self-customization protocol

A reproducible way to measure "the harness customizes itself for the task":

1. **Scaffold phase.** Point the environment at a practice instance (a
   different seed or map). Give the agent the harness's extension docs and a
   time budget, and ask it to build and test its own tools. Forbid tools that
   solve the task outright, and enforce that with budgets rather than prompts
   alone.
2. **Restart.** Reload the harness with the agent's extensions, resume the
   same session, and swap in the live instance.
3. **Record** the scaffold source, the tools declared, each tool's call
   count, scaffold time and tokens, and whether the agent bypassed its own
   tools.
