# Automated Billing Circuit Breaker Architecture

This document details the recommended architecture for implementing an **absolute hard dollar spend cap** in Google Cloud Platform using Cloud Billing Budgets, Pub/Sub, and Cloud Functions / Cloud Run.

---

## 1. The Architectural Problem: Alerts vs. Caps

In GCP, standard Billing Budget alerts **only send notifications** (emails or Pub/Sub messages). GCP **does not automatically stop services** when a budget threshold is exceeded.

To enforce an absolute hard cap (e.g., stopping all workloads when monthly spend reaches $100), an **automated circuit breaker** must be deployed.

---

## 2. Circuit Breaker Architecture Overview

```
[ GCP Billing Engine ]
         │
         ▼ (Publishes spend JSON every ~15-30 mins)
[ Cloud Pub/Sub Topic: billing-alerts ]
         │
         ▼
[ Cloud Function: billing-circuit-breaker ]
         │
         ├─ Spend >= 100% of Budget?
         │
         ├─ YES ──► Unlink Project from Billing OR Disable Costly APIs
         │          (gcloud beta billing projects unlink <PROJECT_ID>)
         │
         └─ NO  ──► Log current spend & take no action
```

---

## 3. Deployment Steps

### Step 1: Create a Pub/Sub Topic
```bash
gcloud pubsub topics create billing-alerts --project=<ADMIN_PROJECT_ID>
```

### Step 2: Attach Billing Budget to Pub/Sub
```bash
gcloud billing budgets create \
  --billing-account=<BILLING_ACCOUNT_ID> \
  --display-name="Automated $100 Hard Cap" \
  --budget-amount=100USD \
  --threshold-rule=percent=1.0 \
  --notifications-rule-pubsub-topic=projects/<ADMIN_PROJECT_ID>/topics/billing-alerts
```

### Step 3: Deploy Automated Circuit Breaker Function (Node.js / Python)
```python
import base64
import json
from googleapiclient import discovery

def stop_billing_on_budget_exceeded(event, context):
    pubsub_data = base64.b64decode(event['data']).decode('utf-8')
    data = json.loads(pubsub_data)
    
    cost_amount = data.get('costAmount')
    budget_amount = data.get('budgetAmount')
    project_id = "<TARGET_PROJECT_ID>"
    
    if cost_amount is not None and budget_amount is not None:
        if cost_amount >= budget_amount:
            print(f"CRITICAL: Budget exceeded (${cost_amount} >= ${budget_amount}). Disabling billing for {project_id}...")
            billing = discovery.build('cloudbilling', 'v1')
            billing.projects().updateBillingInfo(
                name=f"projects/{project_id}",
                body={'billingAccountName': ''}
            ).execute()
            print(f"Billing successfully unlinked for {project_id}.")
```

---

## 4. Operational Considerations
- **Propagation Delay:** GCP Billing telemetry publishes every 15–30 minutes. High-velocity bursts during that window may slightly exceed the threshold before disablement occurs.
- **Service Disruption:** Unlinking billing will immediately pause paid API calls and Compute Engine VMs. Re-linking billing instantly restores operations once approved.
