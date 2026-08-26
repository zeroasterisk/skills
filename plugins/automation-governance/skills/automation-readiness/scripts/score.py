#!/usr/bin/env python3
"""
Automation Readiness Scoring & Governance Evaluator
Based on Google DeepMind's "Intelligent AI Delegation" Framework (arXiv:2602.11865)

Computes a weighted readiness index across 11 diagnostic axes and applies
non-negotiable hard gate overrides to determine the safe automation tier and
operational guardrail matrix.
"""

import sys
import os
import json
import argparse
from typing import Dict, Any, Tuple, List

# Try importing pyyaml, fallback to minimal parser for standard YAML structures
try:
    import yaml
    HAS_YAML = True
except ImportError:
    HAS_YAML = False


def parse_simple_yaml(text: str) -> Dict[str, Any]:
    """Fallback simple YAML parser for key-value and nested dictionary maps."""
    result: Dict[str, Any] = {}
    current_dict = result
    stack: List[Tuple[int, Dict[str, Any]]] = [(0, result)]
    
    for line in text.splitlines():
        # Remove comments
        line_clean = line.split('#')[0].rstrip()
        if not line_clean.strip():
            continue
            
        indent = len(line_clean) - len(line_clean.lstrip())
        stripped = line_clean.strip()
        
        # Adjust stack based on indentation
        while stack and indent < stack[-1][0]:
            stack.pop()
            
        target_dict = stack[-1][1] if stack else result
        
        if ':' in stripped:
            key, val = stripped.split(':', 1)
            key = key.strip()
            val = val.strip()
            
            if not val:
                # New nested dictionary
                new_dict: Dict[str, Any] = {}
                target_dict[key] = new_dict
                stack.append((indent + 2, new_dict))
            else:
                # Parse value
                if (val.startswith('"') and val.endswith('"')) or (val.startswith("'") and val.endswith("'")):
                    parsed_val = val[1:-1]
                elif val.lower() == 'true':
                    parsed_val = True
                elif val.lower() == 'false':
                    parsed_val = False
                elif val.lower() in ('null', 'none', '~'):
                    parsed_val = None
                else:
                    try:
                        parsed_val = int(val) if '.' not in val else float(val)
                    except ValueError:
                        parsed_val = val
                target_dict[key] = parsed_val
    return result


def load_input_file(filepath: str) -> Dict[str, Any]:
    """Loads YAML or JSON input file."""
    if not os.path.exists(filepath):
        sys.stderr.write(f"Error: File '{filepath}' not found.\n")
        sys.exit(1)
        
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
        
    if filepath.endswith('.json'):
        return json.loads(content)
        
    if HAS_YAML:
        return yaml.safe_load(content)
    else:
        try:
            return json.loads(content)
        except Exception:
            return parse_simple_yaml(content)


AXIS_WEIGHTS = {
    'complexity': 0.08,
    'criticality': 0.15,
    'uncertainty': 0.10,
    'duration': 0.05,
    'cost': 0.05,
    'resources': 0.08,
    'constraints': 0.07,
    'verifiability': 0.13,   # Inverted (high verifiability = low risk)
    'reversibility': 0.12,   # Inverted (high reversibility = low risk)
    'contextuality': 0.10,
    'subjectivity': 0.07
}

TIER_DESCRIPTIONS = {
    'Tier 1': {
        'title': 'Full Autonomy (Unattended)',
        'description': 'Workflow can execute unattended with standing least-privilege permissions and lightweight outcome monitoring.'
    },
    'Tier 2': {
        'title': 'Autonomous + Process Monitoring',
        'description': 'Workflow executes autonomously with continuous process telemetry, automated pre-commit/synthetic verification, and runtime circuit breakers.'
    },
    'Tier 3': {
        'title': 'Human-in-the-Loop (HITL) Checkpoints',
        'description': 'Agent drafts, simulates, and executes safe stages; automatically pauses for explicit human review and approval before executing irreversible or critical actions.'
    },
    'Tier 4': {
        'title': 'Human-Led / Do Not Automate',
        'description': 'Workflow must remain firmly under human direction. AI acts strictly as an interactive co-pilot or reference assistant; human holds execution tokens and accountability.'
    }
}


def calculate_readiness(data: Dict[str, Any]) -> Dict[str, Any]:
    scores = data.get('scores', {})
    hard_gates = data.get('hard_gates', {})
    target = data.get('target', {})
    notes = data.get('notes', {})

    # Extract raw scores with defaults
    raw_scores = {
        'complexity': float(scores.get('complexity', 3)),
        'criticality': float(scores.get('criticality', 3)),
        'uncertainty': float(scores.get('uncertainty', 3)),
        'duration': float(scores.get('duration', 3)),
        'cost': float(scores.get('cost', 3)),
        'resources': float(scores.get('resources', 3)),
        'constraints': float(scores.get('constraints', 3)),
        'verifiability': float(scores.get('verifiability', 3)),
        'reversibility': float(scores.get('reversibility', 3)),
        'contextuality': float(scores.get('contextuality', 3)),
        'subjectivity': float(scores.get('subjectivity', 3))
    }

    # Transform scores to risk points (1 to 5)
    risk_scores = {}
    for k, v in raw_scores.items():
        if k in ('verifiability', 'reversibility'):
            # Inverted: rating of 5 means highly verifiable/reversible => risk is 1
            # Rating of 1 means unverifiable/irreversible => risk is 5
            risk_scores[k] = 6.0 - max(1.0, min(5.0, v))
        else:
            risk_scores[k] = max(1.0, min(5.0, v))

    # Compute weighted risk score (1.0 to 5.0)
    weighted_risk = sum(risk_scores[k] * AXIS_WEIGHTS[k] for k in AXIS_WEIGHTS)
    
    # Composite Readiness Index (0 to 100)
    # Risk 1.0 -> 100 Readiness, Risk 5.0 -> 0 Readiness
    readiness_index = round((5.0 - weighted_risk) / 4.0 * 100.0, 1)

    # Determine baseline tier from readiness index
    if readiness_index >= 80.0:
        baseline_tier = 'Tier 1'
    elif readiness_index >= 60.0:
        baseline_tier = 'Tier 2'
    elif readiness_index >= 40.0:
        baseline_tier = 'Tier 3'
    else:
        baseline_tier = 'Tier 4'

    # Evaluate Hard Gates
    triggered_gates = []
    max_allowed_tier = 1 # 1 = Tier 1, 2 = Tier 2, 3 = Tier 3, 4 = Tier 4

    # Gate 1: Contract-First Verifiability Gate
    g1_failed = (
        raw_scores['verifiability'] <= 2.0 or
        hard_gates.get('contract_first_verifiable') is False or
        (raw_scores['subjectivity'] >= 4.0 and raw_scores['verifiability'] <= 3.0)
    )
    if g1_failed:
        triggered_gates.append({
            'gate': 'Gate 1: Contract-First Verifiability',
            'condition': f"Low verifiability ({raw_scores['verifiability']}/5) or high subjectivity ({raw_scores['subjectivity']}/5).",
            'impact': 'Cannot be fully autonomous (Tier 1/2) without automated verification primitives.',
            'cap': 'Tier 3'
        })
        max_allowed_tier = max(max_allowed_tier, 3)

    # Gate 2: Blast Radius Gate (Criticality x Reversibility)
    g2_failed = (
        (raw_scores['criticality'] >= 4.0 and raw_scores['reversibility'] <= 2.0) or
        hard_gates.get('irreversible_blast_radius') is True
    )
    if g2_failed:
        triggered_gates.append({
            'gate': 'Gate 2: Blast Radius (Criticality × Reversibility)',
            'condition': f"High criticality ({raw_scores['criticality']}/5) with low reversibility ({raw_scores['reversibility']}/5).",
            'impact': 'Mandatory explicit human confirmation before executing any irreversible action.',
            'cap': 'Tier 3'
        })
        max_allowed_tier = max(max_allowed_tier, 3)

    # Gate 3: Statutory & Safety Floor Gate
    g3_failed = (
        hard_gates.get('statutory_safety_floor') is True or
        (raw_scores['criticality'] == 5.0 and raw_scores['constraints'] == 5.0)
    )
    if g3_failed:
        cap_target = 'Tier 4' if readiness_index < 50.0 else 'Tier 3'
        triggered_gates.append({
            'gate': 'Gate 3: Statutory / Safety Floor',
            'condition': 'Statutory safety floor or maximum criticality in regulated domain.',
            'impact': f'Autonomous execution prohibited by safety floor; must be {cap_target}.',
            'cap': cap_target
        })
        max_allowed_tier = max(max_allowed_tier, 4 if cap_target == 'Tier 4' else 3)

    # Gate 4: High Context Sensitivity & Privacy Gate
    g4_failed = (
        raw_scores['contextuality'] >= 4.0 or
        hard_gates.get('high_context_sensitivity') is True
    )
    if g4_failed:
        triggered_gates.append({
            'gate': 'Gate 4: Context Sensitivity & Privacy',
            'condition': f"High contextuality ({raw_scores['contextuality']}/5) or sensitive data access.",
            'impact': 'Standing long-lived credentials prohibited; mandates ephemeral JIT scoped tokens and sandboxing.',
            'cap': None # Does not necessarily cap tier, but adds mandatory guardrails
        })

    # Gate 5: Moral Crumple Zone & De-skilling Gate
    g5_failed = hard_gates.get('moral_crumple_zone_risk') is True
    if g5_failed:
        triggered_gates.append({
            'gate': 'Gate 5: Moral Crumple Zone / De-skilling',
            'condition': 'Identified risk of human acting as liability sponge without scrutiny, or depletion of apprenticeship.',
            'impact': 'Enforce curriculum routing or elevate to Tier 4.',
            'cap': 'Tier 4'
        })
        max_allowed_tier = max(max_allowed_tier, 4)

    # Map baseline tier string to int
    tier_num_map = {'Tier 1': 1, 'Tier 2': 2, 'Tier 3': 3, 'Tier 4': 4}
    baseline_num = tier_num_map[baseline_tier]
    
    # Final assigned tier is the more restrictive of baseline vs hard gates
    final_num = max(baseline_num, max_allowed_tier)
    inv_tier_map = {1: 'Tier 1', 2: 'Tier 2', 3: 'Tier 3', 4: 'Tier 4'}
    final_tier = inv_tier_map[final_num]
    
    override_occurred = (final_tier != baseline_tier)

    # Construct Guardrails based on final tier and gates
    guardrails = generate_guardrails(final_tier, raw_scores, g4_failed)

    return {
        'target': target,
        'raw_scores': raw_scores,
        'risk_scores': risk_scores,
        'weighted_risk': round(weighted_risk, 2),
        'readiness_index': readiness_index,
        'baseline_tier': baseline_tier,
        'final_tier': final_tier,
        'override_occurred': override_occurred,
        'triggered_gates': triggered_gates,
        'guardrails': guardrails,
        'notes': notes
    }


def generate_guardrails(tier: str, scores: Dict[str, float], high_context: bool) -> Dict[str, str]:
    if tier == 'Tier 1':
        return {
            'monitoring': 'Outcome-level polling: Log terminal status code, latency, and resource metrics. No synchronous human interrupts.',
            'permissions': 'Standing least-privilege tokens restricted to target service APIs. Long-lived credentials permitted if rotated regularly.',
            'verification': 'Automated schema validation and exit-code validation on completion.',
            'liability_firebreak': 'System owner assumes direct operational responsibility under standard operating limits.'
        }
    elif tier == 'Tier 2':
        return {
            'monitoring': 'Process-level event streaming (e.g. gRPC/SSE emitting CHECKPOINT_REACHED). Continuous anomaly detection with automated circuit breakers.',
            'permissions': 'Attenuated capability tokens. Automatic token revocation if telemetry exceeds drift or error-rate thresholds.',
            'verification': 'Pre-commit automated test suites, golden synthetic test cases, and cryptographic checksum validation of output artifacts.',
            'liability_firebreak': 'Contractual boundaries at sub-task handoffs; automated rollback triggered upon any verification test failure.'
        }
    elif tier == 'Tier 3':
        jit_clause = " Ephemeral Just-In-Time (JIT) tokens granted only upon human click." if high_context else " Scoped tokens limited to dry-run and draft actions."
        return {
            'monitoring': 'State machine with synchronous pauses at irreversible milestones. Present clear diff and rationale to human reviewer.',
            'permissions': f'Tiered authorization.{jit_clause} Live write/delete execution tokens blocked pending explicit approval.',
            'verification': 'Dual-layer: Automated smoke/unit tests executed first, followed by mandatory human inspection and digital sign-off.',
            'liability_firebreak': 'Explicit Liability Firebreak: Human approval explicitly transfers operational accountability to the human reviewer.'
        }
    else: # Tier 4
        return {
            'monitoring': 'Continuous interactive human session. AI functions solely in an advisory, co-pilot, or draft-generation capacity.',
            'permissions': 'Zero autonomous execution privileges. All credentials, API keys, and mutation tokens remain exclusively in human custody.',
            'verification': 'Human end-to-end domain expertise, inspection, and verification.',
            'liability_firebreak': 'Human principal holds 100% end-to-end legal and operational accountability.'
        }


def format_markdown_report(res: Dict[str, Any]) -> str:
    target = res.get('target', {})
    t_name = target.get('name', 'unnamed-unit')
    t_type = target.get('type', 'workflow')
    assessor = target.get('assessor', 'unassigned')
    desc = target.get('description', 'No description provided.')

    tier = res['final_tier']
    tier_info = TIER_DESCRIPTIONS[tier]
    scores = res['raw_scores']
    readiness = res['readiness_index']
    
    md = []
    md.append(f"# Automation Readiness Assessment: `{t_name}`\n")
    md.append(f"- **Target Type:** {t_type.capitalize()}")
    md.append(f"- **Assessor:** {assessor}")
    md.append(f"- **Framework Reference:** Google DeepMind *Intelligent AI Delegation* (arXiv:2602.11865)")
    md.append(f"- **Candidate Description:** {desc}\n")
    md.append("---\n")
    
    md.append("## 1. Executive Summary\n")
    md.append(f"- **Assigned Automation Tier:** **`{tier}` — {tier_info['title']}**")
    md.append(f"- **Readiness Score:** `{readiness}/100` (Baseline: `{res['baseline_tier']}`)")
    if res['override_occurred']:
        md.append(f"- **Hard Gate Override:** ⚠️ **Active** (Down-tiered from `{res['baseline_tier']}` to `{tier}` due to safety constraints)")
    else:
        md.append(f"- **Hard Gate Override:** None (Baseline tier validated)")
    md.append(f"- **Core Guidance:** {tier_info['description']}\n")
    
    md.append("## 2. 11-Axis Diagnostic Scorecard\n")
    md.append("| Axis | Rating (1-5) | Interpretation | Weight | Risk Contribution |")
    md.append("| :--- | :---: | :--- | :---: | :---: |")
    
    axis_labels = [
        ('complexity', 'Complexity (Difficulty/Steps)', '1=Narrow, 5=Deep reasoning'),
        ('criticality', 'Criticality (Blast Radius)', '1=Cosmetic, 5=Catastrophic'),
        ('uncertainty', 'Uncertainty (Stochasticity)', '1=Deterministic, 5=Volatile'),
        ('duration', 'Duration (Execution Horizon)', '1=Instant, 5=Long-lived'),
        ('cost', 'Cost & Overhead', '1=Negligible, 5=Prohibitive'),
        ('resources', 'Resource Scope (Privileges)', '1=Sandboxed, 5=Production roots'),
        ('constraints', 'Operational Constraints', '1=Flexible, 5=Strict SLAs/Regs'),
        ('verifiability', 'Verifiability (Inverted)', '5=Automated tests, 1=Subjective'),
        ('reversibility', 'Reversibility (Inverted)', '5=Dry-run safe, 1=Irreversible'),
        ('contextuality', 'Contextuality & Privacy', '1=Public/Sanitized, 5=Secrets/PII'),
        ('subjectivity', 'Subjectivity', '1=Objective fact, 5=Taste/Brand')
    ]
    
    for k, name, note in axis_labels:
        raw_val = scores[k]
        risk_val = res['risk_scores'][k]
        weight = AXIS_WEIGHTS[k]
        contrib = round(risk_val * weight, 3)
        md.append(f"| **{name}** | `{raw_val}` | {note} | {int(weight*100)}% | `{contrib}` |")
        
    md.append(f"| **Weighted Risk Score** | **`{res['weighted_risk']}/5.0`** | *(1.0 = Min Risk, 5.0 = Max Risk)* | **100%** | **Readiness: `{readiness}/100`** |\n")
    
    md.append("## 3. Hard Gate Veto Evaluations\n")
    if not res['triggered_gates']:
        md.append("✅ **No hard gate violations detected.** Baseline score governs autonomy level.\n")
    else:
        md.append("| Hard Gate | Condition Detected | Governance Action / Impact | Required Tier Cap |")
        md.append("| :--- | :--- | :--- | :---: |")
        for g in res['triggered_gates']:
            cap_str = g['cap'] if g['cap'] else "Operational Guardrail"
            md.append(f"| **{g['gate']}** | {g['condition']} | {g['impact']} | **{cap_str}** |")
        md.append("")
        
    g_rails = res['guardrails']
    md.append("## 4. Operational Guardrail Matrix\n")
    md.append(f"### 4.1 Monitoring Protocol (§4.5)")
    md.append(f"{g_rails['monitoring']}\n")
    md.append(f"### 4.2 Permission & Authority Model (§4.7)")
    md.append(f"{g_rails['permissions']}\n")
    md.append(f"### 4.3 Verification Mechanism (§4.8)")
    md.append(f"{g_rails['verification']}\n")
    md.append(f"### 4.4 Liability Firebreaks & Accountability (§5.2)")
    md.append(f"{g_rails['liability_firebreak']}\n")
    
    if res.get('notes'):
        md.append("## 5. Assessment Notes & Evidence\n")
        for nk, nv in res['notes'].items():
            md.append(f"- **{nk.replace('_', ' ').capitalize()}:** {nv}")
        md.append("")
        
    md.append("## 6. Recommended Action Plan\n")
    if tier == 'Tier 1':
        md.append("1. Formalize standing least-privilege tokens and configure standard outcome-level logging.")
        md.append("2. Implement post-hoc automated schema/error assertions.")
        md.append("3. Deploy as an unattended autonomous skill or service.")
    elif tier == 'Tier 2':
        md.append("1. Implement process-level event telemetry and heartbeat checkpoints.")
        md.append("2. Establish automated pre-commit unit tests and synthetic canary verifications.")
        md.append("3. Configure automated circuit breakers to revoke capability tokens upon SLO drift.")
    elif tier == 'Tier 3':
        md.append("1. Implement a 2-phase state machine: (a) Draft & simulate changes, (b) Pause for sign-off.")
        md.append("2. Build a clear, human-readable diff and impact manifest for the reviewer.")
        md.append("3. Gate mutation/execution tokens on cryptographic or authenticated human approval.")
    else: # Tier 4
        md.append("1. Retain human execution control; do not provision autonomous mutation tokens.")
        md.append("2. Scope AI role exclusively to drafting suggestions, searching documentation, or providing reference analysis.")
        md.append("3. Ensure human operator conducts end-to-end review and manual execution.")
        
    return "\n".join(md)


def main():
    parser = argparse.ArgumentParser(description="Evaluate automation readiness using DeepMind Intelligent AI Delegation framework.")
    parser.add_argument('--input', '-i', required=True, help="Path to input assessment YAML or JSON file.")
    parser.add_argument('--json', action='store_true', help="Output raw JSON results instead of Markdown.")
    parser.add_argument('--output', '-o', help="Optional path to write output report.")
    
    args = parser.parse_args()
    
    data = load_input_file(args.input)
    result = calculate_readiness(data)
    
    if args.json:
        output_str = json.dumps(result, indent=2)
    else:
        output_str = format_markdown_report(result)
        
    if args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            f.write(output_str)
        print(f"Report written to {args.output}")
    else:
        print(output_str)


if __name__ == '__main__':
    main()
