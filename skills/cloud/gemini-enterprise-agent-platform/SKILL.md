---
name: gemini-enterprise-agent-platform
description: >
  Brand naming, product hierarchy, API translations, and service taxonomy for
  Gemini Enterprise and the Agent Platform. Use when you encounter unfamiliar
  product names like UCAIP, GEAP, Agent Engine, Reasoning Engine, Agentspace,
  GAAB, CES, or need to map between old and new brand names, understand which
  APIs or Concord tables correspond to which product surface, or understand the
  agent service hierarchy (Runtime, Sessions, Memory, Sandbox, Gateway, etc.).
  Don't use for ADK code patterns (use google-agents-cli-adk-code) or deployment
  (use google-agents-cli-deploy).
---

# Gemini Enterprise — Brand & Service Taxonomy

## THE MOST IMPORTANT RULE

**When in doubt about product naming, ask. Do not guess.**

Brand names have changed frequently and multiple products share similar names
("Agent Studio", "Agent Designer") in different contexts. The API service name
and REST path are the authoritative source for what something actually is.

**"Agent Builder" is a retired brand name, not a specific product.** When you
see it in configs, table names, or docs, treat it as an ambiguous historical
label — do not assume it refers to any current product.

---

## The Three Branches of Gemini Enterprise

These are three distinct product families that share some infrastructure (ADK,
A2A protocol) but have different APIs, user populations, billing, and
telemetry:

```
Gemini Enterprise (top brand)
│
├── 1. Gemini Enterprise Agent Platform   (GEAP)
│      API service: aiplatform.googleapis.com
│      Users: Cloud developers / API-billed projects
│      Console: console.cloud.google.com/agent-platform
│
├── 2. Gemini Enterprise app              (GE App)
│      API: GAAB infrastructure (ucs_gaab_gwslog)
│      Users: Seat-licensed enterprise employees
│      Surface: business.gemini.google / gemini.google.com enterprise
│
└── 3. Gemini Enterprise for Customer Experience  (GE CX / GECX)
       API service: ces.googleapis.com  (google.cloud.ces.v1)
       Users: B2B customers building customer-facing agents
       Lineage: Dialogflow CX / CCAI, now ADK-based
       Console: ces.cloud.google.com
```

---

## Branch 1: Gemini Enterprise Agent Platform (GEAP)

The developer platform. All services under `aiplatform.googleapis.com`.
Everything lives under `projects/{project}/locations/{location}/reasoningEngines/{id}/`
even though the brand name is "Agent Platform" not "Reasoning Engine".

### Products within GEAP

| Current Brand Name | API Service / Resource | Notes |
|---|---|---|
| **Agent Runtime** | `ReasoningEngineExecutionService` | Execution host for ADK agents; API resource is `reasoningEngines` — will not change |
| **Agent Studio** (in GEAP) | Part of `aiplatform` console | Low-code visual builder for building agents in Cloud console; exports to ADK |
| **Sessions** | `SessionService` (under `reasoningEngines.sessions`) | Session state management |
| **Memory Bank** | `MemoryBankService` | Long-term agent memory |
| **Sandbox** | `SandboxEnvironmentService` + `SandboxEnvironmentExecutionService` | Code execution |
| **Example Store** | `ExampleStoreService` | Few-shot examples |
| **Feedback** | `FeedbackService` | RLHF feedback |
| **Agent Gateway** | AGW (separate GWS log path) | Authz/safety/routing layer |
| **Agent Identity** | Cryptographic IDs | Per-agent verifiable identity |
| **Agent Registry** | Spanner-backed (`cloud_ai_ds_agents` in CloudBI) | Central catalog of all registered agents |
| **Agent Simulation** | Part of `aiplatform` | Pre-production testing |
| **Agent Evaluation** | Part of `aiplatform` | Production quality scoring |
| **Agent Observability** | Part of `aiplatform` | Execution traces, reasoning visibility |

### Agent Designer in GEAP context

The Agent Registry (`cloud_ai_ds_agents`) has an `agent_definition` type of
`AGENT_DESIGNER_AGENT` and `LOW_CODE_AGENT`. These appear to be related to
a visual/low-code agent building experience within GEAP. Whether this is the
same product as "Agent Designer" in GE App is **unclear** — the API path is
the authority and needs verification. When this matters, check with alanblount.

---

## Branch 2: Gemini Enterprise App (GE App)

The knowledge-worker surface. Seat-licensed, not API-billed.
**Different user population from GEAP — cannot naively join telemetry.**

| Product | Description |
|---|---|
| **Agent Designer** (in GE App) | No-code agent builder for knowledge workers ("drag and drop") |
| **Agent Gallery** | Marketplace for discovering partner agents |
| **Inbox** | Central hub for managing long-running agents |
| **Projects** | Team memory workspace |
| **Canvas** | Collaborative editing with AI |

**Telemetry**: `ge_api_usage` table, `ucs_gaab_gwslog_stats` raw logs.
User identifier: `obscured_cloud_principal_id` (NOT `obscured_project_number`).

---

## Branch 3: Gemini Enterprise for Customer Experience (GE CX)

**Lineage**: Dialogflow CX → CCAI → Customer Engagement Suite → GE CX.
Now ADK-based but its own distinct service.
**API service**: `ces.googleapis.com` (package: `google.cloud.ces.v1`)
**NOT** part of `aiplatform.googleapis.com`.

| Product | Description |
|---|---|
| **CX Agent Studio** | Drag-drop canvas for building customer-facing agents; deploys to voice/chat/web channels |
| **Agent Assist** | Real-time coaching for human customer service representatives |
| **CX Insights** | Conversation analytics (Customer Experience Insights) |
| **Shopping agent** | E-commerce agent for product discovery to checkout |
| **AI Commerce Search** | Personalized search for retail/restaurant |
| **Food Ordering agent** | Multilingual voice ordering for restaurants |

**Why it's a "cousin" not a "child" of GEAP**: Shares ADK and A2A protocol
support, but has its own API, billing, console (`ces.cloud.google.com`),
telemetry path, and product management team. It's oriented toward B2B customers
building customer-facing experiences (retail, restaurants, contact centers),
whereas GEAP is oriented toward developers building internal or API-exposed agents.

---

## Complete Rename Chain (from release notes BQ table)

Source: `bigquery-public-data.google_cloud_release_notes.release_notes`

### GEAP / Vertex AI lineage
```
UCAIP (very old)
  → Vertex AI (product name ~2020–2026, release notes end Mar 2026)
  → Generative AI on Vertex AI (release notes for AI/agent features, end May 2026)
  → Gemini Enterprise Agent Platform (Apr 2026 onwards, current)
```

### Agent Engine / Reasoning Engine
```
LangChain on Vertex AI (renamed Mar 2025)
  → Vertex AI Agent Engine (Mar 2025 → Apr 2026)
  → Agent Runtime (Apr 2026 rename, part of GEAP)
API resource: reasoningEngines.* — STABLE, will not change with brand
```

### Agent Builder → the most confusing chain
```
Vertex AI Agent Builder (original product = search/retrieval, pre-Apr 2025)
  → renamed to AI Applications (Apr 2025)
  → renamed to Vertex AI Search (Oct 2025)
  → renamed to Agent Search (Apr 2026)
  (Note: API endpoints unchanged throughout)

Simultaneously in Apr 2025: the label "Vertex AI Agent Builder" was repurposed
in docs to refer to a suite of agent-building features (ADK, Agent Garden, etc.)
in Vertex AI. This caused massive confusion — the name pointed at two different things.
By Apr 2026, this disambiguation resolved: GEAP is the platform, Agent Search
is the search product.
```

### GE App / Agentspace
```
Agentspace (early name)
  → Gemini Enterprise app (current)
  → release notes appear under product name "Gemini Enterprise"
Agent Designer lives in "Gemini Enterprise" release notes = GE App context (confirmed)
```

### CX / Dialogflow lineage
```
Dialogflow (2017→present, still active for CX)
  → CCAI / Contact Center AI
  → Customer Engagement Suite (CES)
  → Gemini Enterprise for Customer Experience (GE CX)
CX Agent Studio: GA Feb 2026, release notes appear as "CX Agent Studio" product name
```

### Critical Name Translations

| You see | Meaning | Stable? |
|---|---|---|
| `ReasoningEngine` / `reasoningEngines` | Agent Runtime (GEAP) | ✅ API resource name is stable |
| `Agent Engine` | Agent Runtime (GEAP) | Old brand, still in Concord table names |
| `Vertex AI` | GEAP (pre-Apr 2026) | Retired from release notes Mar 2026 |
| `Generative AI on Vertex AI` | GEAP features | Retired from release notes May 2026 |
| `UCAIP` | Agent Platform broadly | Very old, still in raw log table names |
| `GEAP` | Gemini Enterprise Agent Platform | Internal acronym, still used in configs |
| `Agent Builder` | **Ambiguous retired label** | Was: search product. Then: suite label. Now: neither specifically |
| `AI Applications` | Now: Vertex AI Search → Agent Search | Search/retrieval product, NOT agents |
| `Agentspace` | Gemini Enterprise app | Rebrand to GE App |
| `GAAB` | GE App backend | `ucs_gaab_gwslog_*` raw log table names |
| `CCAI` | GE CX lineage | Contact Center AI predecessor |
| `CES` | GE CX API service | `ces.googleapis.com` |
| `aiplatform` | `aiplatform.googleapis.com` | ✅ Stable — service name does not change |
| `ces` | `ces.googleapis.com` | ✅ Stable GE CX service name |
| `Agent Studio` (in GEAP) | Low-code builder in Cloud console for GEAP | Different from CX Agent Studio |
| `CX Agent Studio` | GE CX drag-drop canvas (GA Feb 2026) | `ces.googleapis.com` service |
| `Agent Designer` | No-code for GE App knowledge workers | Release notes confirm this is GE App, NOT GEAP |
| `Agent Designer agent` / `AGENT_DESIGNER_AGENT` | In GEAP Agent Registry | May be agents *built with* GE App Agent Designer and *registered* in GEAP — relationship TBD |
| `LowcodeAgentService` | Sawmill console event | Likely Agent Designer in GE App; exact mapping unconfirmed |

---

## Four Non-Overlapping Traffic Signal Paths

When analyzing agent traffic, these are four physically separate log pipelines.
They cover different populations and CANNOT be summed:

```
1. ServiceRuntime → daily_agent_engine_usages
   Covers: GEAP Agent Platform service calls (aiplatform.googleapis.com)
   Users: API-billed Cloud projects

2. Prediction GWS → vertex_userlevel_predictions / adk_aiplatform_usage_daily_v2
   Covers: LLM predictions from any framework using Gemini
   ADK signal: x-goog-api-client header parsed to tool_name array

3. Agent Gateway GWS → daily_agent_engine_agw_usages
   Covers: GEAP gateway layer; has identity_type, customer geography

4. GAAB GWS → ge_api_usage
   Covers: GE App (seat-licensed, NOT API-billed)
   Users: obscured_cloud_principal_id ≠ obscured_project_number

5. CES → (no confirmed Concord table yet)
   Covers: GE CX / CX Agent Studio traffic
   Service: ces.googleapis.com; different billing/telemetry path from GEAP
```

---

## SDK / Framework Detection

The `x-goog-api-client` HTTP header. In Concord: `tool_name` / `client_library_name`.

| tool_name | Framework | Notes |
|---|---|---|
| `google-adk` | ADK | Canonical ADK identifier |
| `google_genai_sdk` | Google GenAI SDK | Very high volume; NOT agent-specific — covers all Gemini SDK usage |
| `langchain-google-vertexai` | LangChain | `is_langchain=TRUE` in some tables |
| `langgraph` | LangGraph | |
| `crewai` | CrewAI | |
| `genkit` | Genkit | |
| `antigravity` / `jetski` | Jetski | Google internal |
| `pydantic-ai` | Pydantic AI | |
| `firebase` | Firebase MCP | |
| `ag2` / `autogen` | AG2 / AutoGen | |
| NULL + language=python | CUSTOM_PYTHON | Best ADK proxy in `daily_agent_engine_usages` (ADK often doesn't set this field) |
| NULL + NULL | UNKNOWN | Direct HTTP / curl / custom stacks |

---

## Release Notes Script (Primary Research Tool)

A self-contained script is bundled at `scripts/release_notes.py` relative to this skill.
Run it directly — it self-installs its only dependency (`google-cloud-bigquery`) via `uv`.

```bash
# From the skill directory:
./scripts/release_notes.py                        # recent agent/Gemini/Vertex notes
./scripts/release_notes.py products              # all product names + activity timeline
./scripts/release_notes.py renames               # all rename/rebrand announcements
./scripts/release_notes.py product "CX Agent"    # history for one product (partial match)
./scripts/release_notes.py search "agent builder" # search description text
./scripts/release_notes.py --since 2024-01-01    # override date range
./scripts/release_notes.py --project my-project  # override GCP project for billing
```

Output is compact TOON-style: `published_at | product_name | type` then description.
Each command prints `hint:` lines suggesting logical next steps.

If the script isn't on PATH, find it relative to this SKILL.md using the skill's base directory.

## Querying Release Notes (Manual / Fallback)

The public BigQuery table `bigquery-public-data.google_cloud_release_notes.release_notes`
is the most reliable source for product renames, GA announcements, and deprecations.
Use it to disambiguate product names or trace rename chains.

**Requires standard BigQuery client, NOT F1/PLX** (F1 can't access public BQ datasets):

```bash
uv run --with google-cloud-bigquery python3 -c "
from google.cloud import bigquery
import re
client = bigquery.Client(project='alanblount-sandbox')
query = '''
SELECT published_at, product_name, release_note_type,
  REGEXP_REPLACE(description, r'<[^>]+>', '') AS description
FROM \`bigquery-public-data.google_cloud_release_notes.release_notes\`
WHERE (LOWER(description) LIKE \"%renamed%\" OR LOWER(description) LIKE \"%agent builder%\")
  AND LOWER(product_name) LIKE \"%agent%\"
ORDER BY published_at DESC LIMIT 20
'''
for row in client.query(query).result():
    print(f'{row.published_at} | {row.product_name}')
    print(f'  {row.description[:250]}')
    print()
"
```

**Useful query patterns:**
- Find all product names: `SELECT DISTINCT product_name, COUNT(*) as c, MAX(published_at) as last FROM ... GROUP BY 1 ORDER BY last DESC`
- Find renames: `WHERE LOWER(description) LIKE '%renamed%' OR LOWER(description) LIKE '%now called%'`
- Find a specific product history: `WHERE product_name = 'CX Agent Studio' ORDER BY published_at`
- Find when a product name was last active: `SELECT MAX(published_at) FROM ... WHERE product_name = 'Vertex AI'`

## Sources for Staying Current

Brand names change. Always verify before asserting.

1. **Official docs**:
   - GEAP: `https://docs.cloud.google.com/gemini-enterprise-agent-platform`
   - GE CX: `https://docs.cloud.google.com/gemini-enterprise-cx`
   - GE App: `https://cloud.google.com/gemini-enterprise`

2. **Release notes** (public BQ — requires standard BigQuery client, not F1/PLX):
   ```sql
   SELECT published_at, product_name, release_note_type, description
   FROM `bigquery-public-data.google_cloud_release_notes.release_notes`
   WHERE product_name IN ('Vertex AI', 'Gemini Enterprise Agent Platform',
     'Gemini Enterprise', 'Dialogflow CX', 'Contact Center AI')
   ORDER BY published_at DESC LIMIT 100
   ```

3. **Recently edited Concord configs** (internal):
   ```bash
   ls -lt /google/src/files/head/depot/google3/cloud/analysis/concord/datamarts/prod/analysis/userlevel/configs/caiis/aiplatform/ | head -20
   ```

4. **Internal taxonomy docs**: `go/agent-metrics-mece` → `g3doc/taxonomy.md`

5. **When uncertain**: Ask alanblount. API paths are the authority.
