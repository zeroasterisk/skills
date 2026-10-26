---
name: developer-friction-reviewer
description: >-
  Orchestrates persona-based developer friction reviews and audit loops on onboarding flows, recipes, tools, and CLIs. Spawns a persona subagent to execute documented steps from a cold start, record errors into a structured Friction Log artifact, and remediate verified issues across iterative review loops. Use when testing developer experience (DX), walking new developer journeys, auditing README instructions, validating recipes, or running cold-start onboarding audits. Don't use for generic unit testing or standalone code formatting without a persona walkthrough.
license: Apache-2.0
compatibility: Requires POSIX shell, python3, and git. Supports subagent orchestration via invoke_subagent.
metadata:
  author: alanblount
  version: 1.0.0
---

# Developer Friction Reviewer (`developer-friction-reviewer`)

Orchestrate automated, persona-driven developer friction audits and iterative remediation loops for codebases, developer recipes, SDK starter kits, and command-line interfaces (CLIs).

This skill replicates real developer behavior: it spawns an isolated subagent instructed to adopt a specific developer persona (novice developer, cloud SRE, security auditor), attempts the documented onboarding journey from a true cold start, catalogs every failure into a structured **Friction Log artifact**, and executes automated verification gates to eliminate papercuts and blockers before human users encounter them.

---

## The Core Review Loop

The friction review operates as an iterative control loop between the **Main Orchestrator** and a **Persona Subagent**:

```
 ┌────────────────────────────────────────────────────────┐
 │ 1. Main Orchestrator                                   │
 │    - Identifies target path & scope                    │
 │    - Selects persona & synthesizes subagent prompt     │
 │    - Spawns subagent via invoke_subagent(self)         │
 └───────────────────────┬────────────────────────────────┘
                         │
                         ▼
 ┌────────────────────────────────────────────────────────┐
 │ 2. Persona Subagent (Cold Start)                       │
 │    - Assumes persona mindset (Novice, SRE, Auditor)    │
 │    - Walks journey stages strictly from docs           │
 │    - Probes surfaces, captures raw error outputs       │
 │    - Records findings in Friction Log artifact         │
 └───────────────────────┬────────────────────────────────┘
                         │
                         ▼
 ┌────────────────────────────────────────────────────────┐
 │ 3. Remediation (Collaborative or Autonomous)           │
 │    - Fixes root causes (code, config, docs)            │
 │    - Preserves existing comments and coding styles     │
 └───────────────────────┬────────────────────────────────┘
                         │
                         ▼
 ┌────────────────────────────────────────────────────────┐
 │ 4. Automated Verification Gates                        │
 │    - Linter & formatter: ruff, eslint, gofmt           │
 │    - Structure & manifest validation                   │
 │    - Offline runnability vs live integration tests     │
 │    - Endpoint probing suite (FastAPI / HTTP / CLI)     │
 └───────────────────────┬────────────────────────────────┘
                         │ (If multi-loop requested)
                         ▼
           Cycle next persona (Loop 1..N)
```

---

## 1. Journey Stages (Cold Start to Production)

Every friction review evaluates up to 6 distinct stages of the developer journey. The persona subagent must progress sequentially:

1. **Stage 1: Discovery & Navigation**
   - Cloning, file navigation, finding the entry point.
   - Verification: Does `cd <documented-path>` resolve? Are directory paths in the README current?

2. **Stage 2: Environment Setup, Dependencies & Auth**
   - Virtual environments (`uv sync`, `npm install`, `go mod download`), PATH resolution, `.env.example` completeness.
   - Verification: Does the app crash on import without cloud credentials? Does it clobber user configuration or environment variables?

3. **Stage 3: Local Run & CLI Execution**
   - Running the primary CLI or script entrypoint.
   - Verification: Does the command run non-interactively? Does it block on unprompted telemetry collection or interactive questions?

4. **Stage 4: Serving & Endpoint Probing**
   - Local servers (FastAPI, Flask, Express, gRPC).
   - Verification: Does the server respect `$PORT`? Are health endpoints (`/health`, `/healthz`) responsive? Do A2A discovery routes (`/.well-known/agent-card.json`) return 200 OK without 404 or 500 errors?

5. **Stage 5: Testing & Verification Suite**
   - Running test suites (`pytest`, `npm test`, `go test`).
   - Verification: Are fast, offline smoke tests segregated from credentialed, live-network integration tests? Does running the default test command fail if cloud credentials are absent?

6. **Stage 6: Container Packaging & Deployment**
   - Container builds (`Dockerfile`), `.dockerignore` hygiene, deployment scripts.
   - Verification: Does the Docker build succeed with layer caching? Does `.dockerignore` exclude `.env`, `.git`, `.venv`, and credential files? Are IAM role recommendations least-privilege?

---

## 2. Friction Severity Matrix

Every issue discovered during the walkthrough must be classified using this severity rubric:

| Severity | Category | Definition | Action Required |
|:---|:---|:---|:---|
| **P0** | **Blocker** | Prevents developer forward progress completely. The user cannot proceed without out-of-band expertise or reverse-engineering. Examples: Broken directory path in README, missing import, unhandled runtime exception on standard routes, mandatory credentials crashed at import time. | Must be resolved and verified immediately before proceeding to next stages. |
| **P1** | **Friction** | Degraded experience, misleading errors, or hidden prerequisites. Workarounds exist but require developer time and create doubt. Examples: Hardcoded port ignoring `$PORT`, interactive telemetry prompts freezing headless scripts, mixed online/offline test commands. | Remediate in code or document explicitly in README. |
| **P2** | **Papercut** | Visual polish, documentation omissions, stale bounds, or ergonomics. Examples: Stale package bounds in secondary deployment scripts, missing `.env` field descriptions, minor styling discrepancies. | Fix inline or log for follow-up refinement. |

---

## 3. Configurable Persona Archetypes

Select the appropriate persona based on the target audit:

1. **Novice Developer (Cold Start)**
   - *Mindset:* First-time user. Zero repo history, no pre-cached tools, no global environment variables set.
   - *Behavior:* Follows documentation verbatim. Never guesses missing parameters. If a command fails or hangs, records the exact terminal trace and halts until resolved.
   - *Checklist:* See [`references/persona-catalog.md`](references/persona-catalog.md#1-novice-developer-cold-start).

2. **Production SRE / Cloud Operator**
   - *Mindset:* Deployability, container performance, observability, and operations.
   - *Behavior:* Inspects `Dockerfile` layer cache efficiency, non-root user execution, `$PORT` binding, SIGTERM graceful shutdown handling, health endpoints (`/healthz`), and resource requests.
   - *Checklist:* See [`references/persona-catalog.md`](references/persona-catalog.md#2-production-sre--cloud-operator).

3. **Security, Governance & Dependency Hygiene Auditor**
   - *Mindset:* Least privilege, leak prevention, and OWASP Top 10 compliance.
   - *Behavior:* Scans for hardcoded credentials, verifies `.dockerignore` excludes local secrets and build caches, audits IAM permissions (no `roles/owner`), checks prompt injection boundaries in tools, and reviews dependency lockfiles.
   - *Checklist:* See [`references/persona-catalog.md`](references/persona-catalog.md#3-security--governance-auditor).

4. **Multi-Agent & Protocol Architect**
   - *Mindset:* Contract adherence, A2A/A2UI protocol compliance, and agent tool resilience.
   - *Behavior:* Probes `agent-card.json`, validates schema conformity, inspects tool input schemas, checks error encapsulation (no raw stack traces in HTTP responses), and tests timeout handling.
   - *Checklist:* See [`references/persona-catalog.md`](references/persona-catalog.md#4-multi-agent--protocol-architect).

---

## 4. Orchestration Protocol: How to Run the Loop

### Step 1: Initialize Workspace & Artifacts
1. Ensure the workspace is clean (`git status`). Note existing unstaged changes.
2. Initialize the Friction Log artifact in the session artifact directory:
   `<appDataDir>/brain/<conversation-id>/<TargetName>_<Persona>_Friction_Log.md`
   Use [`references/friction-log-template.md`](references/friction-log-template.md) as the canonical structure.
3. You can use the helper script `scripts/init-friction-log.py` to scaffold the log file:
   ```bash
   python3 plugins/developer-friction-reviewer/skills/developer-friction-reviewer/scripts/init-friction-log.py \
     --target "contrib/python/financial-advisor" \
     --persona "Novice Developer" \
     --output "<artifact-dir>/Financial_Advisor_Novice_Developer_Friction_Log.md"
   ```

### Step 2: Spawn the Subagent
Invoke a subagent using `invoke_subagent` with the `self` type. Pass an explicit prompt defining:
- The persona to adopt.
- The target repository path and starting README/file.
- The constraint to execute documented commands sequentially without skipping steps.
- The instruction to record every failure into the Friction Log artifact.
- The specific verification gates required before concluding.

*(See Section 5 below for copy-pasteable invocation templates).*

### Step 3: Review Subagent Feedback & Apply Targeted Fixes
When the subagent completes its walkthrough:
1. Review the generated Friction Matrix and reported error outputs.
2. If the subagent applied fixes, review the diffs against repository standards.
3. If orchestrating collaboratively, implement targeted fixes directly in the recipe files:
   - Fix root causes, not superficial symptoms.
   - Never suppress exceptions with blind `try/except: pass` if error handling is expected.
   - Preserve existing coding conventions and file comments.

### Step 4: Run Automated Verification Gates
Run all relevant repo checks to verify the workspace is in pristine condition:
```bash
# Python recipes
uvx ruff check <target_dir>/
uvx ruff format --check <target_dir>/
uv run pytest <target_dir>/tests/test_runnability.py

# Recipe structure and manifest validators (if repo provides them)
uv run validate manifest <target_dir>
uv run validate structure <target_dir>

# Endpoint health and serving checks
python3 -c "from fastapi.testclient import TestClient; ..."
```

### Step 5: Multi-Loop Iteration (Optional)
If running a full multi-loop audit:
- **Loop 0:** Novice Developer Cold Start (Discovery, Setup, CLI, Runnability).
- **Loop 1:** Production SRE & Cloud Run (Containerization, Health Probes, Ports).
- **Loop 2:** Multi-Agent Architecture & Tool Resilience (Protocols, Schemas).
- **Loop 3:** Security, Governance & Dependency Hygiene (Secrets, `.dockerignore`, IAM).

Append findings from each loop into the canonical Friction Log artifact under dedicated loop headings (`## Loop N: ...`).

---

## 5. Subagent Prompt Template

Use this prompt structure when calling `invoke_subagent`:

```markdown
You are executing a Developer Friction Review on `<target_path>`.

Persona: <Persona Name> (e.g. Novice Developer / First-Time User)
Mission: Walk the documented developer journey from a true cold start, strictly executing the steps documented in README.md. Record every friction point and failure into the Friction Log artifact.

Scope & Journey Stages:
1. Discovery & Navigation: Clone/cd to `<target_path>`, inspect folder layout.
2. Environment Setup: Follow dependency installation and environment setup instructions. Do not assume pre-installed tools. Check `.env.example`.
3. Local Run / CLI: Execute documented commands. Note any interactive prompts that block automation (e.g. telemetry).
4. Serving & Endpoints: Probe all documented HTTP/gRPC endpoints (health checks, agent cards, API routes).
5. Testing: Run documented test commands. Verify whether offline smoke tests pass without live cloud credentials.
6. Packaging & Deployment: Inspect Dockerfile, container instructions, and deployment configurations.

Artifact Instructions:
- Update the Friction Log artifact at `<artifact_path>`.
- Assign every issue a unique ID (`FL-01`, `FL-02`, ...), Stage, Severity (`P0 Blocker`, `P1 Friction`, `P2 Papercut`), Root Cause, and Status.
- Capture exact terminal output, stack traces, and HTTP response codes.

Remediation & Verification:
- Implement targeted fixes for verified code and documentation defects.
- Run workspace verification gates: `<verification_commands>`.
- Report back with a concise executive summary and list of applied fixes.
```

---

## 6. Best Practices & Anti-Patterns

- **Never bypass cold-start testing:** Do not reuse cached virtual environments or shell state when evaluating Stage 1 and Stage 2. Test how the repository behaves when dependencies are fresh.
- **Separate offline smoke tests from credentialed tests:** A developer without cloud credentials should still be able to run offline unit tests and runnability checks cleanly.
- **Respect user environment variables:** Always use `os.environ.setdefault()` or `.get()` instead of hardcoded assignments that overwrite user `.env` values.
- **Clean signal in logs:** Always provide exact terminal commands and reproduction snippets in the Friction Log. A friction log without reproduction steps is an opinion, not an audit.
