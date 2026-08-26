---
name: skills-to-plugins
description: Audit, author, migrate, and lint Agent Skills repositories into Agent Plugins v1.0.0 specification packages. Resolves frontmatter conformance debt, groups co-dependent skills, generates plugin.json and marketplace manifests, and enforces spec containment rules. Use when converting a flat skills repo to plugins, creating a new plugin, or linting plugin conformance.
license: Apache-2.0
compatibility: Requires git, python3, and POSIX shell.
metadata:
  author: ghchinoy
  version: "1.1.0"
---

# Skills to Plugins (`skills-to-plugins`)

This skill provides an expert workflow for **migrating** legacy flat skills repositories into [Agent Plugins v1.0.0 Specification](https://github.com/agentplugins/agent-plugins-spec/blob/main/spec/1.0.0.md) packages, **authoring** new plugins from scratch, and **linting** plugins for ongoing spec conformance.

## Canonical Specifications

- **Agent Plugins Specification:** [agentplugins/agent-plugins-spec](https://github.com/agentplugins/agent-plugins-spec) (Normative Text: [spec/1.0.0.md](https://github.com/agentplugins/agent-plugins-spec/blob/main/spec/1.0.0.md))
- **Agent Skills Specification:** [agentskills.io/specification.md](https://agentskills.io/specification.md)
- **Reference Summary:** See [`references/spec-summary.md`](references/spec-summary.md) for a condensed lookup table of normative rules and schema boundaries.

## Reference & Asset Files (Progressive Disclosure)

- [`references/spec-summary.md`](references/spec-summary.md) — Normative reference for Agent Plugins v1.0.0 and Agent Skills spec constraints.
- [`references/discovery-compatibility.md`](references/discovery-compatibility.md) — Detailed analysis of `npx skills`, `gemini skills`, and `agy` discovery algorithms and `.claude-plugin/marketplace.json` indexing.
- [`references/migration-playbook.md`](references/migration-playbook.md) — Step-by-step phased migration guide (Phases 0 through 5).
- [`references/conformance-debt-catalog.md`](references/conformance-debt-catalog.md) — Symptom and resolution lookup for common skills frontmatter and path anti-patterns.
- [`scripts/audit-conformance.sh`](scripts/audit-conformance.sh) — Read-only debt auditor that scans a repository for frontmatter issues, oversized descriptions, non-executable scripts, and parent-relative link dependencies.
- [`scripts/validate-plugins.sh`](scripts/validate-plugins.sh) — Spec validator enforcing `$schema` URLs, name↔directory matches, description limits ($\le 1024$), script executable bits, and marketplace JSON syntax.
- [`assets/plugin.json.template`](assets/plugin.json.template) — Template for `plugin.json` package manifest.
- [`assets/mcp.json.template`](assets/mcp.json.template) — Template for `mcp.json` server definitions.
- [`assets/marketplace.json.template`](assets/marketplace.json.template) — Template for `.claude-plugin/marketplace.json`.

## Modes

### Mode 1: Audit an Existing Repository (Read-Only)

Execute a comprehensive, non-destructive audit of an existing skills repository before planning a migration.

1. Run the audit script from the repository root:
   ```bash
   scripts/audit-conformance.sh
   ```
2. Read [`references/conformance-debt-catalog.md`](references/conformance-debt-catalog.md) to classify every detected debt item (missing frontmatter, oversized descriptions, non-executable scripts, un-nested top-level `version:` fields).
3. Analyze parent-relative links (e.g. `../sibling/SKILL.md`) to identify co-dependent orchestrator and sub-skills that belong in the same plugin bundle.
4. Present an **Audit & Grouping Proposal** table to the user listing:
   - Conformance debt items to resolve.
   - Proposed thematic plugin groupings (`plugins/<plugin-name>/skills/<skill-name>`).
   - Confirmation prompt before proceeding to Mode 2.

### Mode 2: Migrate Repository to Agent Plugins v1.0.0

*Prerequisite:* Mode 1 audit completed and user approved the grouping proposal.

Execute the migration in strict phase order as detailed in [`references/migration-playbook.md`](references/migration-playbook.md):

1. **Phase 0 (Hygiene):** Add untracked machine-local tooling directories to `.gitignore` and confirm no symlinks escape the repository root.
2. **Phase 1 (Conformance Debt):** Resolve all frontmatter issues, truncate descriptions > 1024 characters, move `version:` under `metadata:`, add `license: Apache-2.0`, `chmod +x` scripts, and move static assets from `references/` to `assets/`.
3. **Phase 2 (Directory Restructure):** Execute directory moves into `plugins/<plugin>/skills/<skill>` using `git mv` to preserve commit history.
4. **Phase 3 (Manifests):** Generate `plugins/<plugin>/plugin.json` for each plugin and `.claude-plugin/marketplace.json` at root using templates in `assets/`.
5. **Phase 4 (Validation):** Run `scripts/validate-plugins.sh` and verify 0 errors.

### Mode 3: Author a New Plugin

Create a new conformant plugin package inside an existing or new repository.

1. Choose a spec-valid plugin name (`^[a-z0-9](?:[a-z0-9.-]*[a-z0-9])?$`).
2. Create directory structure `plugins/<plugin-name>/skills/<skill-name>/`.
3. Copy [`assets/plugin.json.template`](assets/plugin.json.template) to `plugins/<plugin-name>/plugin.json` and fill in `$schema`, `name`, `version`, and metadata.
4. Create `plugins/<plugin-name>/skills/<skill-name>/SKILL.md` with valid frontmatter (`name`, `description` $\le 1024$, `license`).
5. Update `.claude-plugin/marketplace.json` to include the new plugin and skill paths.
6. Validate with `scripts/validate-plugins.sh`.

### Mode 4: Lint Ongoing Conformance

Verify ongoing spec compliance for CI/CD or local pre-commit checks.

1. Run `scripts/validate-plugins.sh` locally or in GitHub Actions (`.github/workflows/validate.yml`).
2. Fix any flagged issues: schema URL mismatches, frontmatter description overruns (> 1024 chars), or un-indexed marketplace entries.

## Guiding Principles

1. **Strict Containment (§4.1):** Symlinks or relative paths escaping the plugin root violate spec §4.1 containment. Never create symlink farms pointing outside a plugin.
2. **Cross-Skill Coupling Detection:** Parent-relative links (`../`) inside `SKILL.md` indicate co-dependent skills that MUST be packaged together inside the same plugin root so links resolve legally.
3. **Phase Ordering:** Always resolve frontmatter and license debt *before* running `git mv` so history records clean directory renames without noisy content diffs.
4. **Canonical Spec Verification:** Always verify specification questions against canonical sources ([agentplugins/agent-plugins-spec](https://github.com/agentplugins/agent-plugins-spec) and [agentskills.io/specification.md](https://agentskills.io/specification.md)) rather than relying solely on local summary distillations.
