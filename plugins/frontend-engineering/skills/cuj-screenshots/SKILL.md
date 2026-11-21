---
name: cuj-screenshots
description: Capture Critical User Journey (CUJ) screenshots and GIFs from web apps using headless Chromium, keyed to the repo's feature map so each journey proves one named feature. Use when you need to verify UI changes through the real app, produce reviewable visual evidence for a PR, or document user flows. Don't use for component-level stories (use storybook).
license: Apache-2.0
---

# CUJ Screenshots Skill

Automate visual documentation of web app user journeys using headless browser automation.

## When to Use This

**Always run CUJ captures after UI changes.** This is part of the dev loop, not just documentation.

### Triggered By:
- Any frontend component change
- CSS/styling updates
- New features that affect user flow
- Bug fixes that change visible behavior
- Before sharing work with humans ("here's what it looks like now")

### The Loop:
```
Make UI change → Run CUJs → Review screenshots → 
  ├─ Looks good? → Update GIFs, commit, share link
  └─ Looks wrong? → Fix bug, repeat
```

### Proactive Use:
When finishing UI work, don't just say "done" — capture CUJs, update the GIFs, and share:

> "Updated the task card styling. Here's the new CUJ: 
> https://github.com/user/repo/blob/main/docs/CUJs.md"

This gives your human instant visual feedback without them needing to run the app.

## What It Does

1. Launches headless Chromium via Playwright
2. Navigates through a defined user journey
3. Captures screenshots at each step
4. Stitches screenshots into an animated GIF
5. Outputs to a docs folder for commit

## Requirements

- **Playwright**: `uv run --with playwright python script.py`
- **Chromium**: Auto-installed by Playwright on first run
- **ImageMagick**: For GIF creation (`convert` command)

Install Playwright browsers (one-time):
```bash
uv run --with playwright playwright install chromium
```

## Quick Start

### 1. Define Your CUJ

Create a Python script for each journey:

```python
import asyncio
from playwright.async_api import async_playwright
import os

async def capture_my_cuj():
    output_dir = "/tmp/cuj-screenshots/my-cuj"
    os.makedirs(output_dir, exist_ok=True)
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            viewport={"width": 390, "height": 844},  # Mobile
            device_scale_factor=2  # Retina
        )
        page = await context.new_page()
        
        await page.goto("http://localhost:5173")
        await page.get_by_role("heading", name="Tasks").wait_for()
        await page.screenshot(path=f"{output_dir}/01-initial.png")

        await page.get_by_role("button", name="Submit").click()
        await page.get_by_role("status").filter(has_text="Saved").wait_for()
        await page.screenshot(path=f"{output_dir}/02-submitted.png")
        
        # ... more steps
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(capture_my_cuj())
```

### 2. Run Capture

```bash
uv run --with playwright python my_cuj.py
```

### 3. Create GIF

```bash
convert -delay 150 -loop 0 /tmp/cuj-screenshots/my-cuj/*.png output.gif
```

- `-delay 150` = 1.5 seconds per frame (hundredths of a second)
- `-loop 0` = infinite loop

### 4. Commit & Share

```bash
mv output.gif docs/gifs/my-cuj.gif
git add docs/gifs/my-cuj.gif docs/CUJs.md
git commit -m "docs: add my-cuj GIF"
git push
```

## Viewport Presets

| Device | Width | Height | Scale |
|--------|-------|--------|-------|
| iPhone 12 Pro | 390 | 844 | 2 |
| iPhone SE | 375 | 667 | 2 |
| Pixel 5 | 393 | 851 | 2.75 |
| Desktop | 1280 | 720 | 1 |
| Desktop HD | 1920 | 1080 | 1 |

## Common Interactions

```python
# Click by role and accessible name
await page.get_by_role("button", name="Submit").click()

# Fill input by label
await page.get_by_label("Email").fill("test@example.com")

# Select dropdown
await page.get_by_label("Plan").select_option("premium")

# Wait for the resulting state, not for a fixed time
await page.get_by_role("status").filter(has_text="Saved").wait_for()

# Scroll
await page.evaluate("window.scrollBy(0, 300)")

# Keyboard shortcut
await page.keyboard.press("Escape")
```

## Full Workflow Example

See `scripts/capture-cujs.py` for a complete example that:
- Starts backend + frontend servers
- Captures multiple CUJs
- Generates GIFs
- Updates CUJs.md

## Tips

- **Waits**: Wait for the state the user would see (`wait_for()` on a role, text, or URL). Fixed `wait_for_timeout` sleeps make captures flaky and slow; use one only to let an animation settle before a screenshot.
- **Selectors**: Prefer `get_by_role` and `get_by_label` over CSS selectors. They match the feature map's names and survive restyling.
- **Error handling**: Wrap interactions in try/except, screenshot on error
- **Naming**: Use numbered prefixes (`01-`, `02-`) for sort order
- **GIF size**: Keep under 500KB for GitHub README display

## Feature map (`docs/CUJs.md`)

Each CUJ proves one feature from the repo's feature map. If the repo has a `docs/features/` map (see the codebase-gardening skill), name each CUJ after a feature there and link it. Otherwise keep `docs/CUJs.md` with one section per journey, from the user's point of view:

```markdown
## CUJ 2: Create task

**Goal:** Create a task from the board view.

**Entry points:** `+ Task` button, `n` key, `tasks create` CLI.

**Steps:**
1. Choose `+ Task`.
2. Enter `Write docs` in `Title`, choose `Save`.

**Proof:** status `Saved` appears and the board lists `Write docs` after reload.

![Create task](./gifs/cuj2-create-task.gif)
```

Rules:

- Use the exact names the UI shows, so prompts, tickets, and tests mean the same thing.
- Cover every entry point listed. A capture through one path does not prove the others.
- The proof is the end state after the action (ideally confirmed from a second view, such as a reload), not just the last screen.
- Update the map in the same change that adds or renames a feature.

## Verify and share

1. Make the UI change.
2. Start the app with the repo's launch command.
3. Run the captures: `uv run --with playwright python scripts/capture-cujs.py`.
4. Look at every new screenshot (you can read image files). If one looks wrong, you found a bug. Fix it and rerun.
5. Build GIFs: `convert -delay 150 -loop 0 /tmp/cuj-screenshots/cuj1/*.png docs/gifs/cuj1.gif`.
6. Commit the map and GIFs with the code, and put the GIF in the PR description.
