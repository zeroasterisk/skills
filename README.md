# Agent Skills & Plugins

> **⚠️ Personal Hobby Project** — This is an independent, personal project by [Alan Blount](https://github.com/zeroasterisk). It is **not affiliated with, endorsed by, or supported by any employer, company, or organization**. No warranty; use at your own risk.

[![Validate Plugins and Skills](https://github.com/zeroasterisk/skills/actions/workflows/validate.yml/badge.svg)](https://github.com/zeroasterisk/skills/actions/workflows/validate.yml)
[![Sync Upstream Plugins](https://github.com/zeroasterisk/skills/actions/workflows/sync-upstream.yml/badge.svg)](https://github.com/zeroasterisk/skills/actions/workflows/sync-upstream.yml)
[![License](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](LICENSE)

Reusable agent skills and modular packages adhering to the [Agent Plugins Specification v1.0.0](https://agent-plugins.org) and [Agent Skills Specification](https://agentskills.io). Compatible with Antigravity (`agy`), Jetski, Claude Plugin Marketplace, OpenClaw, Gemini CLI, and `npx skills`.

---

## Repository Architecture

The repository is structured into modular **Agent Plugins** (`plugins/<plugin-name>/`), each containing a `plugin.json` package manifest, structured `skills/<skill-name>/`, and indexed via `.claude-plugin/marketplace.json`.

```
skills/
├── .claude-plugin/
│   └── marketplace.json          # Claude Plugin Marketplace catalog
├── plugins/
│   ├── <plugin-name>/
│   │   ├── plugin.json           # Agent Plugins v1.0.0 package manifest
│   │   └── skills/
│   │       └── <skill-name>/
│   │           ├── SKILL.md      # Normative instructions & YAML frontmatter
│   │           ├── references/   # Deep-dive documentation (progressive disclosure)
│   │           ├── scripts/      # Deterministic, executable automation (+x)
│   │           └── assets/       # Static templates and boilerplate
├── scripts/
│   ├── validate-plugins.sh       # Conformance validator (manifests, frontmatter, scripts)
│   ├── sync-upstream-plugins.py  # Synchronizer for upstream plugins from ghchinoy/agent-skills
│   ├── sync-upstream-plugins.sh  # Shell wrapper for upstream synchronization
│   └── audit-conformance.sh      # Read-only conformance debt scanner
├── registry.toml                 # Source declarations + federation overrides
├── sync.py                       # Reconciles registry → agent configs & ARD catalogs
└── ai-catalog.json               # ARD v1.0 catalog of resolved skills
```

---

## Plugin Catalog

### Personal Plugins (`zeroasterisk`)

| Plugin | Version | Description | Included Skills |
| :--- | :--- | :--- | :--- |
| **`writing-and-editorial`** | `1.0.0` | Authoring, voice matching, style refinement, and anti-AI humanization tools for technical writing and social content. | `alan-writing-style`<br>`googlecloudtech-x-article`<br>`humanizer` |
| **`visual-explainers`** | `1.1.0` | Tools and quality evaluation rubrics for architecture diagrams, terminal animations, YouTube/social thumbnails, and mathematical explainer videos. | `diagram-design`<br>`asciinema-explainer-walkthroughs`<br>`youtube-thumbnail-designer`<br>`manim-video-quality` |
| **`frontend-engineering`** | `1.0.0` | Full-stack UI development workflows, React component isolation with Storybook, CUJ capturing, and product intent refinement. | `ui-developer`<br>`storybook`<br>`cuj-screenshots`<br>`intent-refinement` |
| **`software-craft`** | `1.0.0` | Software engineering discipline, systematic debugging, Elixir best practices, secure web guidelines, and agent skill authoring. | `engineering-discipline`<br>`elixir-best-practices`<br>`mandatory-secure-web-skills`<br>`skill-creator` |
| **`cloud-and-workplace`** | `1.0.0` | Executive inbox/calendar chief-of-staff triage and open-source working group NotebookLM synchronization. | `chief-of-staff-triage`<br>`aaif-notebooklm-sync` |
| **`developer-intel`** | `1.0.0` | Developer trend synthesis combining Plushcap MCP engineering blog data with Good AI List repository velocity. | `developer-trends-intel` |
| **`developer-friction-reviewer`** | `1.0.0` | Persona-based developer friction reviews and automated audit loops across recipes, tools, and onboarding flows. | `developer-friction-reviewer` |

### Consumed Upstream Plugins (`ghchinoy/agent-skills` & `voodootikigod/adlc`)

Mirrored and synchronized from [Hussain Chinoy's agent-skills](https://github.com/ghchinoy/agent-skills) and [Chris Williams's ADLC toolkit](https://github.com/voodootikigod/adlc):

| Plugin | Version | Description | Included Skills |
| :--- | :--- | :--- | :--- |
| **`adlc`** | `1.11.0` | Agentic Development Lifecycle (ADLC) toolkit integration: phase router, rail-guard hooks, slash commands, and prosecutor agents. | `adlc`<br>`adlc-doctrine`<br>`adlc-prosecutor`<br>`adlc-self-orchestrate` |
| **`agent-aware-cli`** | `1.0.0` | Best practices and architectural guidelines for CLI tools optimized for both human users and AI coding agents. | `agent-aware-cli` |
| **`agent-plugin-authoring`**| `1.1.0` | Authoring, migration, and linting tools for packaging Agent Skills into Agent Plugins v1.0.0 spec packages. | `skills-to-plugins` |
| **`ai-pop`** | `1.0.0` | Virtual music artist production suite: lore planning, audio synthesis, visual design, player compilation, and deployment. | `ai-pop-producer`<br>`ai-pop-concept-planner`<br>`ai-pop-audio-synthesizer`<br>`ai-pop-visual-designer`<br>`ai-pop-compiler`<br>`ai-pop-publisher` |
| **`automation-governance`** | `1.0.0` | Framework and tooling for evaluating workflow automation readiness based on Google DeepMind research. | `automation-readiness` |
| **`beads-workflow`** | `1.9.1` | Tools and workflows for the beads (`bd`) Dolt-powered issue tracking ecosystem (diagnostics, repair, plan grilling). | `bd-dolt-troubleshooter`<br>`grill-with-beads` |
| **`gcp-management`** | `1.0.0` | Google Cloud Platform & Firebase project assessment, itemized BigQuery spend analysis, quota governance, and consolidation. | `gcp-project-assessment`<br>`gcp-quota-governance`<br>`gcp-project-consolidation` |
| **`macos-hig`** | `1.1.0` | macOS Human Interface Guidelines assistance and code reviewers for layout, interactions, and HIG compliance. | `macos-hig-layout`<br>`macos-hig-interaction`<br>`macos-hig-reviewer` |
| **`mcp-security`** | `1.0.0` | Model Context Protocol (MCP) security auditing for RCE, STDIO injection, and supply chain vulnerabilities. | `mcp-auditor` |
| **`okf-authoring`** | `1.0.0` | Tool-agnostic authoring and validation for conformant Open Knowledge Format (OKF) v0.2 knowledge bundles. | `okf-author`<br>`okf-validate` |
| **`repo-authoring`** | `1.0.0` | Repository management skills for technical writing, README generation, changelog curation, and commit recaps. | `make-readme`<br>`technical-post-editorial`<br>`repository-change-recap`<br>`changelog-manager` |

---

## Upstream Synchronization

Upstream plugins from `ghchinoy/agent-skills` are maintained in `plugins/` and kept continuously in sync.

### Manual Sync via CLI

Run the synchronizer to fetch upstream updates, update vendored plugins, refresh `.claude-plugin/marketplace.json`, and run validation:

```bash
# Full sync, marketplace refresh, and validation
./scripts/sync-upstream-plugins.sh

# Dry-run to preview upstream changes
./scripts/sync-upstream-plugins.sh --dry-run
```

### Automated Sync via GitHub Actions

The repository includes [`.github/workflows/sync-upstream.yml`](.github/workflows/sync-upstream.yml), which:
- Runs automatically on a weekly schedule (Mondays at 12:00 UTC) and on manual dispatch.
- Checks `ghchinoy/agent-skills` for upstream changes.
- Automatically opens a Pull Request with updated plugins and validated manifests.

---

## Validation & Conformance

Run local validation across all plugin manifests (`plugin.json`), skill frontmatter (`SKILL.md`), executable script bits, and marketplace indexing:

```bash
./scripts/validate-plugins.sh
```

To audit conformance debt on new or modified skills:

```bash
./scripts/audit-conformance.sh
```

---

## Installation & Usage

### Installing via Open Agent Skills CLI (`npx skills`)

The [Open Agent Skills CLI](https://github.com/vercel-labs/skills) works natively with this repository via `.claude-plugin/marketplace.json`:

```bash
# List available skills in the repository
npx skills add zeroasterisk/skills --list

# Install a specific skill (e.g., alan-writing-style or mcp-auditor)
npx skills add zeroasterisk/skills --skill alan-writing-style
npx skills add zeroasterisk/skills --skill mcp-auditor

# Install all skills to your project
npx skills add zeroasterisk/skills --all
```

### Antigravity (`agy`) / Jetski

`agy` (Antigravity) and `jetski` automatically discover skills placed in your customization root (`~/.gemini/config/skills/` or project `.agents/skills/`):

```bash
# Link all skills into ~/.gemini/config/skills via sync.py
./sync.py

# Or manually link a single skill
ln -s "$(pwd)/plugins/writing-and-editorial/skills/alan-writing-style" ~/.gemini/config/skills/
```

### Gemini CLI

```bash
# Install a specific skill directly from GitHub
gemini skills install zeroasterisk/skills --path plugins/software-craft/skills/engineering-discipline

# Link local skill
gemini skills link ./plugins/writing-and-editorial/skills/alan-writing-style
```

---

## Registry Federation (`sync.py`)

`registry.toml` acts as the single source of truth for federated skills across machines. `sync.py` reads the registry and:
1. Auto-discovers all `SKILL.md` files across declared sources.
2. Updates `cloudcode.json` `skills.paths` for CloudCode agents.
3. Manages symlinks in `~/.gemini/config/skills/` for active Gemini / Jetski / Antigravity agents.
4. Generates ARD-compliant [Agentic Resource Discovery](https://agenticresourcediscovery.org/) catalogs (`ai-catalog.json`).

```bash
./sync.py               # Reconcile registry and generate catalogs
./sync.py --dry-run     # Preview actions without writing
./sync.py --verbose     # Show all skipped and included skills
```

---

## Scion Templates

Agent templates for [Scion](https://scion.ai) — each directory contains a `scion-agent.yaml`, system prompt, and agent instructions:

| Template | Description |
| :--- | :--- |
| [elixir-dev](./templates/elixir-dev/) | Elixir SWE agent with Postgres, SQLite, Redis — for AgentMsg and a2a-elixir development |
| [project-lead](./templates/project-lead/) | Project lead — sub-coordinator for sustained project work, delegates to SWE/verifier agents |
| [researcher](./templates/researcher/) | Research agent — investigates questions, reads docs, analyzes code, produces findings |
| [swe](./templates/swe/) | Senior software engineer — implements features, fixes bugs, writes tests |
| [verifier](./templates/verifier/) | Skeptical verifier — independently checks that work actually produces correct outcomes |

---

## License

This repository is licensed under the [Apache License 2.0](LICENSE).
