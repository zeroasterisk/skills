# CUJ Screenshots

Capture Critical User Journey (CUJ) screenshots and GIFs from web apps using headless Chromium.

![CUJ Demo](./examples/demo.gif)

## What It Does

1. 📸 Launches headless Chromium via Playwright
2. 🎯 Navigates through defined user journeys
3. 🖼️ Captures screenshots at each step  
4. 🎬 Stitches screenshots into animated GIFs
5. 📝 Documents journeys in markdown

## When to Use

**Run CUJ captures after UI changes.** This is part of the dev loop, not just docs.

- Frontend component changes
- CSS/styling updates
- New features affecting user flow
- Bug fixes with visible changes
- Before sharing work ("here's what it looks like now")

## Installation

### Universal (npx skills) — Works with 35+ agents

```bash
# Claude Code, Cursor, Codex, Windsurf, OpenClaw, Gemini CLI, etc.
npx skills add zeroasterisk/cuj-screenshots
```

### Gemini CLI Extension

```bash
gemini extensions install https://github.com/zeroasterisk/cuj-screenshots
```

### Manual

Copy the `skills/cuj-screenshots/` folder into your agent's skills directory.

## Prerequisites

| Tool | Install |
|------|---------|
| Python 3.10+ | [python.org](https://python.org) |
| Playwright | `pip install playwright && playwright install chromium` |
| ImageMagick | `brew install imagemagick` (macOS) / `apt install imagemagick` (Linux) |

## Usage

### Quick Start

```bash
# Run the capture script (checks prerequisites first)
uv run --with playwright python scripts/capture-cujs.py
```

### The Dev Loop

```
Make UI change → Run CUJs → Review screenshots → 
  ├─ Looks good? → Update GIFs, commit, share link
  └─ Looks wrong? → Fix bug, repeat
```

### Custom CUJs

Define your journeys in Python:

```python
CUJ_LOGIN = {
    "name": "login-flow",
    "steps": [
        {"action": "goto", "url": "http://localhost:3000/login", "screenshot": "01-login-page.png"},
        {"action": "fill", "selector": "input[name='email']", "value": "test@example.com"},
        {"action": "fill", "selector": "input[name='password']", "value": "secret", "screenshot": "02-filled.png"},
        {"action": "click", "selector": "button[type='submit']", "wait": 2000, "screenshot": "03-dashboard.png"},
    ]
}
```

### Create GIFs

```bash
convert -delay 150 -loop 0 /tmp/cuj-screenshots/*.png docs/gifs/my-cuj.gif
```

## Output: CUJs.md

Document your journeys with embedded GIFs:

```markdown
## Login Flow

**Goal:** User logs in successfully.

**Steps:**
1. Navigate to login page
2. Enter credentials
3. Click submit → Dashboard

![Login Flow](./gifs/login-flow.gif)
```

## Repo Structure

```
cuj-screenshots/
├── README.md                    # You are here
├── skills/
│   └── cuj-screenshots/
│       ├── SKILL.md             # Agent Skills spec (works everywhere)
│       └── scripts/
│           └── capture-cujs.py  # Main capture script
├── gemini-extension.json        # Gemini CLI extension manifest
├── GEMINI.md                    # Context for Gemini CLI sessions
└── examples/
    ├── demo.gif                 # Example output
    └── example-cujs.md          # Example documentation
```

## Compatibility

| Platform | Install Method | Status |
|----------|---------------|--------|
| Claude Code | `npx skills add` | ✅ |
| Cursor | `npx skills add` | ✅ |
| Codex | `npx skills add` | ✅ |
| Windsurf | `npx skills add` | ✅ |
| OpenClaw | `npx skills add` | ✅ |
| Gemini CLI | `gemini extensions install` | ✅ |
| GitHub Copilot | `npx skills add` | ✅ |
| 30+ more agents | `npx skills add` | ✅ |

## License

Apache 2.0
