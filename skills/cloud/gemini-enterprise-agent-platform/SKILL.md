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

## Critical Name Translations

| You see this in configs/APIs/docs | Meaning | Notes |
|---|---|---|
| `ReasoningEngine` | Agent Runtime (GEAP) | API resource — will not change even though brand did |
| `Agent Engine` | Agent Runtime (GEAP) | Intermediate brand; still in Concord table names |
| `reasoningEngines` | Agent Runtime (GEAP) | REST resource path prefix — stable |
| `Vertex AI` | Gemini Enterprise Agent Platform | Marketing rename Apr 2026 |
| `UCAIP` | Agent Platform broadly | Very old; still in raw GWS log table names |
| `GEAP` | Gemini Enterprise Agent Platform | Internal acronym; still used in configs |
| `Agent Builder` | **Retired brand name** | Ambiguous — do not assume it means anything specific |
| `Agentspace` | Gemini Enterprise app | Full rebrand of the GE App product |
| `GAAB` | Gemini Enterprise app backend | In raw log table names (`ucs_gaab_gwslog_*`) |
| `LowcodeAgentService` | Unclear — likely Agent Designer | Sawmill/console event name; exact mapping unconfirmed |
| `CCAI` | GE CX lineage | Contact Center AI — predecessor brand |
| `CES` | GE CX API service | Customer Engagement Suite; `ces.googleapis.com` |
| `aiplatform` | `aiplatform.googleapis.com` | Stable — the service name does not change |
| `ces` | `ces.googleapis.com` | GE CX service name — stable |
| `Agent Studio` (GEAP) | Low-code builder in Cloud console | Different from CX Agent Studio |
| `CX Agent Studio` | GE CX drag-drop canvas | Different from Agent Studio in GEAP |
| `Agent Designer` (GE App) | No-code for knowledge workers | May or may not be same as GEAP `AGENT_DESIGNER_AGENT` |

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
