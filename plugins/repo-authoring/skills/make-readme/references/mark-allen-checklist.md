# README Checklist

Source: Mark Allen, ["How to Write a Great README for Your Public GitHub Project"](https://www.markcallen.com/how-to-write-a-great-readme-for-your-public-github-project/), Everyday DevOps, 04 May 2025. Examples below are adapted from his post's [env-secrets](https://github.com/markcallen/env-secrets) case study.

Work through these sections in order. Each entry has: what it's for, what a good example looks like, and the fix to apply when it's missing or weak.

## 1. Clear Project Description

**What it's for:** The first thing a stranger reads. It decides whether they keep reading.

**Good example:**
```markdown
# env-secrets

A simple CLI to manage secrets in `.env` files and upload them to GitHub Actions secrets or AWS Parameter Store.
```

**Fix when missing/weak:**
- Put a one-sentence, no-buzzword description directly under the `# Title` heading.
- State what the tool *actually does*, not what category it belongs to ("a powerful, flexible framework for..." tells the reader nothing).
- If the title alone doesn't make the purpose obvious, the first sentence must.

## 2. Quick Installation Instructions

**What it's for:** Let people get the thing installed without hunting.

**Good example:**
```bash
npm install -g env-secrets
```

**Fix when missing/weak:**
- Lead with the package-manager one-liner if one exists (`npm install`, `pip install`, `brew install`, `go install`, etc.).
- If install requires cloning/building, give the exact, copy-pasteable commands — not a description of the steps.
- Don't bury installation below a wall of badges or a long philosophy section.

## 3. Immediate Usage Example

**What it's for:** Prove the thing works before asking for more of the reader's attention.

**Good example:**
```bash
env-secrets encrypt .env
```

**Fix when missing/weak:**
- Show the single most common command or code snippet right after installation, in a fenced code block.
- Explain what it does in one line, not a paragraph.
- Cover the common cases up front; save edge cases and full option lists for later in the doc or a separate reference.

## 4. Local Development Setup

**What it's for:** Lets a contributor go from `git clone` to a running dev environment without asking questions.

**Good example:**
```bash
git clone https://github.com/markcallen/env-secrets.git
cd env-secrets
npm install
npm run dev
```

**Fix when missing/weak:**
- Give the exact clone/install/run sequence.
- Call out required environment variables, ports, and prerequisite versions (Node, Python, Docker) explicitly — don't assume the reader has the "right" version already.
- If setup differs from end-user installation (step 2), keep the two clearly separate so contributors don't confuse them.

## 5. Publish / Deploy Process

**What it's for:** Documents how *maintainers* ship a new release, for teammates and future-you.

**Good example:**
```bash
npm version patch
npm publish
```

**Fix when missing/weak:**
- If the project publishes to a registry (npm, PyPI, Docker Hub, a Homebrew tap, etc.), document the exact release commands.
- If the project has no publish/deploy step (e.g. an internal script, a personal tool), skip this section entirely rather than including empty boilerplate.

## 6. Encourage Contributions

**What it's for:** Signals the project is open to outside help and tells people how to start.

**Good example:**
```markdown
## Contributing

Pull requests are welcome! For major changes, please open an issue first to discuss what you'd like to change.

Make sure to update tests as appropriate.
```

**Fix when missing/weak:**
- State plainly whether PRs are welcome and whether an issue should come first for larger changes.
- Link out to `CONTRIBUTING.md` or `CODE_OF_CONDUCT.md` if they exist instead of duplicating their content inline.
- If the project explicitly does *not* accept outside contributions, say so — that's also useful information.

## 7. Use Markdown Well

**What it's for:** Formatting is part of usability, not decoration.

**Checklist:**
- Headings (`##`) organize sections — don't rely on bold text as a heading substitute.
- Commands and config live in fenced code blocks (triple backticks), with a language hint when useful.
- Steps and requirements are lists, not run-on sentences.
- Related tools/docs are linked, not just named.
- Consider status badges near the top (CI build, package version, license) for at-a-glance health.

**Fix when missing/weak:** Reformat offending sections; don't just add content on top of bad structure.

## 8. Optional but Helpful Extras

**What it's for:** Extra scaffolding that pays off as a project grows in size or audience.

**Consider adding, especially for larger projects:**
- A **Table of Contents** once the README has more than ~5 sections.
- Screenshots or terminal output examples for anything visual or CLI-heavy.
- Architecture diagrams for non-trivial systems.
- An FAQ section for recurring questions.
- Troubleshooting tips for known rough edges.

**Fix when missing/weak:** Not every project needs all of these. Add the ones that reduce real support burden or confusion for this specific project — don't pad the README with sections nobody will read.

## Closing Test

Mark Allen's own closing prompt, useful as a final gut-check after drafting or editing:

> "Would I know what to do if I saw this for the first time?"
