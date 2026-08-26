# Conformance Debt Catalog

This catalog documents common conformance anti-patterns found in legacy skills repositories and their exact resolution under the [Agent Plugins Specification v1.0.0](https://github.com/agentplugins/agent-plugins-spec/blob/main/spec/1.0.0.md) and [Agent Skills Specification](https://agentskills.io/specification.md).

| Anti-Pattern / Debt Item | Spec Impact | Root Cause | Resolution |
|---|---|---|---|
| **Missing YAML frontmatter** in `SKILL.md` | **Fatal** (§7.1) | File starts directly with `# Heading` without `---` frontmatter block | Add `---` block containing required `name` and `description` fields. |
| **Description exceeds 1024 characters** | **Fatal** (Agent Skills Spec) | Long prose pasted into frontmatter `description` | Shorten description to < 1024 chars while retaining core trigger keywords and use-case phrases. |
| **Top-level `version:` in `SKILL.md`** | Non-standard field | `version` is not a top-level Agent Skills frontmatter field | Move to `metadata:\n  version: "1.0.0"`. |
| **Name mismatch** (`name` $\neq$ directory name) | Validation failure | Directory renamed without updating frontmatter `name` | Synchronize frontmatter `name` to match parent directory name exactly. |
| **Scripts not executable** (`0644` mode) | Execution failure | Helper scripts created without `chmod +x` | Run `chmod +x scripts/*`. |
| **Symlink escaping repo root** | **Fatal** (§4.1) | Machine-local symlink in untracked folder points to `~/.config/...` | Delete or gitignore untracked folder containing external symlinks. |
| **`../` links escaping plugin root** | **Fatal** (§4.1) | Orchestrator skill links to sibling skill in a different plugin root | Move co-dependent orchestrator and sub-skills into the *same* plugin. |
| **`references/` used for project templates** | Semantic confusion | Config files (e.g. `.swiftlint.yml`) placed in `references/` | Move copy-into-project templates to `assets/`. |
| **Stray root output directories** | Unorganized repository | Example output reports placed at repo root | Move example outputs into `references/` under the relevant skill. |
| **Missing root `LICENSE`** | Compliance risk | Repository distributed without license file | Add root `LICENSE` (Apache-2.0 recommended) and `license:` in skill frontmatter. |
| **Missing `mcp.json` `$schema` match** | **Fatal** (§10.1) | `mcp.json` `$schema` version differs from `plugin.json` `$schema` | Ensure both manifests specify identical `$schema` version URLs. |
| **`PLUGIN_ROOT` in `mcp.json` `env`** | **Fatal** (§9.2) | Server `env` manually defines `PLUGIN_ROOT` or `PLUGIN_DATA` | Remove `PLUGIN_ROOT`/`PLUGIN_DATA` from `env` object; clients supply them automatically. |
