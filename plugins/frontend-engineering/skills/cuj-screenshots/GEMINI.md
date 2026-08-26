# CUJ Screenshots

You have access to the CUJ (Critical User Journey) screenshots skill. Use it to capture visual documentation of web app user journeys.

## When to Use

**Always run CUJ captures after UI changes.** This is part of the dev loop.

Triggers:
- Frontend component changes
- CSS/styling updates  
- New features affecting user flow
- Bug fixes with visible changes
- Before sharing work with humans

## The Loop

```
Make UI change → Run CUJs → Review screenshots → 
  ├─ Looks good? → Update GIFs, commit, share link
  └─ Looks wrong? → Fix bug, repeat
```

## How to Capture

```bash
uv run --with playwright python skills/cuj-screenshots/scripts/capture-cujs.py
```

## Create GIFs

```bash
convert -delay 150 -loop 0 /tmp/cuj-screenshots/*.png output.gif
```

## Prerequisites

- Python 3.10+
- Playwright: `pip install playwright && playwright install chromium`
- ImageMagick: `brew install imagemagick` or `apt install imagemagick`
- Your app running locally

See `skills/cuj-screenshots/SKILL.md` for detailed documentation.
