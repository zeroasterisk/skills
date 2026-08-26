# Discovery Compatibility Analysis

When converting a flat skills repository to an Agent Plugins monorepo, maintaining compatibility with ecosystem installers (`npx skills`, `gemini skills`, `agy`) requires understanding how each tool discovers skills.

## 1. `npx skills` (Open Agent Skills CLI) Discovery Logic

The Open Agent Skills CLI discovers skills in a repository using the following hierarchy:

1. **Standard Containers Walk (Depth 1-2):**
   - Container directories checked: `skills/`, `.agents/skills/`, `.claude/skills/`, `data/skills/`, etc.
   - Walked one level deep for flat layout (`skills/<skill>/SKILL.md`) and one extra level deep for catalog layout (`skills/<category>/<skill>/SKILL.md`).
   - Note: `plugins/` is **not** in the default container list.

2. **Plugin Manifest Discovery (`.claude-plugin/marketplace.json`):**
   - If `.claude-plugin/marketplace.json` or `plugin.json` exists at the repo root, `npx skills` reads declared skill paths directly:
     ```json
     {
       "metadata": { "pluginRoot": "./plugins" },
       "plugins": [
         {
           "name": "my-plugin",
           "skills": ["./plugins/my-plugin/skills/my-skill"]
         }
       ]
     }
     ```
   - Skill paths declared in a marketplace manifest bypass container depth limits and are discovered deterministically.

3. **Recursive Fallback:**
   - If no skills are found in standard container directories, `npx skills` performs a recursive file search for `SKILL.md` across the repository.
   - *Key Insight:* A repository with skills at the root (e.g. `./my-skill/SKILL.md`) was already relying on this recursive fallback! Restructuring into `plugins/*/skills/` with a `.claude-plugin/marketplace.json` index converts an implicit fallback search into deterministic discovery.

## 2. Gemini CLI & Antigravity CLI (`agy`) Compatibility

- **Gemini CLI:** Accepts explicit relative directory paths via `gemini skills install --path <path>` or `gemini skills link <path>`. Points directly to `plugins/<plugin>/skills/<skill>`.
- **Antigravity CLI:** Copies skill directories into `.agents/skills/` or `~/.gemini/antigravity/skills/`. Copying from `plugins/<plugin>/skills/*` works seamlessly.

## 3. Summary of Best Practices
- Always ship a `.claude-plugin/marketplace.json` index at the repository root when placing skills under `plugins/`.
- Ensure skill `name` in frontmatter matches its immediate parent directory name.
- Keep all internal skill file references (`references/`, `scripts/`, `assets/`) relative to the skill root.
