---
name: gcp-project-consolidation
description: Guides the identification, cleanup, and consolidation of duplicate environments, orphaned persistent disks, unlinked codelabs, and safe project decommissioning across Google Cloud portfolios.
license: Apache-2.0
---

# GCP Project Consolidation & Cleanup Skill

This skill provides an expert workflow for rationalizing sprawling Google Cloud portfolios by identifying duplicate build/test projects, detecting orphaned resources (e.g. persistent disks on stopped VMs), removing project liens, and safely executing project retirement.

---

## CRITICAL SAFETY MANDATE: READ-ONLY AUDIT & HUMAN EXECUTION

> **STRICT RULE FOR AGENT EXECUTION:**
> 1. The AI agent **MUST NOT** execute any mutable, modifying, or destructive commands against the user's Google Cloud infrastructure (e.g., `gcloud projects delete`, `gcloud compute disks delete`, `gcloud beta billing projects unlink`).
> 2. All audit steps **MUST be strictly read-only** (`list`, `describe`, `read`).
> 3. Recommendations and remediation steps **MUST be formatted as copy-pasteable shell command blocks for human review and execution**.

---

## When to Use

Use this skill when:
- Consolidating duplicate environments (e.g. merging build projects into primary dev hubs).
- Detecting and deleting orphaned persistent disks left behind by terminated or stopped VMs.
- Releasing unused static external IP addresses to avoid hourly reservation fees.
- Identifying and resolving deletion liens (such as attached Dialogflow agents).
- Safely decommissioning retired test projects or unlinking billing from dormant codelabs.

---

## Bundled References

1. **Decommissioning Checklist (`references/decommissioning-checklist.md`):**
   - Step-by-step verification before shutting down projects, handling deletion liens, and backup commands.
2. **Orphaned Resource Playbook (`references/orphaned-resource-playbook.md`):**
   - Commands for finding and removing persistent disks, unused static IPs, and idle Cloud SQL instances.

---

## Step-by-Step Workflow

### Step 1: Scan for Orphaned Assets
Check for assets incurring monthly storage or reservation charges without active compute:
- **Disks on Stopped VMs:** `gcloud compute disks list --project=<PID>`
- **Unused Static IPs:** `gcloud compute addresses list --project=<PID> --filter="status:RESERVED"`
- **Idle Cloud SQL:** `gcloud sql instances list --project=<PID>`

### Step 2: Check Deletion Liens
If planning project shutdown, verify whether any service liens are active:
```bash
gcloud alpha resource-manager liens list --project=<PROJECT_ID>
```

### Step 3: Classify Consolidation Strategy
- **Strategy A: Merge Workloads:** Move Cloud Run services or Firestore collections to a designated primary hub (e.g., `testingproject-19c4c`).
- **Strategy B: Unlink Billing ($0 Cost, Preserve Config):** For codelabs or reference architectures.
- **Strategy C: Permanent Shutdown:** For completely obsolete or duplicate projects.

### Step 4: Present Remediation Commands
Provide clear, copy-pasteable commands for the human operator:

```bash
# 1. Unlink billing from dormant project
gcloud beta billing projects unlink <PROJECT_ID>

# 2. Delete orphaned persistent disks
gcloud compute disks delete <DISK_NAME> --zone=<ZONE> --project=<PROJECT_ID> --quiet

# 3. Delete retired project
gcloud projects delete <PROJECT_ID> --quiet
```
