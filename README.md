# Agent Skills

Reusable skills for AI coding agents. Works with OpenClaw, Gemini CLI, and other agent platforms.

## Skills

| Skill | Description |
|-------|-------------|
| [cuj-screenshots](./cuj-screenshots/) | Capture Critical User Journey screenshots and GIFs |
| [storybook](./storybook/) | Write and test Storybook stories for React components |
| [ui-developer](./ui-developer/) | Full-stack UI development workflow with testing and docs |

## Usage

### OpenClaw

Copy a skill folder to `~/.openclaw/workspace/skills/`:

```bash
cp -r cuj-screenshots ~/.openclaw/workspace/skills/
```

OpenClaw auto-discovers skills from the `SKILL.md` description.

### Gemini CLI

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
