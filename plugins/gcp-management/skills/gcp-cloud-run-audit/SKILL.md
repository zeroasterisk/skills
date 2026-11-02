---
name: gcp-cloud-run-audit
description: Sweeps and audits deployed Google Cloud Run services and jobs across all GCP projects for public unauthenticated exposure (allUsers vs IAP), container image age and runtime CVE posture, idle min-instance/GPU cost leaks, default service account usage, plaintext environment secrets, and 30-day HTTP traffic. Use when reviewing deployed Cloud Run services across Google Cloud projects, checking for stale Node/Python container images, or auditing Cloud Run security and cost posture.
license: Apache-2.0
---

# GCP Cloud Run Fleet Sweep & Posture Review Skill

## Overview

This skill provides a parallelized, strictly **read-only** workflow to inventory and audit every deployed Cloud Run service and job across your Google Cloud Platform (GCP) project portfolio.

It evaluates each deployed service across five operational and security dimensions:
1. **Exposure & Authentication Posture**: Ingress controls (`all`, `internal`, `internal-and-cloud-load-balancing`), IAM invoker bindings (`allUsers` / `allAuthenticatedUsers`), and Identity-Aware Proxy (`run.googleapis.com/iap-enabled`).
2. **Container Image & Runtime Freshness**: Image URI, tag vs. `@sha256` digest pinning, active revision deployment age (flagging stale images deployed before major runtime advisories such as the October 21, 2026 Node.js security release), and source repository correlation.
3. **Scaling, GPU & Idle Cost Leaks**: Minimum instance floors (`minScale > 0`), always-on CPU allocation (`cpu-throttling: false`), uncapped `maxScale`, and attached GPU accelerators (`nvidia-l4`, `nvidia-rtx-pro-6000`).
4. **Identity & Secret Hygiene**: Default Compute Engine service account usage (`-compute@developer.gserviceaccount.com`) vs. dedicated least-privilege service accounts, and literal environment variables with secret-shaped names (`KEY`, `TOKEN`, `SECRET`, `PASSWORD`) vs. Secret Manager mounts (`valueFrom.secretKeyRef`).
5. **30-Day Traffic & Zombie Detection**: Recent HTTP request activity in Cloud Logging to distinguish active production endpoints from abandoned standby deployments.

---

## Critical Safety Mandate: Read-Only Audit

1. The agent **MUST NOT** execute any mutating or destructive `gcloud run` commands (`deploy`, `delete`, `services update`, `remove-iam-policy-binding`) without explicit human authorization for the specific service.
2. All discovery and inspection commands in `scripts/audit_cloud_run_fleet.py` are strictly read-only (`list`, `describe`, `get-iam-policy`, `logging read`).
3. Remediation commands must be presented as copy-pasteable `gcloud` blocks or executed only when explicitly requested by the user.

---

## Bundled Resources

- `scripts/audit_cloud_run_fleet.py` — Parallelized, read-only scanner that discovers all Cloud Run services and jobs across billing-enabled GCP projects (or a targeted `--projects` list) and outputs a structured JSON and Markdown posture report.
- [Cloud Run Posture Checklist & Remediation Reference](references/cloud-run-posture-checklist.md) (`references/cloud-run-posture-checklist.md`) — Detailed rubric covering IAM/IAP hardening, runtime CVE rebuilds, scaling & GPU cost guardrails, and Secret Manager migration commands.

---

## Step-by-Step Workflow

### Step 1: Run the Cloud Run Fleet Sweep

Execute `scripts/audit_cloud_run_fleet.py` across all accessible GCP projects (or pass `--projects` to scope to specific projects):

```bash
# Sweep all billing-enabled GCP projects and emit JSON + Markdown summary
./scripts/audit_cloud_run_fleet.py --output /tmp/opencode/cloud_run_fleet_audit.json --markdown /tmp/opencode/CLOUD_RUN_AUDIT_REPORT.md

# Scope to specific projects
./scripts/audit_cloud_run_fleet.py --projects my-project-1,my-project-2
```

### Step 2: Triage Findings by Risk & Cost Tier

Consult [Cloud Run Posture Checklist & Remediation Reference](references/cloud-run-posture-checklist.md) to classify each service:
- **P0 — Unintended Public Exposure or Plaintext Secrets**: Services with `allUsers` invoker binding that are not intended public sites/APIs, or services passing sensitive keys as literal env vars instead of Secret Manager references.
- **P1 — Always-On Idle Cost (`minScale > 0` or GPU Attached)**: Services keeping warm instances or GPUs 24/7, especially when 30-day HTTP traffic is zero.
- **P2 — Stale Container Base Images (Runtime CVE Drift)**: Services running container revisions built prior to recent runtime security patches (e.g., Node.js containers built before `2026-10-21`) that need a fresh rebuild/redeploy from their updated GitHub repository.
- **P3 — Identity & Scaling Hygiene**: Services running as the default Compute Engine service account, missing `maxScale` caps, or receiving zero 30-day traffic (zombie candidates).

### Step 3: Correlate with Local/GitHub Source Repositories

For services flagged for runtime CVE rebuilds or configuration drift, map the service name and image repository back to its source repository in `~/projects` or GitHub, verify the repository's Dockerfile base image (`node:22-slim`, `node:24-slim`, etc.), and provide exact rebuild/redeploy commands.
