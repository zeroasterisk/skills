# UI Developer Skill

Complete frontend development workflow with component isolation, testing, and visual documentation.

## What This Skill Does

Guides AI agents through a structured development loop:

1. **Component Development** - Create components with TypeScript + unit tests
2. **Storybook Isolation** - Test variants in isolation
3. **Integration** - Wire into pages
4. **Visual Documentation** - Capture CUJ screenshots and GIFs
5. **Commit** - Push with complete docs

## The Loop

```
Make change → Run tests → Update story → Capture CUJ → Commit
```

Every UI change gets:
- Unit tests ✓
- Storybook story ✓
- Visual documentation ✓

## Files

- `SKILL.md` - Full workflow instructions for OpenClaw
- `GEMINI.md` - Instructions for Gemini CLI

## Usage

### OpenClaw
```bash
cp -r ui-developer ~/.openclaw/workspace/skills/
```

### Gemini CLI
```bash
gemini -i ui-developer/GEMINI.md "add a TaskCard component"
```

## See Also

- [cuj-screenshots](../cuj-screenshots/) - Detailed CUJ capture instructions
- [storybook](../storybook/) - Advanced Storybook patterns
