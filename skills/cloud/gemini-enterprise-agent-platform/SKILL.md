---
name: gemini-enterprise-agent-platform
description: >
  Brand naming, product hierarchy, API translations, and service taxonomy for
  Gemini Enterprise and the Agent Platform. Use when you encounter unfamiliar
  product names like UCAIP, GEAP, Agent Engine, Reasoning Engine, Agent Builder,
  Agentspace, GAAB, or need to map between old and new brand names, understand
  which APIs or Concord tables correspond to which product surface, or understand
  the agent service hierarchy (Runtime, Sessions, Memory, Sandbox, Gateway, etc.).
  Don't use for ADK code patterns (use google-agents-cli-adk-code) or deployment
  (use google-agents-cli-deploy).
---

# Gemini Enterprise Agent Platform — Brand & Service Taxonomy

## The Brand Hierarchy (as of Google Cloud Next, April 2026)

```
Gemini Enterprise  (top-level brand)
├── Gemini Enterprise Agent Platform   ← developer/API surface
│   ├── Agent Studio                   ← pro-code IDE
│   ├── Agent Runtime                  ← hosted agent execution
│   ├── Sessions                       ← session state management
│   ├── Memory Bank                    ← long-term agent memory
│   ├── Sandbox                        ← code execution environment
│   ├── Example Store                  ← few-shot example management
│   ├── Feedback                       ← RLHF feedback collection
│   ├── Agent Gateway                  ← authz / safety / routing
│   ├── Agent Identity                 ← cryptographic agent IDs
│   └── Agent Registry                 ← agent registration database
└── Gemini Enterprise app              ← end-user surface (seat-licensed)
    ├── Agent Designer                 ← no-code agent builder
    ├── Agent Gallery                  ← partner agent marketplace
    ├── Inbox                          ← agent task monitoring
    └── Projects                       ← team memory workspace
```

## Critical Name Translations

These are the renames that cause the most confusion. When you see an old name
in configs, table names, or API paths, translate using this table:

| You see | Current brand name | Notes |
|---|---|---|
| `ReasoningEngine` | **Agent Runtime** | API resource name — WILL NOT CHANGE even though brand did |
| `Agent Engine` | **Agent Runtime** | Intermediate brand; still in many Concord table names |
| `reasoningEngines` | **Agent Runtime** | REST path prefix — stable |
| `Vertex AI` | **Gemini Enterprise Agent Platform** | Marketing rename Apr 2026 |
| `UCAIP` | **Agent Platform** (broadly) | Very old; `ucaip_` still in raw GWS log table names |
| `GEAP` | **Gemini Enterprise Agent Platform** | Internal acronym; still used in configs and g3docs |
| `Agent Builder` | **Agent Studio** (pro-code) or **Agent Designer** (no-code) | Context-dependent |
| `Agentspace` | **Gemini Enterprise app** | Full rebrand |
| `GAAB` | **Gemini Enterprise app** backend | In raw log table names (`ucs_gaab_gwslog_*`) |
| `LowcodeAgentService` | **Agent Designer** | Sawmill/console event name |
| `aiplatform` | `aiplatform.googleapis.com` | Stable — the actual service name does not change |

## API Service → Product Mapping

All Agent Platform services are under `aiplatform.googleapis.com` and
use `projects/{project}/locations/{location}/reasoningEngines/{id}/` as
the REST resource path, even for sub-services like Sessions and Memory.

| API Service (in api_method) | Product Surface | is_valuable? |
|---|---|---|
| `ReasoningEngineExecutionService` | Agent Runtime (execution) | Query/Stream/BidiQuery/A2aStream* = TRUE; others = FALSE |
| `ReasoningEngineService` | Agent Runtime (management) | CreateReasoningEngine = TRUE; Get/List/Delete/Update = FALSE |
| `SessionService` | Sessions | AppendEvent/CreateSession/UpdateSession = TRUE; Get/List/Delete = FALSE |
| `MemoryBankService` | Memory Bank | RetrieveMemories/UpdateMemory/GenerateMemories/CreateMemory/IngestEvents/RetrieveProfiles = TRUE; Get/List = FALSE |
| `SandboxEnvironmentExecutionService` | Sandbox | ExecuteSandboxEnvironment/ExecuteCode/BidiExecute = TRUE |
| `SandboxEnvironmentService` | Sandbox (management) | CreateSandboxEnvironment = TRUE; Get/List/Delete/Update/Resume = FALSE |
| `ExampleStoreService` | Example Store | Search/Upsert/Create/Update = TRUE; Get = FALSE |
| `FeedbackService` | Feedback | All = FALSE (not in production IsValuableMethod) |

**Important**: `ResumeSandboxEnvironment` is NOT classified as valuable in the
production definition (from dashboard `_842fa26c`) but is likely an oversight.

## A2A Protocol

A2A (Agent-to-Agent) protocol is a JSON-RPC over HTTP protocol for agent
interoperability. On Agent Runtime it appears as:
- `A2aStreamPostReasoningEngine` — send a message to an agent (valuable)
- `A2aStreamGetReasoningEngine` — receive / agent card fetch (valuable)
- `A2aPostReasoningEngine` — non-streaming send (NOT valuable in production def)
- `A2aGetReasoningEngine` — non-streaming agent card fetch (NOT valuable)

A2A traffic is a small fraction of total Agent Runtime traffic (~21K requests/day
vs ~2.4M total service requests/day as of Jul 2026).

## Four Non-Overlapping Traffic Signal Paths

When analyzing agent traffic, there are four log pipelines that CANNOT be summed:

```
1. ServiceRuntime → daily_agent_engine_usages
   Covers: All Agent Platform service API calls
   User ID: obscured_project_number (Cloud API billing project)

2. Prediction GWS → vertex_userlevel_predictions / adk_aiplatform_usage_daily_v2
   Covers: LLM prediction calls (GenerateContent, Predict, etc.)
   ADK signal: x-goog-api-client header parsed to tool_name array
   User ID: obscured_project_number

3. Agent Gateway GWS → daily_agent_engine_agw_usages
   Covers: Gateway layer; has identity_type, customer_name, gateway flags
   User ID: resource_project_number (raw, not obscured)

4. GAAB GWS → ge_api_usage
   Covers: Gemini Enterprise app (seat-licensed, NOT API-billed)
   User ID: obscured_cloud_principal_id (DIFFERENT from project number)
   CANNOT be joined to paths 1-3 without special mapping
```

## SDK / Framework Detection

The `x-goog-api-client` HTTP header carries SDK information. In Concord tables
it appears as `tool_name` or `client_library_name`. Key values:

| tool_name value | Framework | Notes |
|---|---|---|
| `google-adk` | ADK | Canonical ADK identifier |
| `google_genai_sdk` | Google GenAI SDK | Very high volume (~7.8B req/3d) — NOT agent-specific |
| `langchain-google-vertexai` | LangChain | Also `is_langchain=TRUE` flag in some tables |
| `langchain-google-genai` | LangChain (GenAI) | |
| `langgraph` | LangGraph | |
| `crewai` | CrewAI | |
| `genkit` | Genkit | |
| `antigravity` / `jetski` | Jetski | Google internal framework |
| `pydantic-ai` | Pydantic AI | |
| `firebase` | Firebase MCP | |
| `ag2` / `autogen` | AG2 / AutoGen | |
| `smolagents` | SmolAgents | |
| NULL + language=python | CUSTOM_PYTHON | Best ADK proxy in daily_agent_engine_usages |
| NULL + NULL | UNKNOWN | Direct HTTP, curl, custom stacks |

**ADK attribution caveat**: ADK does NOT reliably set `client_library_name` in
`daily_agent_engine_usages` (serviceruntime path). `CUSTOM_PYTHON` is the best
available proxy there. The correct ADK signal is in `adk_aiplatform_usage_daily_v2`
where `is_adk = TRUE` uses the correctly parsed header array.

## Agent Types (from Agent Registry)

Agents registered in the Agent Registry (`cloud_ai_ds_agents`) have an
`agent_definition` field:

| agent_definition | agent_type | Ownership |
|---|---|---|
| `ADK_AGENT` | ADK | 3P (customer) |
| `A2A_AGENT` + first_party/managed card | A2A_1P | 1P (Google) |
| `A2A_AGENT` + other card | A2A_3P | 3P (customer) |
| `MANAGED_AGENT` | Various managed subtypes | 1P (Google) |
| `LOW_CODE_AGENT` / `AGENT_DESIGNER_AGENT` | LOW_CODE_AGENT_DESIGNER | Mixed |
| `NO_CODE_AGENT` | NO_CODE | Mixed |
| `DIALOGFLOW_AGENT` | DIALOGFLOW | 3P |
| `HTTP_AGENT` | HTTP | 3P |

Managed agent subtypes: DATA_SCIENCE_AGENT, DATA_AGENT, RESEARCH_ASSISTANT_AGENT,
CAMPUS_AGENT, IDEA_GENERATION_AGENT, COSCIENTIST_AGENT, DATA_INSIGHTS_AGENT,
RESEARCH_ASSISTANT_GEM3_AGENT.

## Sources for Staying Current

Brand names and product surfaces change frequently. Authoritative sources:

1. **Release notes** (public BQ table — use standard BigQuery client, not F1):
   ```sql
   SELECT published_at, product_name, release_note_type, description
   FROM `bigquery-public-data.google_cloud_release_notes.release_notes`
   WHERE product_name IN ('Vertex AI', 'Gemini Enterprise Agent Platform',
     'Agent Builder', 'Gemini Enterprise')
   ORDER BY published_at DESC
   LIMIT 100
   ```

2. **Official docs**: https://docs.cloud.google.com/gemini-enterprise-agent-platform

3. **Blog**: https://cloud.google.com/blog/products/ai-machine-learning/
   (filter for "agent" or "Gemini Enterprise")

4. **Recently edited Concord configs** (internal):
   ```bash
   ls -lt /google/src/files/head/depot/google3/cloud/analysis/concord/datamarts/prod/analysis/userlevel/configs/caiis/aiplatform/ | head -20
   ls -lt /google/src/files/head/depot/google3/cloud/analysis/concord/datamarts/prod/service/cloudbi/configs/cloud_ai/ | head -20
   ```

5. **Production dashboard for canonical IsValuableMethod definition**:
   Dashboard `_842fa26c_ea96_4400_8c3b_09d6247a8922` (Agent Engine General Usage)
   contains the production SQL function — always check this before writing
   is_valuable_call logic.

## Key Internal Resources

- `go/agent-metrics-mece` — MECE agent analytics framework with full taxonomy docs
- `go/orcas-rfc-374` — RFC: "Measuring What Matters" (valuable call taxonomy)
- `go/agent-builder-datasite` — Agent Builder DataSite with production dashboards
- `go/geap-cujs` — GEAP Critical User Journey definitions and taxonomy
