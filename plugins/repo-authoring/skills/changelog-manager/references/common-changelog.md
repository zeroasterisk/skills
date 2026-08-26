# Common Changelog Reference

Common Changelog is a style guide for changelogs, adapted from and a stricter subset of [Keep a Changelog](https://keepachangelog.com/). It focuses on a clean changelog stemming from a clean git history.

## Guiding Principles

1.  **Write changelogs for humans.** Communicate the impact of changes.
2.  **Sort content by importance.** Skip content that isn't important.
3.  **Link each change to further information.** Use reference-style links at the bottom.
4.  **A clean git history strengthens a clean changelog.**

## Format

*   **File Name**: Must be `CHANGELOG.md`.
*   **Version Format**: Must start with second-level heading `## VERSION - DATE` (e.g., `## 1.0.1 - 2019-08-24`).
*   **Date Format**: ISO 8601 (`YYYY-MM-DD`).
*   **Releases Order**: Sorted latest-first according to Semantic Versioning rules, even if an older branch version is published later.

### Release Sections

A release must have markdown content that is either:
1.  One or more **change groups**;
2.  A **notice** followed by zero or more **change groups**.

#### Notice Section (Optional)
A single-sentence paragraph with markdown emphasis (italics). Useful for:
- Pointing to an upgrade guide (e.g. `_If you are upgrading: please see [UPGRADING.md](UPGRADING.md)._`)
- Pointing out first releases (e.g. `_First release._`)
- Highlighting yanked releases.

#### Change Group Prefixes
Use standard bold prefixes to call out high-impact actions inside change bullet points, particularly breaking changes:
- `- **Breaking:** remove write() method from public API (01e3a64)`

## Writing Guidelines

*   **Generate a draft**: Pull git commits and issue tracker items first.
*   **Remove noise**: Filter out trivial commits like "fix typo", format tweaks, and chore tasks.
*   **Rephrase changes**: Do not copy commit messages verbatim. Rewrite them for clarity.
*   **Merge related changes**: Group multiple micro-tasks into a single higher-level feature change summary.
*   **Avoid Conventional Commit verbatim duplication**: Avoid using conventional commits directly as headers, which can be repetitive and hard to read.
