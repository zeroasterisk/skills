# Automation Readiness Scorecard

> **Assessment Rubric based on DeepMind's *Intelligent AI Delegation* Framework (arXiv:2602.11865)**

Use this scorecard to evaluate whether a skill, workflow, or process should be automated, and to determine the required safeguards.

---

## 1. Candidate Overview

- **Unit Name**: `[e.g., automated-database-migration, pr-code-reviewer, customer-refund-processor]`
- **Target Type**: `[Skill | Workflow | Business Process | Tool]`
- **Assessor**: `[Name / Role]`
- **Date**: `[YYYY-MM-DD]`
- **Brief Description**: `[What does this unit do, what inputs does it take, and what outputs/side-effects does it produce?]`

---

## 2. 11-Axis Diagnostic Scoring

Rate each axis from **1 (Strongly favors automation / Low friction)** to **5 (Severely restricts automation / High risk)**:

| # | Axis | Score (1-5) | Notes & Evidence |
| :-: | :--- | :-: | :--- |
| **1** | **Complexity**<br>*(1 = Narrow/modular steps, 5 = Open-ended deep reasoning)* | `[ ]` | |
| **2** | **Criticality**<br>*(1 = Cosmetic/zero impact, 5 = Catastrophic blast radius / financial / legal)* | `[ ]` | |
| **3** | **Uncertainty**<br>*(1 = Deterministic inputs/env, 5 = Highly volatile / unknown edge cases)* | `[ ]` | |
| **4** | **Duration**<br>*(1 = Sub-second / stateless, 5 = Multi-day / complex state)* | `[ ]` | |
| **5** | **Cost & Budget**<br>*(1 = Negligible compute cost, 5 = Prohibitive token / verification expense)* | `[ ]` | |
| **6** | **Resource & Tooling Scope**<br>*(1 = Read-only / sandbox, 5 = Root OS / live external production systems)* | `[ ]` | |
| **7** | **Operational Constraints**<br>*(1 = Standard tolerances, 5 = Strict statutory / regulatory / SLA mandates)* | `[ ]` | |
| **8** | **Inverted Verifiability**<br>*(1 = High verifiability / automated tests, 5 = Low verifiability / subjective)* | `[ ]` | |
| **9** | **Inverted Reversibility**<br>*(1 = High reversibility / dry-run safe, 5 = Irreversible real-world side effects)* | `[ ]` | |
| **10** | **Contextuality & Privacy**<br>*(1 = Sanitized/public data, 5 = Unredacted PII / secrets / high IP value)* | `[ ]` | |
| **11** | **Subjectivity**<br>*(1 = Objective truth / binary correctness, 5 = Highly subjective / taste / brand)* | `[ ]` | |

---

## 3. Hard Gate Veto Checklist

Check all conditions that apply. Any checked hard gate will cap or override the final tier:

- [ ] **Gate 1: Contract-First Verifiability** — Task cannot be validated via automated tests, schemas, or formal checks at runtime. *(Caps at Tier 3)*
- [ ] **Gate 2: Blast Radius (High Criticality + Low Reversibility)** — Execution carries irreversible side-effects with significant financial, operational, or safety consequences. *(Caps at Tier 3 with mandatory human confirmation)*
- [ ] **Gate 3: Statutory / Safety Floor** — Workflow operates in regulated healthcare, judicial, safety-critical systems, or live financial custody. *(Mandates Tier 3 or Tier 4)*
- [ ] **Gate 4: High Context / Privacy Sensitivity** — Uses sensitive credentials, unredacted PII, or confidential IP requiring ephemeral JIT access. *(Requires JIT tokens and audit logging)*
- [ ] **Gate 5: Moral Crumple Zone / De-skilling** — Automating this task would place humans as liability sponges without real scrutiny, OR completely deplete the junior skill development pipeline. *(Requires curriculum routing or Tier 4)*

---

## 4. Final Recommendation Summary

- **Raw Readiness Index**: `[0 - 100]`
- **Assigned Automation Tier**:
  - [ ] **Tier 1: Full Autonomy** (Unattended, standing permissions)
  - [ ] **Tier 2: Autonomous + Monitoring** (Telemetry + automated verification + circuit breakers)
  - [ ] **Tier 3: HITL Checkpoints** (Draft & preview; human sign-off on irreversible actions)
  - [ ] **Tier 4: Human-Led** (AI as co-pilot only; human executes)
- **Key Decision Factors**: `[Summary of critical drivers]`
