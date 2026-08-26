---
name: gcp-project-assessment
description: Audits, categorizes, and correlates Google Cloud & Firebase projects across billing accounts, active compute, 30-day traffic metrics, cost drivers, and Firebase services. Produces structured Markdown reports with Mermaid cost charts and actionable optimization recommendations.
license: Apache-2.0
---

# GCP & Firebase Project Assessment Skill

This skill provides an automated, parallelized workflow to analyze, categorize, and optimize Google Cloud Platform (GCP) and Firebase project portfolios.

It inspects billing accounts, itemized service spend via BigQuery Billing Export, active compute resources (Compute Engine, Cloud Run, App Engine, Cloud Functions, GKE, Cloud SQL), Cloud Storage buckets, Cloud Logging activity, and Firebase services (Firestore databases, Firebase Apps, Firebase Hosting domains).

---

## CRITICAL SAFETY MANDATE: READ-ONLY AUDIT & HUMAN EXECUTION

> **STRICT RULE FOR AGENT EXECUTION:**
> 1. The AI agent **MUST NOT** execute any mutable, modifying, or destructive commands against the user's Google Cloud infrastructure (e.g., `gcloud compute instances stop`, `gcloud compute disks delete`, `gcloud projects delete`, `gcloud beta billing projects unlink`).
> 2. All audit steps **MUST be strictly read-only** (`list`, `describe`, `read`, BigQuery SQL `SELECT`).
> 3. Recommendations and remediation steps **MUST be formatted as copy-pasteable shell command blocks for human review and execution**.

---

## When to Use

Use this skill when:
- Evaluating a collection of Google Cloud / Firebase projects.
- Identifying exact 30-day dollar spend per project and per service (e.g. Vertex AI, Claude models, Gemini API, Storage).
- Calculating month-to-date (MTD) spend and month-end projections.
- Identifying cost drivers, running VMs, or orphaned resources (e.g., persistent disks on stopped VMs).
- Determining which projects are receiving active user or API traffic vs. background system activity.
- Planning project consolidations, billing unlinking, or project closures.
- Generating a formal portfolio audit report (`GCP_PROJECTS_AUDIT_REPORT.md`) with visual Mermaid diagrams and ASCII charts.

---

## Required Tools & Dependencies

Ensure the following local tools are available:
- `gcloud` CLI (authenticated with access to billing accounts and project viewer permissions)
- `firebase` CLI (`firebase --version`)
- `bq` CLI (BigQuery CLI tool for itemized billing export queries)
- `python3` (with standard library modules: `subprocess`, `json`, `concurrent.futures`, `datetime`)

---

## Bundled Assets & Scripts

1. **Audit Script (`scripts/audit_portfolio.py`):** Parallelized, read-only discovery script capturing compute, storage, logging traffic, Firebase assets, billing budgets, and BigQuery spend.
2. **SQL Reference (`references/billing-export-queries.sql`):** Pre-formulated BigQuery SQL queries for 30-day spend, Week-over-Week velocity, and MTD daily burn rates.

### Execution:
```bash
python3 scripts/audit_portfolio.py --output gcp_audit_results.json
```

---

## Step-by-Step Skill Workflow

### Step 1: Execute Portfolio Audit
Run `python3 scripts/audit_portfolio.py --output gcp_audit_results.json` or perform equivalent read-only `gcloud`, `bq`, and `firebase` commands.

### Step 2: Analyze Itemized Spend & Cost Drivers
Query BigQuery billing export tables for 30-day net spend grouped by project and service:
```sql
SELECT
  IFNULL(project.id, "Shared / Unassigned") AS project_id,
  service.description AS service_description,
  ROUND(SUM(cost), 2) AS gross_cost_usd,
  ROUND(SUM(cost + IFNULL((SELECT SUM(c.amount) FROM UNNEST(credits) c), 0)), 2) AS net_cost_usd
FROM
  `simple-node-001.billingexport.gcp_billing_export_v1_00615D_35664D_BF0DF0`
WHERE
  _PARTITIONTIME >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 30 DAY)
GROUP BY
  project_id, service_description
HAVING
  gross_cost_usd > 0 OR net_cost_usd > 0
ORDER BY
  net_cost_usd DESC
```

### Step 3: Categorize Projects
Analyze `gcp_audit_results.json` to group projects into four distinct categories:
- **Category A: Active Production & Workload Hubs** (Active HTTP/API traffic, high spend, production workloads).
- **Category B: Deployed Services / Low Traffic & Standby** (Deployed Cloud Run/Functions/Hosting with low or zero 30d traffic; consolidation candidates).
- **Category C: Dormant Projects with Billing Enabled** (Zero active compute, zero traffic, but billing linked; candidates for unlinking billing).
- **Category D: Billing Disabled / Unlinked Projects** ($0 cost; candidates for project deletion/cleanup).

### Step 4: Generate Report with Mermaid Charts & Visualizations
Write a Markdown report named `GCP_PROJECTS_AUDIT_REPORT.md` in the current working directory containing:
1. **Executive Summary & Progress Update:** High-level project counts, total spend, billing-enabled vs unlinked.
2. **30-Day Cost & Spend Analysis (Data & Visualizations):**
   - **Mermaid Pie Chart:** Portfolio spend distribution across projects.
   - **Mermaid Bar / Gantt Chart:** Top service spend breakdown for the primary project.
   - **Itemized Dollar Breakdown Table:** Project, Service Description, Gross Cost, Net Cost.
3. **High-Priority Active Projects (In-Depth Audit):** Cloud Run services, Firebase DBs, apps, domains, buckets.
4. **Firebase Services Correlation Matrix:** Comprehensive table linking projects to Firestore DBs, Apps, Hosting domains, and status.
5. **Master Categorization:** Structured list of all projects under Categories A, B, C, and D.
6. **Human Action Roadmap & Command Cheatsheet:** Copy-pasteable `gcloud` command blocks for the human operator to review and execute.

---

## Human Remediation Commands (Provide to User - Do Not Execute)

```bash
# 1. Stop a running VM instance
gcloud compute instances stop <INSTANCE_NAME> --zone=<ZONE> --project=<PROJECT_ID>

# 2. Delete orphaned persistent disks
gcloud compute disks delete <DISK_NAME> --zone=<ZONE> --project=<PROJECT_ID> --quiet

# 3. Unlink billing from a dormant project
gcloud beta billing projects unlink <PROJECT_ID>

# 4. Delete/shut down a retired project
gcloud projects delete <PROJECT_ID> --quiet
```
