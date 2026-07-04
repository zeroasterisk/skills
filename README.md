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
| [verification-before-completion](./verification-before-completion/) | Two-lane verification (scrutiny + real-surface) before any completion claim. Adapted from [superpowers](https://github.com/obra/superpowers) + [zenith](https://github.com/Intelligent-Internet/zenith) |
| [systematic-debugging](./systematic-debugging/) | Four-phase root cause debugging: trace → analyze → hypothesize → fix. Adapted from [superpowers](https://github.com/obra/superpowers) |
| [contract-driven-validation](./contract-driven-validation/) | VAL-* assertions: Surface/Needs/Behavior/Evidence for every capability. Adapted from [zenith](https://github.com/Intelligent-Internet/zenith) |

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
federated skills from other sources (team repos, google/skills, internal tooling).

### How federation works

External skill sources are cloned as independent git repos into gitignored
subdirectories alongside the personal skills. `registry.toml` declares each
**source** once; skills within a source are **auto-discovered** by scanning
for `SKILL.md` files (scoped by `include`/`exclude` globs):

```
skills/                        # this repo
  registry.toml                # source declarations + per-skill overrides
  sync.py                      # reconciles registry → agent config + catalogs
  sync.sh                      # thin wrapper around sync.py
  elixir-best-practices/       # personal skill (tracked by this repo)
  ui-developer/                # personal skill (tracked by this repo)
  google-skills/               # github.com/google/skills clone — gitignored
  ai-catalog.json              # generated: ARD aggregate of resolved skills
  ai-catalog.<source>.json     # generated: one ARD catalog per source
```

Each external directory is its own git repo. This repo never tracks their
contents — only `registry.toml` knows they exist. On machines without a given
source, that directory simply isn't present and its skills are silently
skipped. New skills added upstream appear automatically after `git pull` +
`./sync.py` — no per-skill registry edits needed.

### Replicating on a new machine

```bash
git clone git@github.com:zeroasterisk/skills.git ~/Workspaces/skills
cd ~/Workspaces/skills
./sync.py --clone-missing     # clones declared external sources, then syncs
```

Sources declared with `repo` + `clone_to` in `registry.toml` are cloned
automatically by `--clone-missing`; anything else (e.g. google3 paths) is
skipped silently on machines without access. Agent wiring destinations are
configurable per machine via `[targets]` in `registry.toml`.

### Adding an external skill source

```bash
# 1. Add ONE [[source]] block to registry.toml:
#    repo = "https://github.com/google/skills.git"
#    clone_to = "google-skills"        # gitignore this dir
#    path = "google-skills/skills"
#    include = ["cloud/gcloud", ...]   # curate, or omit for everything

# 2. Clone + sync
./sync.py --clone-missing
```

### sync.py

Reads `registry.toml` (stdlib `tomllib`, no dependencies) and on each run:

1. Auto-discovers `*/SKILL.md` under each source path present on this machine
2. Updates `cloudcode.json` `skills.paths` (CloudCode agent)
3. Creates/cleans symlinks in `~/.gemini/config/skills/` (Gemini/AGY)
4. Writes ARD-compliant `ai-catalog.json` per source + an aggregate

```bash
./sync.py               # normal sync (sync.sh still works)
./sync.py --dry-run     # preview without changes
./sync.py --verbose     # show skipped skills too
```

### ai-catalog.json (ARD)

Catalogs follow the [Agentic Resource Discovery](https://agenticresourcediscovery.org/)
`ai-catalog` spec (specVersion 1.0, validated against the
[official schema](https://github.com/ards-project/ard-spec/blob/main/spec/schemas/ai-catalog.schema.json)).
Each skill is an entry of type `application/ai-skill+md` with a
domain-anchored URN (`urn:air:github.com:zeroasterisk:<skill>`), public
GitHub URL, tags, and metadata. No local filesystem paths — safe to commit,
and publishable at `/.well-known/ai-catalog.json` for ARD registries to
crawl once we want public discovery.

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
