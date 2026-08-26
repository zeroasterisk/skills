# Phased Plugin Migration Playbook

This playbook outlines the recommended step-by-step sequence for converting an existing flat skills repository into an Agent Plugins v1.0.0 monorepo.

## Phase 0: Pre-flight Hygiene & Git Exclusion
1. Identify machine-local runtime directories (e.g. `.serena/`, `.antigravitycli/`, `.cache/`).
2. Verify that no untracked file or symlink points *outside* the repository root (e.g. absolute symlinks to home directory config files). Symlinks escaping the repo violate spec §4.1 containment and will poison archive distributions.
3. Add machine-local runtime paths to `.gitignore`.

## Phase 1: Resolve Conformance Debt (Before Directory Moves)
*Rule:* Fix all `SKILL.md` frontmatter, missing licenses, and non-executable script issues **before** moving files, so git history tracks pure directory renames without mixed content diffs.

1. **Add Missing Frontmatter:** Ensure every `SKILL.md` begins with `---` YAML frontmatter containing `name` and `description`.
2. **Trim Oversized Descriptions:** Truncate `description` strings exceeding 1024 characters (Agent Skills spec constraint) while preserving key trigger phrases.
3. **Normalize Metadata & Versioning:** Move non-spec top-level fields (like top-level `version: 1.0.0`) under `metadata:\n  version: "1.0.0"`.
4. **License & Executable Bits:** Ensure `license:` is specified (e.g., `license: Apache-2.0`) and run `chmod +x` on all files inside `scripts/` directories.
5. **Asset & Reference Relocation:** Move project configuration templates (e.g. `.yml` configs) from `references/` to `assets/`. Fold stray root directories (like sample output reports) into their parent skill's `references/` directory.

## Phase 2: Restructure Directories via `git mv`
1. Group skills into thematic plugins under `plugins/<plugin-name>/skills/`.
2. Analyze cross-skill relative links (e.g. `../sibling-skill/SKILL.md`). Ensure skills that delegate to each other belong to the same plugin so parent-relative links resolve legally within the plugin root (§4.1).
3. Execute renames using `git mv <skill-name> plugins/<plugin-name>/skills/<skill-name>`.

## Phase 3: Add Plugin Manifests & Marketplace Index
1. Create `plugins/<plugin-name>/plugin.json` for each plugin, specifying `$schema` (`https://agent-plugins.org/schemas/1.0.0/plugin.schema.json`), `name`, `version`, `description`, `author`, `repository`, and `license` per [Agent Plugins §5](https://github.com/agentplugins/agent-plugins-spec/blob/main/spec/1.0.0.md#5-manifest).
2. If the plugin provides or configures MCP servers, create `plugins/<plugin-name>/mcp.json` with matching `$schema` version (`https://agent-plugins.org/schemas/1.0.0/mcp.schema.json`) per [Agent Plugins §7.2](https://github.com/agentplugins/agent-plugins-spec/blob/main/spec/1.0.0.md#72-mcp-servers).
3. Create `.claude-plugin/marketplace.json` at the repo root to provide a deterministic index for `npx skills` and Claude Code.

## Phase 4: Validation & Automation
1. Run `./scripts/validate-plugins.sh` locally to verify:
   - `plugin.json` schema and name consistency
   - `SKILL.md` frontmatter, description length ($\le 1024$), and directory name match
   - Script executable bits (`+x`)
   - `marketplace.json` validity
2. Add a GitHub Actions workflow (`.github/workflows/validate.yml`) to run the validation script on push/PR.

## Phase 5: Documentation & Commit
1. Add root `LICENSE` (e.g. Apache License 2.0) and `CONTRIBUTING.md`.
2. Update root `README.md` to organize skills by plugin and document installation paths for `npx skills`, `gemini skills`, and `agy`.
3. Commit all changes with a clear commit message: `feat: restructure repository into Agent Plugins v1.0.0 architecture`.
