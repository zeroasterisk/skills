# Storybook Skill

Write and test Storybook stories for React components.

## What This Skill Does

Guides AI agents through:
- Creating Storybook stories for React components
- Testing component variants and states in isolation
- Capturing visual screenshots via Playwright
- Setting up responsive and interaction tests

## Quick Example

```tsx
// Button.stories.tsx
import type { Meta, StoryObj } from '@storybook/react';
import { Button } from './Button';

const meta: Meta<typeof Button> = {
  title: 'Components/Button',
  component: Button,
  tags: ['autodocs'],
};

export default meta;
type Story = StoryObj<typeof Button>;

export const Primary: Story = {
  args: { variant: 'primary', children: 'Click me' },
};
```

## Files

- `SKILL.md` - Full skill instructions for OpenClaw
- `GEMINI.md` - Instructions for Gemini CLI
- `scripts/capture-stories.py` - Batch screenshot capture

## Usage

### OpenClaw
```bash
cp -r storybook ~/.openclaw/workspace/skills/
```

### Gemini CLI
```bash
gemini -i storybook/GEMINI.md "create a story for my Card component"
```

## See Also

- [cuj-screenshots](../cuj-screenshots/) - Capture full user journey screenshots
- [ui-developer](../ui-developer/) - Complete UI development workflow
