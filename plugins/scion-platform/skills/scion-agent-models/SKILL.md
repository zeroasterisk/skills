---
name: scion-agent-models
description: Audit fleet model and Vertex AI region configurations across Scion Hub projects, detect static env overrides (ANTHROPIC_MODEL, CLOUD_ML_REGION) and unpinned fallback drift, and live-switch running agent models. Requires jq and curl.
license: Apache-2.0
compatibility: Requires scion CLI, jq, curl, and bash.
metadata:
  author: ghchinoy
  version: "1.1.0"
---

# Scion Fleet Model Assessment & Live-Switching (`scion-agent-models`)

This skill provides operational procedures, architectural guidelines, and executable scripts for auditing LLM model assignments and Vertex AI region routing across Scion Hub projects, detecting Hub/project override traps (`ANTHROPIC_MODEL`, `defaultModel`, regional `429`s), and live-switching running agent models.

---

## 1. Prerequisites

1. **`scion` CLI installed and authenticated**:
   ```bash
   scion hub auth login --hub-url https://<your-hub-domain>/ --no-browser
   ```
2. **`jq` and `curl` available** in `PATH`.
3. Cached credentials present in `~/.scion/credentials.json`.

---

## 2. Helper Scripts

- [`scripts/hub-model-audit.sh`](scripts/hub-model-audit.sh) — Audits Hub-scoped environment variables (`ANTHROPIC_MODEL`, `CLOUD_ML_REGION`, `GOOGLE_CLOUD_REGION`), global harness configs, project default annotations (`scion.io/default-model`, `scion.io/default-harness-config`), and running agents.
- [`scripts/hub-model-patch.sh`](scripts/hub-model-patch.sh) — Switches models on Scion agents: uses `PATCH /api/v1/agents/{id}` when `phase == "created"`, sends live `/model <model>` commands (`raw: true`) to running Claude Code sessions when `phase == "running"`, and supports `--restart-containers` (`stop` + `start`) so running containers pick up updated Hub/project environment variables (`CLOUD_ML_REGION=global`).

---

## 3. The 5-Tier Model & Region Precedence Architecture

Understanding how Scion resolves models and Vertex AI endpoints prevents accidental fleet-wide overrides and regional `429 RESOURCE_EXHAUSTED` errors:

1. **Container Environment Overrides (Highest Precedence — Common Trap)**:
   - Inside `scion-claude`, `harnesses/claude/provision.py` only sets `ANTHROPIC_MODEL = SCION_MODEL` if `ANTHROPIC_MODEL` is **not** already present in the container environment.
   - **Rule**: Never set a static `ANTHROPIC_MODEL` at `scope=hub` or `scope=project` (`DELETE /api/v1/env/ANTHROPIC_MODEL?scope=hub&scopeId=<hubId>`), or it will override every template and agent model setting.
   - **Vertex AI Region**: Anthropic models (`claude-opus-5-5@default`, `claude-opus-4-8`) require the **`global`** Vertex AI endpoint (`CLOUD_ML_REGION=global`, `GOOGLE_CLOUD_REGION=global`, `GOOGLE_CLOUD_LOCATION=global` with `injectionMode: "always"` at `scope=hub`). Regional endpoints (`us-east5`, `us-central1`) frequently return `429 Quota exceeded`.
2. **Explicit Agent Config (`agent.appliedConfig.model`)**:
   - Passed at creation time (`scion start --model ...`) or inherited from the agent's template (`scion-agent.yaml`).
3. **Project Default Model (`project.annotations["scion.io/default-model"]`)**:
   - **Rule**: Keep project `defaultModel` **empty (`""`)** on multi-tier agent teams! Setting a project-wide `defaultModel` overrides harness defaults for every worker template that leaves `model` unset (e.g. forcing all `developer` or `qa-tester` agents onto Opus).
4. **Template `scion-agent.yaml` (`model` & `default_harness_config`)**:
   - Pin `model: "claude-opus-5-5@default"` and `default_harness_config: "claude"` on `coordinator` (and `eng-manager` if desired), while leaving worker templates unset so they inherit from their harness config.
5. **Harness Config Default (`GET /api/v1/harness-configs`)**:
   - Configure `claude` with `model: "claude-opus-5-5@default"` and `antigravity` with `model: "Gemini 3.8 Flash (Medium)"`.

---

## 4. Core Workflows

### Workflow 1: Fleet Model & Region Audit

```bash
# Full fleet audit (Hub env vars, harness configs, projects, and agents):
./scripts/hub-model-audit.sh --hub https://<your-hub-domain>/

# Audit specific template role across projects (e.g. all coordinators):
./scripts/hub-model-audit.sh --hub https://<your-hub-domain>/ --template coordinator

# Audit specific project:
./scripts/hub-model-audit.sh --hub https://<your-hub-domain>/ --project <project-slug-or-id>

# Programmatic / JSON output:
./scripts/hub-model-audit.sh --hub https://<your-hub-domain>/ --json
```

---

### Workflow 2: Live-Switching Running Agents & Refreshing Container Env Vars

Because `PATCH /api/v1/agents/{id}` only allows `config.model` modifications when `phase == "created"`, running Claude Code agents (`phase == "running"`) must be switched in-place via `POST /api/v1/agents/{id}/message` using `structured_message` with `"raw": true` (`{"structured_message": {"msg": "/model <model-id>", "raw": true}}` followed by `{"structured_message": {"msg": "Enter", "raw": true}}`, or via the CLI `scion message <agent> --project <slug> --raw "/model <model-id>"` + `"Enter"`). Note that top-level `"raw": true` outside `structured_message` is ignored by the Hub API and delivered as a chat message envelope.

**Claude Code Version Gate (`>= 2.1.280` for `claude-opus-5-5`)**:
- Vertex AI rejects `claude-opus-5-5@default` (and the `opus` alias, which resolves to Opus 5 in Claude Code `2.1.270`) with `HTTP 400 claude_code_version_too_old` (`Claude Code 2.1.270 does not support this model; version 2.1.280 or newer is required`) if the `scion-claude` container image has Claude Code `< 2.1.280`.
- Verify the container's Claude Code version with `scion look <agent> --project <slug>`. If the container runs Claude Code `< 2.1.280`, switch the agent to `claude-opus-4-8` (`--model claude-opus-4-8`) until `scion-claude` is rebuilt with Claude Code `>= 2.1.280`.

Furthermore, if you updated Hub or project environment variables (such as setting `CLOUD_ML_REGION=global`), existing Docker containers retain their old `os.Environ()` (`CLOUD_ML_REGION=us-east5`) until recreated via `stop` + `start` (`--restart-containers`), which preserves the workspace and `.claude` conversation (`--resume`).

#### A. Preview Changes (Dry-Run)
```bash
./scripts/hub-model-patch.sh --hub https://<your-hub-domain>/ \
  --template coordinator \
  --model claude-opus-5-5@default \
  --dry-run
```

#### B. Live-Switch a Single Running Coordinator
```bash
./scripts/hub-model-patch.sh --hub https://<your-hub-domain>/ \
  --agent <agent-id> \
  --model claude-opus-5-5@default
```

#### C. Recreate Containers (Pick Up `CLOUD_ML_REGION=global`) & Switch Model Across All Coordinators
```bash
./scripts/hub-model-patch.sh --hub https://<your-hub-domain>/ \
  --all --template coordinator \
  --restart-containers \
  --model claude-opus-5-5@default
```
