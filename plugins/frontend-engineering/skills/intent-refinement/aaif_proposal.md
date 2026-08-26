# Proposal: Donating Narrative-Driven Development (NDD) to AAIF

**To**: Agentic AI Foundation (AAIF)
**From**: Alan Blount (zeroasterisk)
**Subject**: Proposal for Open Standard: Narrative-Driven Development (NDD)
**Date**: June 26, 2026

## Executive Summary

We propose the donation of **Narrative-Driven Development (NDD)**, a specification dialect and modeling method, to the Agentic AI Foundation (AAIF) to be established as an open standard.

NDD addresses a critical failure mode in current AI-assisted software development: **the loss of product intent during iteration**. By defining a structured, human-readable, and machine-validatable taxonomy for software behavior, NDD ensures that AI agents and human collaborators remain aligned throughout the software lifecycle.

## The Problem: Intent Decay in Agentic Workflows

In typical prompt-to-code or chat-based development, product intent is ephemeral. It starts as a prompt, but as the user iterates and corrects the AI, the "source of truth" becomes scattered across:
1.  Buried chat messages.
2.  Ad-hoc corrections.
3.  Implicit assumptions in the generated code.

This leads to regression, where subsequent prompts cause the AI to forget previously established rules, leading to a cycle of "one step forward, two steps back."

## The Solution: Narrative-Driven Development (NDD)

NDD introduces a middle layer between the prompt and the code: a **durable product story**.

```
[Prompt] ──> [NDD Specification (Model)] ──> [Human Review] ──> [AI Build]
                   │
                   └─── (Iterative Refinement occurs here first)
```

By forcing the model to be updated *before* the code is generated, NDD preserves intent.

### Core Contributions of NDD:
1.  **Strict Taxonomy**: Domain -> Narrative -> Scene -> Moment.
2.  **Moment Typing**: Classifying interactions (Command, Query, React, Experience) to guide AI implementation.
3.  **Cohesive Rules & Examples**: Linking business rules directly to moments and proving them with concrete `Given/When/Then` examples.
4.  **Data Completeness**: A principle ensuring all displayed information has a defined source, preventing "hallucinated" UI data.

## Why AAIF?

The Agentic AI Foundation is the ideal home for NDD. As an open standard under AAIF, NDD can:
-   **Foster Interoperability**: Enable different AI agents to understand the same specification format.
-   **Encourage Tooling**: Spurr the creation of open-source validators, visualizers, and code-generators based on NDD.
-   **Establish Best Practices**: Define how humans and AI should collaborate on software design.

## Proposed Action Plan

1.  **Form a Working Group**: Establish an AAIF working group to refine the NDD specification.
2.  **Publish Schema**: Publish official JSON/YAML schemas for NDD.
3.  **Open Source Reference Tooling**: Donate basic validation and visualization tools (like the ones initiated in this workspace).
4.  **Community Feedback**: Gather input from other AAIF members and the broader AI development community.
