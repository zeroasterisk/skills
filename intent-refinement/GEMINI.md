# Intent Refinement (NDD) for Gemini

You have access to the Intent Refinement skill using Narrative-Driven Development (NDD). Use it to collaborate with humans to define robust, regression-resistant specifications before writing code.

## When to Use

**Always refine and validate intent before starting implementation or when requirements change.**

Triggers:
- Designing a new feature or system
- Refining requirements for an existing system
- Preparing a specification for an AI agent to build
- When a user uses the `/refine-intent` slash command

## The NDD Taxonomy

Structure all specifications into a strict four-layer hierarchy:
1. **Domain**: The high-level capability area (e.g., "Manage Deals").
2. **Narrative**: A specific user goal within the domain (e.g., "Sales rep follows up on opportunities").
3. **Scene**: A self-contained outcome that becomes true (e.g., "Follow-up remains visible").
4. **Moment**: A single behavior slice. Must be typed as `Command`, `Query`, `React`, or `Experience`.

## Rules & Examples

For every `Command` (write/state change) and `React` (system side-effect), you MUST define:
- **Business Rules**: Constraints that must always hold true.
- **Examples**: Concrete scenarios proving the rule using `Given/When/Then`.

## Cohesion & Data Completeness

- **Data Completeness**: Every piece of data shown in a `Query` must have a source (created/modified in a `Command` or `React`).
- **Read/Write Balance**: If a narrative has `Commands`, it should usually have `Queries` to view the result.

## How to Validate

```bash
python skills/intent-refinement/validate.py path/to/spec.yaml
# Also supports .json files
```

See `skills/intent-refinement/SKILL.md` for detailed documentation.
