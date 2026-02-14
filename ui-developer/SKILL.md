---
name: ui-developer
description: Full-stack UI development workflow with component isolation, testing, visual documentation, and CUJ capture. Use for React/TypeScript frontend development.
---

# UI Developer Skill

Complete workflow for frontend development with testing and visual documentation.

## When to Use This

- Building new UI features end-to-end
- Following a structured dev loop with visual verification
- Ensuring components are tested in isolation AND in context

## The Development Loop

```
1. Component Development
   └─ Create/edit component
   └─ Write unit tests
   └─ Run tests: bun test (or npm test)

2. Storybook Isolation
   └─ Create story for component
   └─ Test variants (loading, error, empty, responsive)
   └─ Run storybook: bun storybook

3. Integration
   └─ Use component in pages
   └─ Verify in browser

4. Visual Documentation
   └─ Capture CUJ screenshots
   └─ Create GIFs
   └─ Update docs

5. Commit & Share
   └─ Commit code + docs + GIFs
   └─ Push and share link
```

## Step 1: Component Development

### Create Component

```tsx
// src/components/TaskCard.tsx
interface TaskCardProps {
  id: string;
  title: string;
  status: 'todo' | 'doing' | 'done';
  onClick?: () => void;
}

export function TaskCard({ id, title, status, onClick }: TaskCardProps) {
  return (
    <div 
      className={`task-card task-card--${status}`}
      onClick={onClick}
      role="button"
      tabIndex={0}
    >
      <h3>{title}</h3>
      <span className="status-badge">{status}</span>
    </div>
  );
}
```

### Write Tests

```tsx
// src/components/TaskCard.test.tsx
import { render, screen, fireEvent } from '@testing-library/react';
import { TaskCard } from './TaskCard';

describe('TaskCard', () => {
  it('renders title', () => {
    render(<TaskCard id="1" title="Test Task" status="todo" />);
    expect(screen.getByText('Test Task')).toBeInTheDocument();
  });

  it('shows status badge', () => {
    render(<TaskCard id="1" title="Test" status="doing" />);
    expect(screen.getByText('doing')).toBeInTheDocument();
  });

  it('calls onClick when clicked', () => {
    const onClick = vi.fn();
    render(<TaskCard id="1" title="Test" status="todo" onClick={onClick} />);
    fireEvent.click(screen.getByRole('button'));
    expect(onClick).toHaveBeenCalled();
  });
});
```

### Run Tests

```bash
bun test                    # Run all tests
bun test TaskCard           # Run specific tests
bun test --watch            # Watch mode
bun test --coverage         # With coverage
```

## Step 2: Storybook Isolation

### Create Story

```tsx
// src/components/TaskCard.stories.tsx
import type { Meta, StoryObj } from '@storybook/react';
import { TaskCard } from './TaskCard';

const meta: Meta<typeof TaskCard> = {
  title: 'Components/TaskCard',
  component: TaskCard,
  tags: ['autodocs'],
};

export default meta;
type Story = StoryObj<typeof TaskCard>;

export const Todo: Story = {
  args: { id: '1', title: 'Write documentation', status: 'todo' },
};

export const Doing: Story = {
  args: { id: '2', title: 'Implement feature', status: 'doing' },
};

export const Done: Story = {
  args: { id: '3', title: 'Ship it!', status: 'done' },
};

export const Mobile: Story = {
  args: { id: '1', title: 'Mobile view', status: 'todo' },
  parameters: { viewport: { defaultViewport: 'mobile1' } },
};
```

### Run Storybook

```bash
bun storybook               # Start dev server at :6006
bun build-storybook         # Build static site
```

## Step 3: Visual Documentation

### CUJ Screenshot Capture

Create a CUJ script for the feature:

```python
# scripts/capture-task-flow.py
import asyncio
from playwright.async_api import async_playwright

async def capture():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page(viewport={"width": 390, "height": 844})
        
        # Step 1: Initial view
        await page.goto("http://localhost:5173")
        await page.wait_for_timeout(1000)
        await page.screenshot(path="/tmp/cuj/01-initial.png")
        
        # Step 2: Create task
        await page.click("button:has-text('Add Task')")
        await page.fill("input[name='title']", "New Task")
        await page.screenshot(path="/tmp/cuj/02-form.png")
        
        # Step 3: Submit
        await page.click("button:has-text('Save')")
        await page.wait_for_timeout(500)
        await page.screenshot(path="/tmp/cuj/03-created.png")
        
        await browser.close()

asyncio.run(capture())
```

### Create GIF

```bash
convert -delay 150 -loop 0 /tmp/cuj/*.png docs/gifs/task-flow.gif
```

### Update CUJs.md

```markdown
# Critical User Journeys

## Create Task

**Goal:** Create a new task from the board view.

**Steps:**
1. View board with existing tasks
2. Click "Add Task" button
3. Fill in task title
4. Submit form

![Create Task](./gifs/task-flow.gif)
```

## Step 4: Commit Workflow

```bash
# Stage everything
git add src/components/TaskCard.tsx
git add src/components/TaskCard.test.tsx
git add src/components/TaskCard.stories.tsx
git add docs/gifs/task-flow.gif
git add docs/CUJs.md

# Commit with conventional message
git commit -m "feat(TaskCard): add TaskCard component with tests and docs

- Add TaskCard component with status variants
- Add unit tests for render and click behavior
- Add Storybook stories for all states
- Add CUJ GIF for task creation flow"

# Push
git push origin feature/task-card
```

## Checklist

Before marking a UI feature complete:

- [ ] Component created with TypeScript types
- [ ] Unit tests passing
- [ ] Storybook story with key variants
- [ ] Responsive behavior tested (mobile story)
- [ ] CUJ screenshots/GIF captured
- [ ] CUJs.md updated
- [ ] All tests green
- [ ] Committed with docs

## File Structure

```
src/
├── components/
│   ├── TaskCard.tsx          # Component
│   ├── TaskCard.test.tsx     # Unit tests
│   └── TaskCard.stories.tsx  # Storybook
├── pages/
│   └── BoardPage.tsx         # Page using component
docs/
├── CUJs.md                   # Journey documentation
└── gifs/
    └── task-flow.gif         # Visual proof
scripts/
└── capture-task-flow.py      # CUJ capture script
```

## Related Skills

- **cuj-screenshots**: Detailed CUJ capture workflow
- **storybook**: Advanced Storybook patterns

## Tips

- Run tests continuously: `bun test --watch`
- Keep Storybook running during development
- Capture screenshots after every significant UI change
- Don't commit broken tests — TCR discipline
- Share GIF links in PRs for visual review
