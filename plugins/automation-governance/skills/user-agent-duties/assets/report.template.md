# W3C User Agent Fiduciary Assessment Report

**Target Agent:** `{{ target_name }}` (`{{ classification }}`)  
**Evaluation Date:** `{{ assessment_date }}`  
**Assessor:** `{{ assessor }}`  
**Specification Source:** [W3C User Agents Group Note](https://www.w3.org/TR/user-agents/) (`{{ spec_version_url }}`)  
**Live Spec Check Status:** `{{ spec_check_status }}`

---

## Executive Summary

- **Assigned Fiduciary Tier:** **`{{ final_tier }}`** (`{{ tier_title }}`)
- **Fiduciary Alignment Index:** `{{ fiduciary_index }}/100` (Baseline: `{{ baseline_tier }}`)
- **Duty Sub-Scores:**
  - **§ 3.1 Protection:** `{{ protection_index }}/100` (`{{ protection_avg }}/5.0`)
  - **§ 3.2 Honesty:** `{{ honesty_index }}/100` (`{{ honesty_avg }}/5.0`)
  - **§ 3.3 Loyalty:** `{{ loyalty_index }}/100` (`{{ loyalty_avg }}/5.0`)
- **Fiduciary Hard Gate Overrides Triggered:** `{{ gate_override_count }}`
- **Core Verdict:** `{{ tier_description }}`

---

## 1. 12-Axis W3C Fiduciary Duty Profile

```
Duty & Axis                                        Score (1-5)   Weight
-----------------------------------------------------------------------
[3.1 Protection — 40%]
  P1. Safe Browsing & Sandboxing                      [{{ p1 }}]          10%
  P2. Data Minimization & Anti-Tracking               [{{ p2 }}]          10%
  P3. Granular Informed Consent                       [{{ p3 }}]          10%
  P4. Local File & Origin Isolation                   [{{ p4 }}]          10%

[3.2 Honesty — 30%]
  H1. Action & Consequence Visibility                 [{{ h1 }}]          10%
  H2. Source & Transformation Provenance              [{{ h2 }}]           8%
  H3. Active Truthfulness & Indicators                [{{ h3 }}]           6%
  H4. Honest Defaults & Tradeoff Disclosure           [{{ h4 }}]           6%

[3.3 Loyalty — 30%]
  L1. User Primacy Over Third Parties                 [{{ l1 }}]          10%
  L2. Scoped & Reversible Commitments                 [{{ l2 }}]           6%
  L3. Data Portability & Zero Lock-In                 [{{ l3 }}]           8%
  L4. Contestability & User Override                  [{{ l4 }}]           6%
-----------------------------------------------------------------------
Composite Fiduciary Alignment Index:                  {{ fiduciary_index }}/100
```

---

## 2. Fiduciary Hard Gate Evaluations

| Hard Gate | Status | Triggered Condition & Fiduciary Impact |
| :--- | :--- | :--- |
| **G1: Unsandboxed Execution / Prompt Injection (§ 3.1)** | `{{ g1_status }}` | `{{ g1_rationale }}` |
| **G2: Covert Action / Deceptive Defaults (§ 3.2)** | `{{ g2_status }}` | `{{ g2_rationale }}` |
| **G3: Divided Loyalty / Fiduciary Breach (§ 3.3)** | `{{ g3_status }}` | `{{ g3_rationale }}` |
| **G4: Data Hostage / Anti-Portability (§ 3.3)** | `{{ g4_status }}` | `{{ g4_rationale }}` |
| **G5: Unmarked External Boundary (§ 2.1)** | `{{ g5_status }}` | `{{ g5_rationale }}` |

---

## 3. Architectural & Boundary Analysis (§ 2.1)

- **Internal vs. External Boundary Clarity:** `{{ boundary_analysis }}`
- **Permission & Sandboxing Posture:** `{{ permission_posture }}`
- **Portability & Switching Friction:** `{{ portability_posture }}`

---

## 4. Prioritized Remediation Roadmap

1. `{{ remediation_1 }}`
2. `{{ remediation_2 }}`
3. `{{ remediation_3 }}`
