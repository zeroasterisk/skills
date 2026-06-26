# Intent Refinement (Narrative-Driven Development)

A skill and tooling for drafting, validating, and refining product intent and plan specifications using **Narrative-Driven Development (NDD)**.

This approach ensures that product intent is preserved in a durable "product story" rather than getting lost in chat history during iterative development with AI agents.

## Inspiration & Sources

This skill is heavily inspired by and based on:
-   **Narrative-Driven Development (NDD)**: [narrativedriven.org](https://narrativedriven.org/) - An open taxonomy for preserving product intent.
-   **Auto**: [on.auto](https://on.auto/) - A product modeling platform that implements NDD.
-   **Spec-Driven Movement**: [specdriven.com](https://specdriven.com/) - The broader movement of specifying software intent clearly.

## Taxonomy

NDD structures software intent into four layers:

1.  **Domain**: The high-level capability area (e.g., "Manage Deals").
2.  **Narrative**: A specific user goal within the domain (e.g., "Sales rep follows up on opportunities").
3.  **Scene**: A self-contained outcome that becomes true (e.g., "Follow-up remains visible").
4.  **Moment**: A single behavior slice (Command, Query, React, Experience).

## Contents

-   [SKILL.md](./SKILL.md): The primary agent-facing skill instructions (used by `agy`, `jetski`, and `OpenClaw`).
-   [specification.md](./specification.md): The draft open standard specification for NDD.
-   [validate.py](./validate.py): A CLI tool to validate NDD YAML and JSON specifications.
-   [aaif_proposal.md](./aaif_proposal.md): A proposal to donate NDD as an open standard to the Agentic AI Foundation (AAIF).
-   [examples/](./examples/): Example NDD specification files.
-   [GEMINI.md](./GEMINI.md) & [gemini-extension.json](./gemini-extension.json): Legacy Gemini CLI definitions (Deprecated).

## Usage

### Antigravity (`agy`) & Jetski

`agy` (Antigravity - external) and `jetski` (internal) automatically discover this skill when placed in your customization root (`~/.gemini/config/skills/intent-refinement/` or `.agents/skills/intent-refinement/`).

Once installed, you can trigger intent refinement instantly via the slash command:
```
/refine-intent
```

### Validating a Specification

You can validate an NDD specification file (YAML or JSON) using the provided Python script:

```bash
python3 validate.py examples/valid_crm.yaml
```

You can also pass JSON files or pipe content directly via stdin:
```bash
cat examples/valid_crm.yaml | python3 validate.py
```

The validator checks:
-   Strict hierarchical structure.
-   Valid moment types (`Command`, `Query`, `React`, `Experience`).
-   Presence of rules and examples (Given/When/Then) for state-changing moments.
-   **Cohesion**: Warns if you have Commands (state changes) but no Queries (ways to read the state) in a narrative.
