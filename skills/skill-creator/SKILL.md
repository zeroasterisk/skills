# Skill Creator: How to Build AI Agent Skills

This guide explains how to create, evaluate, and iteratively improve skills for AI agents. 

## What Skills Are

Agent skills are **opinionated cheatsheets**. They encode what the agent gets wrong without help — the gotchas, the exact commands, the conditional logic, and the "do this, not that" decisions that turn an unreliable agent into a reliable one.

A skill's value is the delta between the agent with the skill and the agent without it. If the agent already handles a task well, a skill adds noise without value. If the agent consistently fails without specific guidance, that guidance is the skill.

Skills are **NOT**:
*   **Documentation or tutorials** — leave explanatory text to general wikis or docs.
*   **Libraries or CLIs** — these belong in code repositories.
*   **One-off scripts** — the agent can write these itself.

**Create a skill when** the agent fails reliably without one, the workflow recurs, and consistency matters. **Don't create one** for one-off tasks, things the agent already handles well, or workflows that change weekly.

---

## Principles

These principles guide skill design decisions. They help you *think* about skill quality, not just follow a checklist.

### 1. Experience Before Theory
Try the task before writing the skill. Run the prompts yourself, without any skill loaded, and observe where the agent fails. The gotchas you discover by failing are the skill's core content.

*Speculation about what might go wrong produces noise. Experience with what does go wrong produces signal.*

### 2. Explain the "Why"
Models comply better with understood intent than with rigid directives. When you explain *why* an instruction exists, the model generalizes to edge cases the instruction doesn't literally cover.

*   ❌ *Always use tool X instead of tool Y.*
*   ✅ *Use tool X instead of tool Y — tool X has faster startup and is designed for ad-hoc queries, while tool Y is for administrative operations.*

If you find yourself writing ALWAYS or NEVER in caps, pause. Can you explain *why* instead?

### 3. Signal, Not Noise
Every line must earn its place. The context window is shared with the system prompt, conversation history, other skills, and user requests.

**Keep (Signal):**
*   Gotchas from real failure modes.
*   Exact command patterns with concrete placeholder values.
*   Flag/argument documentation with conditional requirements.
*   Domain-specific business logic and workflow branching.
*   Anti-patterns the agent defaults to without warning.

**Remove (Noise):**
*   Boilerplate the agent already knows ("always validate output").
*   Verbose explanations of concepts the model understands from training.
*   Redundant restatements of the same instruction.
*   Generic advice that applies to any CLI ("read the docs first").

### 4. One Job Well
Each skill should do one job. If describing a skill requires "and" between unrelated capabilities, split it into separate skills. Broad skills trigger unreliably because the description cannot be specific enough to match diverse user intents.

### 5. Generalize, Don't Overfit
You will test on a handful of cases, but the skill will run on thousands of diverse prompts. After each improvement, ask: *"Would this help on a prompt I haven't seen, or did I just add a narrow fix for my specific test case?"*

Watch for:
*   Fiddly changes that address one specific test failure.
*   Instructions phrased in terms of your test data rather than the general case.
*   Growing lists of special cases instead of general rules.

### 6. Verify, Don't Trust
Every instruction should be verifiable. If the agent cannot test whether it followed the instruction correctly, the instruction is too vague. Include runnable validation commands, expected outputs, or concrete success criteria.

---

## The Lifecycle

Creating a skill is an iterative development process, not a one-shot writing task.

### Phase 1: Understand
1.  **Check for duplicates:** Search if a relevant skill already exists or can be expanded.
2.  **Collect prompts:** Gather 3–15 example prompts or use cases. If capturing a workflow from a past conversation, extract the tools used, the sequence of steps, and the corrections made.
3.  **Define success criteria:** What should be true when the agent finishes? These criteria become your evaluation expectations.

### Phase 2: Experience
Try to solve the prompts *without* the skill loaded. Explore broadly:
*   **Failures and wrong turns:** What did you try that didn't work? (Gotchas)
*   **Missing information:** What did you wish you knew? (Domain knowledge)
*   **Default mistakes:** What does the agent do by default that is wrong? ("Do this, not that")
*   **Tool capabilities:** Run `--help` on every CLI involved. Discover flags, subcommands, and output formats.
*   **Fallback paths:** What if the primary approach fails? (Alternative tools or workarounds)

### Phase 3: Draft
1.  **Initialize the directory:** Create a folder named `my_skill/` containing a `SKILL.md` file.
2.  **Write the description first:** The description determines whether the skill triggers. See [The Description](#the-description) below.
3.  **Write the body:** Imperative form ("Run the validator", not "You should run"), concrete input/output examples, and clear placeholders like `{variable_name}`.
4.  **Use a `references/` subdirectory:** Move deep content (schemas, API tables, long cheatsheets) to separate files in a `references/` folder and link them from `SKILL.md`.

### Phase 4: Evaluate & Improve
1.  **Run the agent** against your test prompts with and without the skill.
2.  **Compare the results:** Did the skill improve the success rate or quality?
3.  **Diagnose failures:**
    *   *Agent ignores the skill:* The description is too weak to trigger it.
    *   *Agent reads the skill but fails:* The instructions are unclear, wrong, or the agent got stuck on an unhandled edge case.
4.  **Iterate:** Refine the instructions, explain the "why" better, or add fallback paths. Expect 2–4 iterations.

---

## The Description

The `name` and `description` in the skill's YAML frontmatter are the **only** things the agent sees before deciding whether to load a skill. A weak description means the skill never fires.

### Rules for Descriptions
1.  **Start with a capability statement** in the third person: *"Processes Excel files and generates reports"* — not *"I can help you"* or *"You can use this to."*
2.  **Describe the user's problem, not the tool:** Frame it around what the user is trying to accomplish.
3.  **List concrete triggers:** Add *"Use when..."* followed by specific scenarios.
4.  **Add negative triggers:** Include *"Don't use for..."* to help the agent disambiguate.
5.  **Keep it concise:** Under 1000 characters.

### Example

```yaml
---
name: pdf-processing
description: >-
  Extracts text, tables, and metadata from PDF documents, and performs merges or splits.
  Use when the user wants to parse PDF contents, convert PDFs to text/markdown, extract tables,
  or combine multiple PDF files.
  Don't use for editing PDF layout, OCR on scanned images (use OCR skill), or generating PDFs from scratch.
---
```
