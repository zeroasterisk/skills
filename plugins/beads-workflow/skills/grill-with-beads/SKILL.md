---
name: grill-with-beads
description: Grilling session that challenges your plan, sharpens the work breakdown, and updates the beads (bd) issue tracker inline as decisions crystallise. Use when you want to stress-test a plan and translate it directly into actionable, tracked bd tasks and dependencies.
license: Apache-2.0
metadata:
  version: "1.0.0"
---

<what-to-do>

Interview me relentlessly about every aspect of this plan until we reach a shared understanding and a concrete work breakdown. Walk down each branch of the design tree, resolving dependencies between decisions one-by-one. For each question, provide your recommended answer.

Ask the questions one at a time, waiting for feedback on each question before continuing.

As decisions are made and tasks are identified, proactively use the `bd` CLI to create and link issues in real-time.

</what-to-do>

<supporting-info>

## Beads Issue Tracking Integration

During the grilling session, you should be actively looking for opportunities to break the plan down into `bd` issues:

1. **Identify Epics:** If the plan represents a large feature, propose creating a parent Epic issue using `bd`.
2. **Breakdown Tasks:** As we resolve specific branches of the design tree, propose and create granular implementation tasks.
3. **Establish Dependencies:** When a design decision mandates that X must happen before Y, enforce this by linking the tasks:
   - Use `bd dep <blocked-task-id> --blocks <blocker-epic-id>` to map tasks to their epics.
   - Use `bd dep` to ensure execution order is strictly tracked.
4. **Contextualize:** Ensure that the description of each generated `bd` issue captures the "why" that we discussed during the grilling phase, acting as mini-ADRs within the task itself.

If we need to know what's currently in flight or what Epics already exist, use `bd ready` or explore the local `.beads` / dolt database using the CLI.

</supporting-info>
