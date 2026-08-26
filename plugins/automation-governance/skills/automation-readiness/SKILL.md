---
name: automation-readiness
description: Evaluates whether a skill, workflow, or process should be fully automated, partially automated with human-in-the-loop (HITL) checkpoints, or kept human-led. Implements Google DeepMind's Intelligent AI Delegation framework (arXiv:2602.11865) using an 11-axis diagnostic scorecard, hard gate vetoes, autonomy tiers, and an operational guardrail matrix. Use when deciding whether to automate a process, conducting automation risk assessments, determining delegation autonomy, or configuring monitoring and verification guardrails.
license: Apache-2.0
metadata:
  version: "1.0.0"
  framework: "Google DeepMind Intelligent AI Delegation (arXiv:2602.11865)"
---

# Automation Readiness Evaluator

Evaluates candidate skills, agent tools, software workflows, or business processes to determine whether they should be fully automated, automated with human-in-the-loop (HITL) checkpoints, or retained under human control.

Based on Google DeepMind's foundational research:
> **Tomašev, Franklin, Osindero (2026)**. *Intelligent AI Delegation*. [arXiv:2602.11865](https://arxiv.org/abs/2602.11865).

---

## When to Use This Skill

- Deciding whether a new workflow, script, or agentic capability should be fully automated.
- Reviewing existing automated jobs for safety, liability, or blast radius risks.
- Determining the correct autonomy tier (Full Autonomy vs Monitored vs HITL vs Human-Led).
- Designing operational guardrails (monitoring telemetry, permission scoping, verification contracts, and liability firebreaks).
- Auditing multi-agent delegation chains against systemic failure or moral crumple zones.

---

## Progressive Disclosure & Reference Architecture

- **Theoretical Core & Taxonomy**: Read [`references/FRAMEWORK.md`](references/FRAMEWORK.md) for the 11 characterization axes, organizational dynamics, 5 pillars, 9 protocols, and protocol extensions (MCP, A2A, AP2, UCP).
- **Human Rubric / Scorecard**: [`assets/scorecard.template.md`](assets/scorecard.template.md).
- **Report Template**: [`assets/report.template.md`](assets/report.template.md).
- **Execution Script**: Run `scripts/score.py` to calculate the weighted readiness score and apply hard gate vetoes deterministically.

---

## Assessment Workflow (5-Gate Funnel)

When requested to evaluate an automatable unit of work, follow these sequential gates:

```
[Candidate Workflow]
        │
        ▼
┌──────────────────────────────────────┐
│ Gate 1: Characterize on 11 Axes      │ ──► Scores 1-5 across complexity, criticality, etc.
└──────────────────────────────────────┘
        │
        ▼
┌──────────────────────────────────────┐
│ Gate 2: Contract-First Verifiability │ ──► Can outcome be objectively tested at runtime?
└──────────────────────────────────────┘      (If NO: cap at Tier 3 or decompose)
        │
        ▼
┌──────────────────────────────────────┐
│ Gate 3: Blast Radius & Reversibility │ ──► High criticality + low reversibility?
└──────────────────────────────────────┘      (If YES: cap at Tier 3 with human sign-off)
        │
        ▼
┌──────────────────────────────────────┐
│ Gate 4: Context Sensitivity & Trust  │ ──► Sensitive PII / credentials involved?
└──────────────────────────────────────┘      (If YES: ephemeral JIT tokens + TEE sandboxing)
        │
        ▼
┌──────────────────────────────────────┐
│ Gate 5: Statutory & De-skilling Check│ ──► Regulated safety floor or junior training loss?
└──────────────────────────────────────┘      (If YES: cap at Tier 3/4 or curriculum route)
        │
        ▼
[Assigned Tier + Operational Guardrail Spec]
```

### Step 1: Elicit Workflow Details & Score the 11 Axes
Prompt the user or inspect the candidate workflow code/specification to score each axis on a scale of 1 to 5:

1. **Complexity** (1 = Simple/modular, 5 = Open-ended deep reasoning)
2. **Criticality** (1 = Cosmetic/internal, 5 = High blast radius / financial / health / legal)
3. **Uncertainty** (1 = Deterministic environment, 5 = Volatile / stochastic / ambiguous)
4. **Duration** (1 = Sub-second / stateless, 5 = Long-lived / multi-day state)
5. **Cost** (1 = Low compute/token budget, 5 = Prohibitive verification & inference cost)
6. **Resource Scope** (1 = Read-only sandbox, 5 = Production root / live mutations)
7. **Constraints** (1 = Loose tolerances, 5 = Strict SLAs / legal regulations)
8. **Verifiability** (5 = Automated unit tests/schemas, 1 = Subjective/unverifiable)
9. **Reversibility** (5 = Fully reversible/dry-run safe, 1 = Irreversible side effects)
10. **Contextuality** (1 = Public/sanitized data, 5 = Unredacted PII / confidential IP)
11. **Subjectivity** (1 = Objective ground truth, 5 = Pure aesthetic/preference)

### Step 2: Evaluate Non-Negotiable Hard Gate Overrides
Assess the 5 hard gate conditions:
- **Gate 1 (Verifiability)**: Is `verifiability <= 2` or `subjectivity >= 4`? $\rightarrow$ Caps at **Tier 3**.
- **Gate 2 (Blast Radius)**: Is `criticality >= 4` AND `reversibility <= 2`? $\rightarrow$ Caps at **Tier 3** with mandatory human confirmation.
- **Gate 3 (Safety Floor)**: Is this in healthcare, legal, safety-critical, or financial custody? $\rightarrow$ Caps at **Tier 3 or 4**.
- **Gate 4 (Privacy)**: Is `contextuality >= 4`? $\rightarrow$ Enforces Just-In-Time (JIT) ephemeral tokens.
- **Gate 5 (Moral Crumple Zone / De-skilling)**: Does this reduce human oversight to a liability sponge or destroy apprenticeship? $\rightarrow$ Caps at **Tier 4** or enforces developmental curriculum routing.

### Step 3: Run the Scoring Evaluator
Generate a temporary assessment file (YAML or JSON) and run the bundled scoring script:

```bash
python3 plugins/automation-governance/skills/automation-readiness/scripts/score.py --input assessment.yaml
```

*(Alternatively, run with `--json` for machine-readable output or `--output report.md` to save directly).*

### Step 4: Emit Structured Decision Report & Guardrail Matrix
Present the findings using the 4-tier automation model:

- **Tier 1: Full Autonomy (Unattended)** — Standing least-privilege tokens, lightweight outcome polling.
- **Tier 2: Autonomous + Process Monitoring** — Process telemetry, automated synthetic/pre-commit verification, runtime circuit breakers.
- **Tier 3: Human-in-the-Loop (HITL) Checkpoints** — 2-phase state machine (draft & simulate $\rightarrow$ pause for approval on irreversible steps).
- **Tier 4: Human-Led / Do Not Automate** — AI assists as co-pilot only; human holds execution tokens and accountability.

Include the operational guardrails:
1. **Monitoring Protocol (§4.5)**: Telemetry frequency and anomaly triggers.
2. **Permission Model (§4.7)**: Ephemeral JIT vs standing tokens, attenuation.
3. **Verification Mechanism (§4.8)**: Direct inspection, test suites, or cryptographic proofs.
4. **Liability Firebreaks (§5.2)**: Clear accountability locus and human approval gates.

---

## Examples

### Example 1: Pull Request Lint & Formatting Bot
- **Axes**: Complexity 1, Criticality 1, Uncertainty 1, Verifiability 5, Reversibility 5, Contextuality 1.
- **Result**: **Tier 1 (Full Autonomy)**.
- **Guardrails**: Standing GitHub App token with write access limited to branches; post-hoc test verification.

### Example 2: Production Database Migration Orchestrator
- **Axes**: Complexity 3, Criticality 5, Uncertainty 2, Verifiability 4, Reversibility 2, Contextuality 4.
- **Hard Gate**: Gate 2 (Blast Radius) + Gate 4 (Context Sensitivity).
- **Result**: **Tier 3 (HITL Checkpoints)**.
- **Guardrails**: Agent validates migration script on staging DB, generates dry-run diff and schema migration plan, pauses for DBA sign-off before obtaining ephemeral JIT credentials for production run.

### Example 3: Clinical Diagnostic Treatment Recommender
- **Axes**: Complexity 5, Criticality 5, Uncertainty 4, Verifiability 2, Reversibility 1, Contextuality 5.
- **Hard Gate**: Gate 1 (Low Verifiability) + Gate 2 (Blast Radius) + Gate 3 (Statutory Safety Floor).
- **Result**: **Tier 4 (Human-Led / Do Not Automate)**.
- **Guardrails**: AI provides differential diagnosis references and literature citations; physician retains sole decision and prescribing authority.
