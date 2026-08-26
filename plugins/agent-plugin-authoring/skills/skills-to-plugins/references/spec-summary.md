# Agent Plugins Specification v1.0.0 — Normative Reference Summary

This reference summarizes the core rules of the Agent Plugins Specification v1.0.0 and Agent Skills Specification for quick lookup during migration, authoring, and validation.

## Canonical Sources

| Specification / Artifact | Canonical Location |
|---|---|
| **Agent Plugins Specification (Repository)** | [agentplugins/agent-plugins-spec](https://github.com/agentplugins/agent-plugins-spec) |
| **Agent Plugins Specification (v1.0.0 Text)** | [spec/1.0.0.md](https://github.com/agentplugins/agent-plugins-spec/blob/main/spec/1.0.0.md) |
| **Plugin Manifest Schema** | [schemas/1.0.0/plugin.schema.json](https://github.com/agentplugins/agent-plugins-spec/blob/main/schemas/1.0.0/plugin.schema.json) |
| **MCP Configuration Schema** | [schemas/1.0.0/mcp.schema.json](https://github.com/agentplugins/agent-plugins-spec/blob/main/schemas/1.0.0/mcp.schema.json) |
| **Agent Skills Specification** | [agentskills.io/specification.md](https://agentskills.io/specification.md) |
| **Reference Skill Validator (`skills-ref`)** | [agentskills/skills-ref](https://github.com/agentskills/agentskills/tree/main/skills-ref) |

> **Precedence & Identification Notes:**
> 1. **Specification Text Governs:** As defined in Agent Plugins §5.2, if a discrepancy exists between a machine-readable JSON schema and the normative specification text, the specification text is authoritative.
> 2. **`$schema` URLs are Identifiers, Not Documents:** Canonical `$schema` values (e.g., `https://agent-plugins.org/schemas/1.0.0/plugin.schema.json`) are version identifiers used for local schema matching — clients MUST NOT retrieve them over the network at runtime (§5.2).
> 3. **Staleness Warning:** This document is a summary distillation. On any ambiguity or specification update, re-verify against the canonical links above.

---

## 1. Package Containment ([§4.1](https://github.com/agentplugins/agent-plugins-spec/blob/main/spec/1.0.0.md#41-general-requirements))
- A plugin is a single directory rooted at a filesystem location.
- **Strict Containment:** Every path resolved by a client MUST remain within the plugin root directory.
- Symlinks, junctions, or relative paths escaping the plugin root (e.g. `../`) MUST be rejected by conformant clients.
- Symlinks pointing *inside* the plugin root are allowed.

## 2. Manifest (`plugin.json`) ([§5](https://github.com/agentplugins/agent-plugins-spec/blob/main/spec/1.0.0.md#5-manifest))
- MUST exist at the plugin root: `plugin.json`.
- Closed schema: the only permitted top-level fields are `$schema`, `name`, `version`, `description`, `author`, `homepage`, `repository`, `license`, `keywords`, and `extensions`.
- `$schema` MUST be `https://agent-plugins.org/schemas/1.0.0/plugin.schema.json`.
- `name` MUST match `^[a-z0-9](?:[a-z0-9.-]*[a-z0-9])?$` (1-64 chars, lowercase alphanumeric, hyphens, periods).
- Unknown top-level fields are reported and ignored by clients (non-fatal schema exception). Any other schema violation is fatal.

## 3. Fixed Component Discovery ([§6](https://github.com/agentplugins/agent-plugins-spec/blob/main/spec/1.0.0.md#6-component-discovery), [§7](https://github.com/agentplugins/agent-plugins-spec/blob/main/spec/1.0.0.md#7-component-types))
- **Skills Location:** `skills/<skill-name>/SKILL.md` (immediate children of `skills/` directory only; deep recursion is not performed).
- **MCP Location:** `mcp.json` at the plugin root only.
- Missing component locations (e.g. no `mcp.json` or no `skills/` dir) are non-fatal.

## 4. MCP Server Configuration (`mcp.json`) ([§7.2](https://github.com/agentplugins/agent-plugins-spec/blob/main/spec/1.0.0.md#72-mcp-servers), [§9](https://github.com/agentplugins/agent-plugins-spec/blob/main/spec/1.0.0.md#9-environment-variables-and-placeholder-expansion))
- `$schema` MUST be `https://agent-plugins.org/schemas/1.0.0/mcp.schema.json` (MUST match the version of `plugin.json`).
- `mcpServers` object contains server definitions (`type`: `"stdio"`, `"streamable-http"`, or `"sse"`).
- **Subprocess Environment Variables ([§9.1](https://github.com/agentplugins/agent-plugins-spec/blob/main/spec/1.0.0.md#91-subprocess-environment)):**
  - Clients set `PLUGIN_ROOT` (absolute path to plugin root) and `PLUGIN_DATA` (absolute path to client-managed persistent writable directory).
  - Server configuration `env` MUST NOT contain entries named `PLUGIN_ROOT` or `PLUGIN_DATA`.
- **Placeholder Expansion ([§9.2](https://github.com/agentplugins/agent-plugins-spec/blob/main/spec/1.0.0.md#92-placeholder-expansion)):**
  - Text placeholders `${PLUGIN_ROOT}` and `${PLUGIN_DATA}` are expanded in `args`, `env` values, and `cwd`.
  - Expansion does NOT apply to `command`, `env` keys, or fixed locations.

## 5. Agent Skills Frontmatter ([§7.1](https://github.com/agentplugins/agent-plugins-spec/blob/main/spec/1.0.0.md#71-skills), [Agent Skills Spec](https://agentskills.io/specification.md))
- `SKILL.md` MUST begin with `---` YAML frontmatter.
- Required: `name` (1-64 chars, lowercase alphanumeric and hyphens; MUST match directory name), `description` (1-1024 chars).
- Optional: `license`, `compatibility` (1-500 chars), `metadata` (mapping), `allowed-tools`.
- Non-standard top-level fields (like top-level `version:`) MUST be nested under `metadata:`.
