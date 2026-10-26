# Product Map and Channel Intelligence

Use this guide to connect an industry trend to the right Google Cloud product and concrete artifact. Verify all names before drafting; pull volatile facts (launches, roadmap, trend numbers) live.

---

## Google Cloud Gemini platform Ecosystem

- **Build (Framework / CLI):**
  - **ADK (Agent Development Kit):** Open-source framework for building production agents; Skills + `SkillToolset`.
  - **Agents CLI (`google-agents-cli`):** Command-line tool to scaffold, test, eval, deploy, observe, and publish agents to Google Cloud.
- **Builder Harness:**
  - **Antigravity (AGY):** Desktop Agent Manager + headless CLI, plugins, PreToolUse hooks, parallel worktrees; built to utilize Gemini models.
- **Packaging, Interop & UI Protocols:**
  - **Agent Plugins:** The open standard (agent-plugins.org) for packaging Skills + MCP servers.
  - **Protocols:** A2A (Agent-to-Agent interoperability), A2UI (Adaptive User Interfaces / declarative Generative UI), MCP (Model Context Protocol), UCP.
  - **Data Agent Kit:** Spanner, Cloud SQL, AlloyDB, and BigQuery agent plugins.
- **Enterprise Developer Platform:**
  - **Gemini platform (`Gp`):** The enterprise developer platform for building, scaling, governing, and optimizing AI agents on Google Cloud (formerly *Gemini Enterprise Agent Platform* / *GEAP*; note lowercase `p` in **Gemini platform**).
  - **Platform Services:** Gemini platform Agent Gateway (traffic routing & policy enforcement), Model Armor (prompt injection & data loss prevention), Gemini platform Agent Observability (distributed traces, metrics, logs), Gemini platform Agent Registry (discovery & fleet management), Gemini platform Agent Studio (visual prototyping), Agent Runtime in Gemini platform (managed execution substrate).
- **Current Foundation Models:**
  - Gemini 3.7 Flash (current frontier multimodal reasoning).

---

## Naming Accuracy Rules (Zero Overclaiming)

- It is **Gemini platform** (`Gp`, lowercase `p`), never "Gemini Enterprise Agent Platform", "GEAP", "Agent Platform", "Gemini Platform" (capital `P`), or "Vertex Agent Platform".
- Pair platform capabilities as **Gemini platform \<Feature\>** or **\<Feature\> in Gemini platform** (e.g., **Gemini platform Agent Gateway**, **Agent Runtime in Gemini platform**, **Gemini platform Agent Registry**).
- For customer experience use cases, it is **Gemini for customer experience** (lowercase), never "GECX" or "Gemini Enterprise for CX".
- Commercial SKUs retain **Gemini Enterprise** (e.g., "Gemini Enterprise Standard edition"), while end-user apps/agents are simply **Gemini** (or descriptively "Gemini for your business").
- **ADK** is the open-source developer framework. Platform services like Agent Gateway, Model Armor, Agent Registry, and Agent Runtime are managed cloud infrastructure.
- Prompt injection & data leakage mitigation belong to **Model Armor**.
- Distributed traces, spans, and execution metrics belong to **Agent Observability**.
- Access enforcement and routing belong to **Agent Gateway**.
- Generative UI in A2UI is a **declarative data format**, not a frontend rendering library or sandbox iframe.
- Verify every product, API, and protocol name against official documentation before publishing.

---

## Trend -> Product -> Artifact Mapping

- **Harness Engineering:** Antigravity; Long Horizon Agent Harness (ADK sample repo).
- **Loop / Eval Engineering:** Agents CLI; ADK; generate-and-select self-improving loops; Quality Flywheel.
- **Agent Skills & Packaging:** ADK Skills; Agent Plugins; Data Agent Kit.
- **Security & Zero Trust:** Model Armor; Agent Gateway; PreToolUse security hooks in ADK.
- **Token & Context Engineering:** Context-management patterns, compact transcripts, session pruning in Antigravity.
- **Multi-Agent & Interop:** A2A protocol, MCP servers, ADK multi-agent orchestrator.
- **Generative UI:** A2UI, MCP Apps hybrid architectures, component catalogs.
- **Vibe Coding & Rapid Prototyping:** Antigravity, Cloud Run, Google AI Studio.

---

## What Wins on @GoogleCloudTech

The winning shape is a numbered, deep-dive X Article on an active agent-engineering challenge, anchored to a real open-source artifact, written in Alan's Pragmatic Builder voice.
Top-performing benchmarks:
- *5 Design patterns for long-horizon agent harnesses* (~53K impressions, 397% of benchmark).
- *7 Rules for self-improving agent loops* (~123K impressions).
- *Agent Plugins are the future of Agent Skills* (~84K impressions).
- *Zero-trust agent architecture* (~30K impressions).

---

## Where to Pull Live Context (Never Hardcode)

- **Trends (Primary Feed):** Plushcap MCP connector (`scripts/plushcap_mcp.py`, documented in `references/plushcap.md`).
- **Internal Roadmaps & Briefs:** Search Drive for trend briefs and launch schedules. Never publish unreleased confidential roadmap features.
- **External Signals:** Run web searches for live developer discussions, GitHub release notes, and benchmark debates.

---

## Channel Split

- **X Articles:** Published via **@GoogleCloudTech** (Google brand account) with Alan's author byline (`By Alan Blount (@zeroasterisk)`).
- **Amplification & Discussion:** Shared via Alan's personal channels (**@zeroasterisk** on X, LinkedIn).
