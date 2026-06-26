# Narrative-Driven Development (NDD) Specification
Version: 0.1.0-draft
Status: Proposal for AAIF

## Abstract
Narrative-Driven Development (NDD) is a specification dialect and modeling method designed for Agentic AI workflows. It establishes a durable "product story" that humans and AI agents can review, align on, and build from, preventing the loss of intent common in chat-based development.

## 1. Core Taxonomy

NDD models software intent using a strict four-layer hierarchy:

```
Domain
  └── Narrative
        └── Scene
              └── Moment
```

### 1.1 Domain
*   **Definition**: A high-level business capability or subject area.
*   **Attributes**:
    *   `name`: Unique identifier.
    *   `description`: Brief explanation of the capability.

### 1.2 Narrative
*   **Definition**: A user or business goal within a Domain.
*   **Attributes**:
    *   `name`: Unique identifier.
    *   `goal`: The desired outcome or value.
    *   `actors`: The personas involved.

### 1.3 Scene
*   **Definition**: A self-contained state or outcome that becomes true. Named for the *outcome*, not the screen.
*   **Attributes**:
    *   `name`: Unique identifier (e.g., "Tickets Reserved", "Deal Won").
    *   `outcome`: Description of the state change.

### 1.4 Moment
*   **Definition**: A single step or behavior slice that moves the scene forward.
*   **Attributes**:
    *   `name`: Unique identifier.
    *   `type`: One of `Command`, `Query`, `React`, `Experience`.
    *   `description`: What happens in this moment.
    *   `rules`: List of Business or Interaction Rules.
    *   `data`: (Optional) Data inputs/outputs (for Data Completeness).

## 2. Moment Types

*   **Command**: An action that changes the system state (Write).
*   **Query**: An action that retrieves or inspects state (Read).
*   **React**: An automatic system response to an event (Side-effect).
*   **Experience**: A user transition or navigation step.

## 3. Rules and Examples

### 3.1 Business Rule
A constraint or requirement that must always hold true for a Moment.

### 3.2 Example (Scenario)
A concrete test case proving a Business Rule, using the `Given-When-Then` format.

```yaml
rule: "Tickets cannot be reserved beyond capacity"
examples:
  - name: "Reject reservation when capacity exceeded"
    given: "1 ticket remains"
    when: "User attempts to book 2 tickets"
    then: "Booking is rejected"
```

## 4. Schema Definition (YAML)

NDD documents should be validated against the following structure:

```yaml
domain: CRM
description: Customer Relationship Management
narratives:
  - name: "Sales rep follows up on active opportunities"
    goal: "Ensure reps don't lose track of follow-ups"
    scenes:
      - name: "Follow-up remains visible while deal stages change"
        outcome: "Follow-ups are preserved across stage transitions"
        moments:
          - name: "Rep advances deal stage"
            type: Command
            description: "Rep changes the stage of a deal"
            rules:
              - text: "Stage changes must not remove active follow-up reminders."
                examples:
                  - name: "Reminder survives stage advancement"
                    given: "A deal has stage 'Discovery' and an active follow-up reminder for tomorrow"
                    when: "The rep changes the deal stage to 'Proposal'"
                    then: "The deal stage is 'Proposal' and the follow-up reminder remains active"
```
