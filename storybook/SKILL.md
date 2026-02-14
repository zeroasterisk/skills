---
name: storybook
description: Write and test Storybook stories for React components. Use for component isolation, visual testing, and documentation.
---

# Storybook Skill

Create, test, and capture Storybook stories for React components.

## When to Use This

- Creating new React components that need isolation testing
- Documenting component variants and states
- Capturing visual snapshots for documentation
- Testing responsive behavior across viewport sizes

## Quick Start

### 1. Install Storybook (if not present)

```bash
cd frontend
npx storybook@latest init
```

### 2. Create a Story

For a component at `src/components/Button.tsx`:

```tsx
// src/components/Button.stories.tsx
import type { Meta, StoryObj } from '@storybook/react';
import { Button } from './Button';

const meta: Meta<typeof Button> = {
  title: 'Components/Button',
  component: Button,
  tags: ['autodocs'],
  argTypes: {
    variant: {
      control: 'select',
      options: ['primary', 'secondary', 'danger'],
    },
  },
};

export default meta;
type Story = StoryObj<typeof Button>;

export const Primary: Story = {
  args: {
    variant: 'primary',
    children: 'Click me',
  },
};

export const Secondary: Story = {
  args: {
    variant: 'secondary',
    children: 'Click me',
  },
};

export const Disabled: Story = {
  args: {
    variant: 'primary',
    children: 'Disabled',
    disabled: true,
  },
};
```

### 3. Run Storybook

```bash
npm run storybook
# or
bun storybook
```

Default: http://localhost:6006

### 4. Capture Screenshots

Use Playwright to capture story screenshots:

```python
import asyncio
from playwright.async_api import async_playwright

async def capture_stories():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page(viewport={"width": 1280, "height": 720})
        
        # Navigate to specific story
        await page.goto("http://localhost:6006/iframe.html?id=components-button--primary")
        await page.wait_for_timeout(1000)
        await page.screenshot(path="button-primary.png")
        
        await browser.close()

asyncio.run(capture_stories())
```

## Story Patterns

### With Decorators (Providers, Theme)

```tsx
const meta: Meta<typeof MyComponent> = {
  title: 'Components/MyComponent',
  component: MyComponent,
  decorators: [
    (Story) => (
      <ThemeProvider theme={lightTheme}>
        <Story />
      </ThemeProvider>
    ),
  ],
};
```

### With Mock Data

```tsx
export const WithData: Story = {
  args: {
    items: [
      { id: 1, name: 'Item 1' },
      { id: 2, name: 'Item 2' },
    ],
  },
};

export const Empty: Story = {
  args: {
    items: [],
  },
};

export const Loading: Story = {
  args: {
    loading: true,
  },
};
```

### Responsive Stories

```tsx
export const Mobile: Story = {
  args: { /* ... */ },
  parameters: {
    viewport: {
      defaultViewport: 'mobile1',
    },
  },
};

export const Tablet: Story = {
  args: { /* ... */ },
  parameters: {
    viewport: {
      defaultViewport: 'tablet',
    },
  },
};
```

### With Actions

```tsx
import { action } from '@storybook/addon-actions';

export const Interactive: Story = {
  args: {
    onClick: action('clicked'),
    onSubmit: action('submitted'),
  },
};
```

### Play Functions (Interaction Testing)

```tsx
import { within, userEvent } from '@storybook/testing-library';
import { expect } from '@storybook/jest';

export const Filled: Story = {
  play: async ({ canvasElement }) => {
    const canvas = within(canvasElement);
    
    await userEvent.type(
      canvas.getByRole('textbox', { name: /email/i }),
      'test@example.com'
    );
    
    await userEvent.click(canvas.getByRole('button', { name: /submit/i }));
    
    await expect(canvas.getByText('Success')).toBeInTheDocument();
  },
};
```

## Storybook Configuration

### .storybook/main.ts

```ts
import type { StorybookConfig } from '@storybook/react-vite';

const config: StorybookConfig = {
  stories: ['../src/**/*.stories.@(js|jsx|ts|tsx)'],
  addons: [
    '@storybook/addon-links',
    '@storybook/addon-essentials',
    '@storybook/addon-interactions',
  ],
  framework: {
    name: '@storybook/react-vite',
    options: {},
  },
  docs: {
    autodocs: 'tag',
  },
};

export default config;
```

### .storybook/preview.ts

```ts
import type { Preview } from '@storybook/react';
import '../src/index.css'; // Global styles

const preview: Preview = {
  parameters: {
    actions: { argTypesRegex: '^on[A-Z].*' },
    controls: {
      matchers: {
        color: /(background|color)$/i,
        date: /Date$/,
      },
    },
  },
};

export default preview;
```

## Batch Screenshot Capture

```python
#!/usr/bin/env python3
"""Capture all Storybook stories as screenshots."""

import asyncio
import json
from playwright.async_api import async_playwright

STORYBOOK_URL = "http://localhost:6006"

async def get_stories(page):
    """Fetch story list from Storybook."""
    await page.goto(f"{STORYBOOK_URL}/index.json")
    content = await page.content()
    # Parse JSON from page
    data = json.loads(await page.evaluate("() => document.body.innerText"))
    return [
        story_id for story_id, story in data.get("entries", {}).items()
        if story.get("type") == "story"
    ]

async def capture_all():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page(viewport={"width": 1280, "height": 720})
        
        stories = await get_stories(page)
        
        for story_id in stories:
            url = f"{STORYBOOK_URL}/iframe.html?id={story_id}&viewMode=story"
            await page.goto(url)
            await page.wait_for_timeout(500)
            
            filename = story_id.replace("--", "-").replace("/", "-")
            await page.screenshot(path=f"screenshots/{filename}.png")
            print(f"Captured: {story_id}")
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(capture_all())
```

## Tips

- **autodocs tag**: Add `tags: ['autodocs']` for auto-generated docs
- **Args vs render**: Use `args` for simple prop changes, `render` for complex setups
- **Naming**: Use `ComponentName--VariantName` format for story IDs
- **Mock API**: Use MSW addon for mocking API calls in stories
- **Viewport addon**: Configure common viewports in preview.ts
- **Backgrounds**: Add background switcher for light/dark mode testing

## Integration with CUJ Screenshots

Storybook stories can be captured as part of CUJ workflows:

```python
# In your CUJ script
await page.goto("http://localhost:6006/iframe.html?id=components-taskcard--default")
await page.screenshot(path="docs/screenshots/taskcard.png")
```

This gives you both isolated component shots and full-app journey shots.
