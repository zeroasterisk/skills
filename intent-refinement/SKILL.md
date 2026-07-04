---
name: intent-refinement
description: Identify, draft, validate, and refine product intent and plan specifications using Narrative-Driven Development (NDD) taxonomy. Use when designing new features, refining requirements, or preparing specs for AI agents.
---

# Skill: Intent Refinement (NDD)

Identify, draft, validate, and refine product intent and plan specifications using Narrative-Driven Development (NDD) taxonomy.

## Description

This skill enables the agent to collaborate with humans to define robust, regression-resistant specifications. By modeling software as a structured "product story" (Domain -> Narrative -> Scene -> Moment) with explicit rules and examples, we ensure the AI agent builds the right thing and doesn't lose intent during iteration.

## Prompt Triggers & Slash Commands

-   `/refine-intent` (Slash command)
-   "Help me design a new feature..."
-   "Refine the requirements for..."
-   "Draft a spec for..."
-   "Let's align on the behavior of..."

## Instructions

### 1. Structure the Intent (Taxonomy)

When asked to design or refine a feature, guide the user to structure their intent into the NDD hierarchy:

*   **Domain**: Define the broad capability area.
*   **Narrative**: Define the specific user goal.
*   **Scene**: Define the outcomes (what becomes true, *not* the screens).
*   **Moment**: Define the interaction slices. Classify each as:
    *   `Command`: Writes/changes state.
    *   `Query`: Reads/inspects state.
    *   `React`: System reacts automatically.
    *   `Experience`: User navigation/UI flow.

### 2. Define Rules and Examples

For every `Command` and `React` moment, you MUST define:
*   **Business Rules**: What must always hold true.
*   **Examples**: Concrete scenarios proving the rule using `Given/When/Then`.

### 3. Validate Cohesion

Ensure the specification is cohesive:
*   **Data Completeness**: Every piece of data shown in a `Query` must have a source (created/modified in a `Command` or `React`).
*   **Read/Write Balance**: If a narrative has `Commands`, it should usually have `Queries` to view the result.

### 4. Refine First, Code Second

If the user requests a change to an existing system or a draft:
1.  Update the NDD specification file *first*.
2.  Validate the updated specification: check that every Command has at least one rule with an example, and every Query's data sources trace to Commands/Reacts.
3.  Only proceed to generating code or plans once the specification is aligned and valid.

### 5. When to Stop Refining

The spec is ready for implementation when:
- Every `Command` has at least one business rule with a concrete example
- Every `Query`'s data sources trace to `Commands` or `Reacts`
- At least one edge case or failure scenario is documented per narrative
- The user has reviewed and confirmed the specification

Don't over-refine. A spec with clear rules and examples is better than a spec with exhaustive coverage of unlikely scenarios.

## Specification Format (YAML or JSON)

Recommend the user to keep specifications in this format:

```yaml
domain: <Domain Name>
description: <Description>
narratives:
  - name: <Narrative Name>
    goal: <Goal>
    scenes:
      - name: <Scene Name (Outcome)>
        outcome: <Outcome Description>
        moments:
          - name: <Moment Name>
            type: <Command|Query|React|Experience>
            description: <Description>
            rules:
              - text: <Rule Description>
                examples:
                  - name: <Example Name>
                    given: <Context>
                    when: <Action>
                    then: <Expected Result>
```
