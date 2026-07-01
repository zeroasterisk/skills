# Agent Skills

Reusable skills for AI coding agents. Works with OpenClaw, Gemini CLI, and other agent platforms.

## Skills

| Skill | Description |
|-------|-------------|
| [cuj-screenshots](./cuj-screenshots/) | Capture Critical User Journey screenshots and GIFs |
| [storybook](./storybook/) | Write and test Storybook stories for React components |
| [elixir-best-practices](./elixir-best-practices/) | Elixir coding standards — pattern matching, error handling, Phoenix conventions |
| [intent-refinement](./intent-refinement/) | Draft, validate, and refine product intent using Narrative-Driven Development (NDD) |
| [ui-developer](./ui-developer/) | Full-stack UI development workflow with testing and docs |

## Scion Templates

Agent templates for [Scion](https://scion.ai) — each directory contains a `scion-agent.yaml`, system prompt, and agent instructions.

| Template | Description |
|----------|-------------|
| [elixir-dev](./templates/elixir-dev/) | Elixir SWE agent with Postgres, SQLite, Redis — for AgentMsg and a2a-elixir development |
| [project-lead](./templates/project-lead/) | Project lead — sub-coordinator for sustained project work, delegates to SWE/verifier agents |
| [researcher](./templates/researcher/) | Research agent — investigates questions, reads docs, analyzes code, produces findings |
| [swe](./templates/swe/) | Senior software engineer — implements features, fixes bugs, writes tests |
| [verifier](./templates/verifier/) | Skeptical verifier — independently checks that work actually produces correct outcomes |

Also included: [elixir-best-practices.md](./templates/elixir-best-practices.md) — Elixir coding standards and conventions for SWE agents.

## Registry & Sync

This repo is the **canonical source** for personal skills and the **registry** for
federated skills from other sources (team repos, internal tooling, etc.).

### How federation works

External skill sources are cloned as independent git repos into gitignored
subdirectories alongside the personal skills:

```
skills/                        # this repo
  registry.yaml                # index of all skills across all sources
  sync.sh                      # reconciles registry → agent config + catalogs
  elixir-best-practices/       # personal skill (tracked by this repo)
  ui-developer/                # personal skill (tracked by this repo)
  some-team-skills/            # external repo, gitignored — independent .git
  another-source/              # external repo, gitignored — independent .git
  ai-catalog.json              # generated: aggregate of all resolved skills
  ai-catalog.zeroasterisk-skills.json  # generated: this bundle only
```

Each external directory is its own git repo. This repo never tracks their
contents — only `registry.yaml` knows they exist. On machines that don't have
access to a source, that directory simply won't be present and those skills are
silently skipped.

### Adding an external skill source

```bash
# 1. Clone the external repo into this directory
git clone <remote-url> ~/path/to/skills/source-name

# 2. Add entries to registry.yaml pointing at paths inside it
#    e.g.  path: source-name/some-skill

# 3. Sync
./sync.sh
```

The external repo updates independently — `git pull` inside its directory.
Your registry entry keeps working as long as the path exists.

### sync.sh

Reads `registry.yaml` and on each run:

1. Resolves which skill paths actually exist on this machine
2. Updates `cloudcode.json` `skills.paths` (CloudCode agent)
3. Creates/cleans symlinks in `~/.gemini/config/skills/` (Gemini/AGY)
4. Writes `ai-catalog.json` per source bundle + an aggregate

```bash
./sync.sh               # normal sync
./sync.sh --dry-run     # preview without changes
./sync.sh --verbose     # show skipped skills too
```

### ai-catalog.json

Machine-readable skill catalog emitted by `sync.sh`. Contains all skills
resolved on the current machine with per-agent views (`by_agent.cloudcode`,
`by_agent.gemini`). Does not contain local filesystem paths or machine
identifiers — safe to commit and publish.

Intended as a future interface point for skill discovery services.

### Usage

### Antigravity (`agy`) / Jetski

`agy` (Antigravity - external) and `jetski` (internal) auto-discover skills placed in your customization root (e.g., `~/.gemini/config/skills/` or project `.agents/skills/`).

Copy a skill folder to your skills directory:

```bash
# External (Antigravity)
cp -r cuj-screenshots ~/.gemini/config/skills/

# Internal (Jetski)
cp -r cuj-screenshots ~/.gemini/config/skills/
```

Both platforms automatically discover the skill from the `SKILL.md` frontmatter and instructions.

### OpenClaw

Copy a skill folder to `~/.openclaw/workspace/skills/`:

```bash
cp -r cuj-screenshots ~/.openclaw/workspace/skills/
```

OpenClaw auto-discovers skills from the `SKILL.md` description.

### Gemini CLI (Deprecated)

> [!WARNING]  
> `gemini` CLI is deprecated in favor of `agy` (Antigravity) externally and `jetski` internally.

Point Gemini to the skill's `GEMINI.md`:

```bash
gemini -i cuj-screenshots/GEMINI.md "capture screenshots of my app"
```

Or use the extension format:

```bash
gemini --load-extension cuj-screenshots/gemini-extension.json
```

## Structure

Each skill follows this structure:

```
skill-name/
├── SKILL.md              # OpenClaw skill file (required)
├── README.md             # Human documentation
├── GEMINI.md             # Gemini CLI instructions (optional)
├── gemini-extension.json # Gemini extension manifest (optional)
├── scripts/              # Helper scripts
└── examples/             # Usage examples
```

## Contributing

PRs welcome! Each skill should:

1. Have a clear, single purpose
2. Work without project-specific dependencies
3. Include examples
4. Support at least OpenClaw (SKILL.md)

## License

MIT
