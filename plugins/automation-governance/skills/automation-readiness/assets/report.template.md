# Automation Readiness & Governance Assessment Report

**Target:** `{{ target_name }}` (`{{ target_type }}`)  
**Evaluation Date:** `{{ assessment_date }}`  
**Assessor:** `{{ assessor }}`  
**Framework Version:** Google DeepMind Intelligent AI Delegation (arXiv:2602.11865)

---

## Executive Summary

- **Assigned Automation Tier:** **`{{ assigned_tier }}`** (`{{ tier_title }}`)
- **Readiness Score:** `{{ composite_score }}/100` (`{{ score_tier_label }}`)
- **Hard Gate Overrides Triggered:** `{{ gate_override_count }}`
- **Primary Recommendation:** `{{ primary_recommendation_summary }}`

---

## 1. 11-Axis Diagnostic Profile

```
Axis                   Score (1-5)   Risk Profile
-----------------------------------------------------------
Complexity             [{{ complexity }}]          {{ complexity_desc }}
Criticality            [{{ criticality }}]          {{ criticality_desc }}
Uncertainty            [{{ uncertainty }}]          {{ uncertainty_desc }}
Duration               [{{ duration }}]          {{ duration_desc }}
Cost                   [{{ cost }}]          {{ cost_desc }}
Resource Requirements  [{{ resources }}]          {{ resources_desc }}
Constraints            [{{ constraints }}]          {{ constraints_desc }}
Verifiability          [{{ verifiability }}]          {{ verifiability_desc }} ({{ verifiability_inv }} risk)
Reversibility          [{{ reversibility }}]          {{ reversibility_desc }} ({{ reversibility_inv }} risk)
Contextuality          [{{ contextuality }}]          {{ contextuality_desc }}
Subjectivity           [{{ subjectivity }}]          {{ subjectivity_desc }}
-----------------------------------------------------------
Composite Readiness:   {{ composite_score }}/100
```

---

## 2. Hard Gate Evaluations & Overrides

| Gate | Status | Triggered Condition & Impact |
| :--- | :--- | :--- |
| **G1: Contract-First Verifiability** | `{{ g1_status }}` | `{{ g1_rationale }}` |
| **G2: Blast Radius (Criticality × Reversibility)** | `{{ g2_status }}` | `{{ g2_rationale }}` |
| **G3: Statutory Safety Floor** | `{{ g3_status }}` | `{{ g3_rationale }}` |
| **G4: Context Sensitivity & Privacy** | `{{ g4_status }}` | `{{ g4_rationale }}` |
| **G5: Moral Crumple Zone & De-skilling** | `{{ g5_status }}` | `{{ g5_rationale }}` |

*Overrides Applied:* `{{ override_details }}`

---

## 3. Operational Guardrail Specification

### 3.1 Monitoring Protocol (§4.5)
- **Monitoring Level:** `{{ monitoring_level }}`
- **Telemetry Hooks:** `{{ telemetry_hooks }}`
- **Revocation Triggers:** `{{ revocation_triggers }}`

### 3.2 Permission & Authority Model (§4.7)
- **Permission Tier:** `{{ permission_tier }}`
- **Token Lifecycle:** `{{ token_lifecycle }}`
- **Attenuation & Boundaries:** `{{ permission_boundaries }}`

### 3.3 Verification Mechanism (§4.8)
- **Primary Mechanism:** `{{ verification_mechanism }}`
- **Acceptance Criteria:** `{{ acceptance_criteria }}`
- **Fallback / Dispute Policy:** `{{ dispute_policy }}`

### 3.4 Liability Firebreaks & Accountability (§5.2)
- **Firebreak Checkpoints:** `{{ firebreak_checkpoints }}`
- **Accountability Assignment:** `{{ accountability_assignment }}`
- **Human Oversight Requirements:** `{{ human_oversight_reqs }}`

---

## 4. Action Plan & Next Steps

1. `{{ step_1 }}`
2. `{{ step_2 }}`
3. `{{ step_3 }}`
