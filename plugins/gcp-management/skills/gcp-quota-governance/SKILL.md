---
name: gcp-quota-governance
description: Evaluates, recommends, and formats commands for setting hard API quotas, rate limits, Cloud Run scaling caps, and automated billing circuit breakers across Google Cloud & Vertex AI projects.
license: Apache-2.0
---

# GCP Quota & Spending Governance Skill

This skill provides an expert workflow for analyzing cloud spend velocity and establishing **enforceable hard caps, rate limits, and automated circuit breakers** across Google Cloud Platform and Vertex AI.

---

## CRITICAL SAFETY MANDATE: READ-ONLY AUDIT & HUMAN EXECUTION

> **STRICT RULE FOR AGENT EXECUTION:**
> 1. The AI agent **MUST NOT** execute any mutable quota changes, scaling overrides, or billing modifications directly on the user's infrastructure.
> 2. All discovery operations **MUST be strictly read-only** (`list`, `describe`, `inspect_quotas.py`).
> 3. Recommended quota adjustments and scaling limits **MUST be formatted as copy-pasteable CLI commands for human review and execution**.

---

## When to Use

Use this skill when:
- Investigating runaway API spend (e.g., Vertex AI Claude models, Gemini API, Text-to-Speech).
- Setting hard request/min or token/min rate limits via `gcloud beta quotas preferences`.
- Capping Cloud Run microservice auto-scaling (`--max-instances`).
- Designing automated billing circuit breakers (Pub/Sub + Cloud Functions) to enforce hard dollar cutoffs.
- Inspecting existing quota overrides across projects using `scripts/inspect_quotas.py`.

---

## Bundled Tools & References

1. **Quota Inspector Script (`scripts/inspect_quotas.py`):**
   - Read-only script that queries configured Cloud Run max instances and custom quota preferences.
   - Run: `python3 scripts/inspect_quotas.py --project <PROJECT_ID>`
2. **Quota Capping Guide (`references/quota-capping-guide.md`):**
   - Syntax and dimension mappings for Vertex AI and Gemini base models.
3. **Automated Circuit Breaker Architecture (`references/automated-circuit-breaker.md`):**
   - Reference implementation for event-driven hard spend caps.

---

## Step-by-Step Workflow

### Step 1: Inspect Current Scaling & Quotas
Run the read-only inspection script:
```bash
python3 scripts/inspect_quotas.py --project <PROJECT_ID> --service aiplatform.googleapis.com
```

### Step 2: Determine Appropriate Cap Granularity
Based on the cost drivers identified:
- **Layer 1 (Per-Model / Per-Token Cap):** For frontier LLMs (Claude Sonnet, Opus, Gemini 1.5 Pro).
- **Layer 2 (Regional API Request Cap):** Total prediction requests/min in a specific region (e.g., `us-central1`).
- **Layer 3 (Microservice Instance Cap):** Setting `--max-instances=2` on Cloud Run services.
- **Layer 4 (Hard Dollar Spend Cap):** Automated billing circuit breaker via Pub/Sub.

### Step 3: Present Recommendations to Human Operator
Formulate copy-pasteable commands for the human operator to apply:

```bash
# Example: Cap online prediction requests to 50/min in us-central1
gcloud beta quotas preferences create \
  --service=aiplatform.googleapis.com \
  --project=<PROJECT_ID> \
  --quota-id=OnlinePredictionRequestsPerMinutePerProjectPerRegion \
  --dimensions=region=us-central1 \
  --preferred-value=50 \
  --allow-high-percentage-quota-decrease

# Example: Enforce Cloud Run max instances
gcloud run services update <SERVICE_NAME> \
  --project=<PROJECT_ID> \
  --region=<REGION> \
  --max-instances=2
```
