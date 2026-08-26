# Intelligent AI Delegation Framework

> **Reference Documentation for Automation Readiness & Delegation Analysis**  
> Based on: *Intelligent AI Delegation* (Nenad Tomašev, Matija Franklin, Simon Osindero — Google DeepMind, Feb 2026). [arXiv:2602.11865](https://arxiv.org/abs/2602.11865). CC BY 4.0.

---

## 1. Overview & Core Philosophy

As AI agents evolve from static query-response assistants to autonomous systems operating across workflows, task delegation can no longer rely on simplistic heuristics or naive parallelization. 

**Intelligent Delegation** is defined as:
> *A sequence of decisions involving task allocation that incorporates the transfer of authority, responsibility, and accountability, clear specifications regarding roles and boundaries, clarity of intent, and mechanisms for establishing trust between delegator and delegatee.*

The framework moves beyond the question *"Can AI do this?"* to answer:
1. **Should** this skill, workflow, or process be automated?
2. Under what **autonomy tier**?
3. With which **operational guardrails** (monitoring, permissions, verification, and liability firebreaks)?

---

## 2. The 11 Task Characterization Axes

Every candidate unit of work (task, workflow, or sub-skill) is scored across 11 fundamental diagnostic axes:

| Axis | Definition | Low-Risk Profile (Favors Automation) | High-Risk Profile (Restricts Autonomy) |
| :--- | :--- | :--- | :--- |
| **1. Complexity** | Difficulty, number of sub-steps, reasoning depth. | Narrow, modular, well-bounded steps. | Open-ended, multi-layered reasoning chains. |
| **2. Criticality** | Severity of consequences upon failure or suboptimal execution. | Cosmetic, non-business-critical, low blast radius. | Financial loss, safety hazard, legal/compliance violation. |
| **3. Uncertainty** | Ambiguity of environment, dynamic inputs, stochastic outcomes. | Deterministic inputs, stable static environment. | Volatile data, ambiguous requirements, unknown edge cases. |
| **4. Duration** | Execution timeframe. | Milliseconds to minutes (short-lived). | Hours to weeks (long-running stateful workflows). |
| **5. Cost** | Economic/compute budget (tokens, API fees, energy). | Negligible marginal cost per run. | Expensive model calls, high verification overhead. |
| **6. Resource Reqs** | System privileges, external tools, APIs, human dependencies. | Standard read-only tools, self-contained dependencies. | Root access, private DBs, real-world actuators, human blockers. |
| **7. Constraints** | Operational, legal, compliance, or safety boundaries. | Standard operational limits. | Strict SLAs, statutory regulations (HIPAA, GDPR, SOX). |
| **8. Verifiability** | Cost and feasibility of validating execution correctness. | **High**: Binary, automated checks (tests, schemas, proofs). | **Low**: Subjective, qualitative, labor-intensive review. |
| **9. Reversibility** | Ease of undoing execution effects in the real world. | **High**: In-memory state, drafts, dry-runs, git commits. | **Low**: Financial trades, DB drops, outbound emails, external API mutations. |
| **10. Contextuality** | Volume and sensitivity of private/proprietary state required. | Context-free, sanitized, public data. | PII, financial credentials, trade secrets, confidential IP. |
| **11. Subjectivity** | Extent to which success is aesthetic/preferential vs objective. | Objective ground truth, mathematical/code correctness. | Brand voice, visual aesthetics, strategic judgment. |

---

## 3. Human Organizational Dynamics Applied to AI

The framework draws on organizational economics and safety-critical engineering:

- **The Principal-Agent Problem**: Delegatees (AI agents) may exhibit reward hacking, sycophancy, or misalignment with user intent when given open-ended objectives.
- **Span of Control**: Bounded limits on how many sub-agents or sub-tasks a single orchestrator (or human supervisor) can reliably manage without cognitive overload or failure cascades.
- **Authority Gradient**: Communication barriers caused by perceived hierarchy. Agents must have calibrated assertiveness—avoiding sycophancy by challenging ambiguous/flawed prompts while respecting valid overrides.
- **Zone of Indifference**: The danger where delegatees blindly execute instructions without moral/contextual scrutiny. Intelligent systems require *dynamic cognitive friction* to pause and ask for confirmation when requests are technically permissible but contextually high-risk.
- **Trust Calibration**: Aligning autonomy strictly with empirical competence. High general reputation does not equal contextual trust in high-stakes domains.
- **Transaction Cost Economics**: Balancing the cost/latency of verification and negotiation against the risk of unverified delegation.
- **Contingency Theory**: No static delegation model fits all cases; structure and oversight must dynamically adapt to evolving environmental conditions.

---

## 4. The 5 Pillars & Technical Protocols

```
┌────────────────────────────────────────────────────────────────────────┐
│                      Intelligent AI Delegation                         │
├──────────────────┬───────────────────┬──────────────────┬──────────────┤
│ Dynamic          │ Adaptive          │ Structural       │ Systemic     │
│ Assessment       │ Execution         │ Transparency     │ Resilience   │
├──────────────────┼───────────────────┼──────────────────┼──────────────┤
│ • Decomposition  │ • Adaptive Coord  │ • Monitoring     │ • Security   │
│ • Assignment     │ • Re-delegation   │ • Verifiability  │ • Permission │
│ • Optimization   │ • Escalation      │ • Audit Trails   │   Handling   │
└──────────────────┴───────────────────┴──────────────────┴──────────────┘
```

1. **Task Decomposition (§4.1)**: Enforces *contract-first decomposition*. If an objective is too subjective or costly to verify, it must be recursively decomposed until sub-tasks match automated verification primitives (unit tests, schemas, formal checks).
2. **Task Assignment (§4.2)**: Decentralized capability and reputation matching, interactive parameter negotiation, and formalization of expectations.
3. **Multi-objective Optimization (§4.3)**: Pareto navigation across speed, cost, quality, privacy, and certainty. Accounts for delegation overhead below which direct execution is favored.
4. **Adaptive Coordination (§4.4)**: Real-time re-delegation upon SLO degradation, external resource outages, or intermediate check failures.
5. **Monitoring (§4.5)**: 5-axis observability taxonomy (Outcome vs Process, Indirect vs Direct, Black-box vs White-box, Full Transparency vs Cryptographic, Direct vs Transitive).
6. **Trust & Reputation (§4.6)**: Graduated authority where trust dictates autonomy caps and monitoring intensity.
7. **Permission Handling (§4.7)**: Standing permissions for low-stakes; just-in-time (JIT), least-privilege, attenuated tokens with algorithmic circuit breakers for high-stakes.
8. **Verifiable Task Completion (§4.8)**: 4 verification mechanisms (Direct Inspection, Third-Party Audit, Cryptographic Proofs, Game-Theoretic Consensus) tied to escrow and non-transitive liability chains.
9. **Security (§4.9)**: Defense-in-depth against prompt injection, model extraction, data poisoning, and cognitive monoculture across multi-agent networks.

---

## 5. Automation Readiness Tiers

Based on the diagnostic score and hard gate assessments, workflows map into one of 4 operational tiers:

```
┌────────────────────────────────────────────────────────────────────────┐
│                        Automation Readiness Tiers                      │
├──────────────┬────────────────────────┬────────────────────────────────┤
│ Tier         │ Name                   │ Description & Authority Level  │
├──────────────┼────────────────────────┼────────────────────────────────┤
│ **Tier 1**   │ **Full Autonomy**      │ Unattended execution. Standing │
│              │                        │ permissions, outcome-only      │
│              │                        │ lightweight monitoring.        │
├──────────────┼────────────────────────┼────────────────────────────────┤
│ **Tier 2**   │ **Autonomous +         │ Unattended execution with      │
│              │ Monitoring**           │ automated verification checks, │
│              │                        │ process telemetry, and runtime │
│              │                        │ circuit breakers.              │
├──────────────┼────────────────────────┼────────────────────────────────┤
│ **Tier 3**   │ **Human-in-the-Loop    │ Agent drafts/executes safe     │
│              │ (HITL) Checkpoints**   │ parts; pauses at irreversible  │
│              │                        │ or critical milestones for     │
│              │                        │ explicit human approval.       │
├──────────────┼────────────────────────┼────────────────────────────────┤
│ **Tier 4**   │ **Human-Led / Do Not   │ Workflow must remain human-    │
│              │ Automate**             │ driven. AI provides assist/ref │
│              │                        │ only; human holds execution.   │
└──────────────┴────────────────────────┴────────────────────────────────┘
```

---

## 6. Hard Gate Override Rules (Veto Criteria)

Even if a workflow achieves a high overall composite score, any single hard gate violation caps or down-tiers the permissible autonomy:

1. **Gate 1: Contract-First Verifiability Gate**
   - *Rule*: If `Verifiability == Low` AND `Subjectivity == High` (cannot be tested or formally validated at runtime), the workflow **CANNOT** be Tier 1 or Tier 2.
   - *Action*: Down-tier to **Tier 3 (HITL)** or recursively decompose into verifiable sub-components.

2. **Gate 2: Blast Radius Gate (Criticality × Reversibility)**
   - *Rule*: If `Criticality == High` AND `Reversibility == Low` (e.g., executing financial transactions, dropping databases, issuing irreversible public actions), the workflow is capped at **Tier 3 (HITL)**.
   - *Requirement*: Mandatory explicit human confirmation before executing any irreversible action.

3. **Gate 3: Statutory & Safety Floor Gate**
   - *Rule*: Regulated domains (healthcare diagnostics, judicial/legal determination, safety-critical infrastructure, live financial custody) have mandatory, non-bypassable safety floors.
   - *Requirement*: Capped at **Tier 3 or Tier 4** regardless of speed/cost incentives.

4. **Gate 4: Context Sensitivity & Privacy Gate**
   - *Rule*: If `Contextuality == High` (handling unredacted PII, credentials, or proprietary IP), standing credentials are prohibited.
   - *Requirement*: Requires Just-In-Time (JIT) ephemeral token scoping and cryptographic/sandboxed execution.

5. **Gate 5: Moral Crumple Zone & De-skilling Gate**
   - *Moral Crumple Zone*: Never place a human in the loop *solely* to absorb legal liability if they lack the time, telemetry, or cognitive capacity to inspect the trace.
   - *Apprenticeship & De-skilling*: If automating this task completely eliminates the developmental pipeline for junior practitioners, preserve human execution on representative subsets (curriculum routing).

---

## 7. The Operational Guardrail Matrix

When an automation tier is assigned, the skill generates specifications across 4 operational dimensions:

| Dimension | Tier 1 (Full) | Tier 2 (Autonomous + Monitored) | Tier 3 (HITL Checkpoints) | Tier 4 (Human-Led) |
| :--- | :--- | :--- | :--- | :--- |
| **Monitoring** | Lightweight outcome polling; log success/error codes. | Process-level telemetry; event streaming (`CHECKPOINT_REACHED`), intermediate state validation. | Synchronous pause on state machine; human-readable diff / rationale presentation. | Continuous user interactive console; AI acts as passive co-pilot. |
| **Permissions** | Standing pre-approved tokens for least-privilege toolset. | Attenuated capability tokens; automated circuit breaker on anomaly detection. | Ephemeral Just-In-Time (JIT) scoped tokens granted only upon human click/approval. | No autonomous execution tokens; credentials remain in human custody. |
| **Verification** | Automated post-hoc checks (exit status, schema check). | Pre-commit automated unit test suites, static analysis, synthetic golden tests. | Dual-verification: automated validation + human sign-off on change manifest. | Human cognitive review and domain expertise. |
| **Liability & Firebreaks** | System owner absorbs standard operational variance. | Non-transitive sub-agent contract bounds; automatic rollback on test failure. | Explicit **Liability Firebreak**: user approval transfers responsibility to human sign-off. | Human principal holds full end-to-end accountability. |

---

## 8. Protocol Integration Landscape

The framework bridges to contemporary AI communication and tool protocols:

- **Model Context Protocol (MCP)**: Standardizes tool invocation. Needs extensions for semantic permission attenuation (read-only scopes vs binary tool access) and streaming process telemetry (SSE events).
- **Agent-to-Agent Protocol (A2A)**: Provides agent discovery and capability cards. Needs `verification_policy` handshakes so agents pre-commit to verification evidence before accepting delegated tasks.
- **Agent Payments Protocol (AP2)**: Provides cryptographically signed mandates and escrow for liability firebreaks.
- **Universal Commerce Protocol (UCP)**: Provides verifiable multi-party settlement for outsourced sub-tasks.

---

## 9. Citation

If using or referencing this governance framework, cite:

```bibtex
@article{tomasev2026intelligent,
  title={Intelligent AI Delegation},
  author={Toma{\v{s}}ev, Nenad and Franklin, Matija and Osindero, Simon},
  journal={arXiv preprint arXiv:2602.11865},
  year={2026},
  url={https://arxiv.org/abs/2602.11865}
}
```
