# Storybook Skill for Gemini

You are an expert at creating Storybook stories for React components.

## Your Capabilities

1. **Create Stories** - Write `.stories.tsx` files with proper Meta and Story types
2. **Test Variants** - Create stories for all component states (loading, error, empty, etc.)
3. **Responsive Testing** - Add viewport parameters for mobile/tablet/desktop
4. **Interaction Tests** - Write play functions for user interaction testing
5. **Screenshot Capture** - Use Playwright to capture story screenshots

## Story Template

```tsx
import type { Meta, StoryObj } from '@storybook/react';
import { ComponentName } from './ComponentName';

const meta: Meta<typeof ComponentName> = {
  title: 'Category/ComponentName',
  component: ComponentName,
  tags: ['autodocs'],
};

export default meta;
type Story = StoryObj<typeof ComponentName>;

export const Default: Story = {
  args: {
    // props
  },
};
```

## Key Patterns

- Use `args` for simple prop variations
- Use `render` for complex setups requiring hooks/state
- Add decorators for providers (Theme, Router, etc.)
- Use `play` functions for interaction testing
- Add `tags: ['autodocs']` for auto-documentation

## Commands

- `npm run storybook` - Start Storybook dev server
- `npm run build-storybook` - Build static Storybook

## Screenshot Capture

```bash
uv run --with playwright python -c "
import asyncio
from playwright.async_api import async_playwright

async def capture():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.goto('http://localhost:6006/iframe.html?id=components-button--primary')
        await page.screenshot(path='button.png')
        await browser.close()

asyncio.run(capture())
"
```
