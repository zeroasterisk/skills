---
name: changelog-manager
description: Generates, updates, and curates a CHANGELOG.md file adhering to the Keep a Changelog v1.1.0 specification and Common Changelog style guide by analyzing bd issue tracking history and git commit history.
license: Apache-2.0
metadata:
  version: "1.0.0"
---

# Changelog Manager Skill

This skill provides an expert workflow for generating and maintaining high-quality, curated `CHANGELOG.md` files, combining the modular groupings of [Keep a Changelog v1.1.0](https://keepachangelog.com/en/1.1.0/) with the stricter formatting and git-alignment rules of [Common Changelog](https://common-changelog.org/).

## Core Philosophy

- **Write for Humans**: Changelogs are designed for human end-users and developers to understand the impact of a release. Avoid dumping raw git logs or conventional commits verbatim.
- **Curated over Automated**: While automation drafts, a human or expert agent must edit, rephrase, and merge related changes to eliminate noise.
- **Git Alignment**: A clean changelog is strengthened by a clean git history. Clean up commit/issue data prior to drafting.

## Reference Guides (Progressive Disclosure)

For detailed formatting guidelines and examples, read the following specialized guides:
*   [Keep a Changelog Guide](references/keep-a-changelog.md) - Explains standard semantic categories (`Added`, `Changed`, `Deprecated`, `Removed`, `Fixed`, `Security`) and structural principles.
*   [Common Changelog Guide](references/common-changelog.md) - Outlines strict curation standards, the use of `Notice` blocks, and bold impact prefixes.

---

## Workflow

Follow these steps precisely when asked to generate or update a project's changelog:

### 1. Gather Change Sources

Collect data from all available project histories:
*   **Git Commits**: Run `git log --oneline -n 100` or search since the last tagged version.
*   **Beads Issues (`bd`)**: Run `bd list --status closed --no-pager` or export the beads database to JSON/JSONL using `bd list --all --json` to inspect closed tasks and completed epics.
*   **Release Tags**: Run `git tag -l` to find existing version tags and their dates.

### 2. Check for an Existing `CHANGELOG.md` (CRITICAL)

Before writing any content, check if a `CHANGELOG.md` already exists at the project root:

*   **If it does NOT exist**: Create a fresh file starting with the standard header:
    ```markdown
    # Changelog

    All notable changes to this project will be documented in this file.

    The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/)
    and [Common Changelog](https://common-changelog.org/),
    and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).
    ```
*   **If it DOES exist**: Do NOT overwrite the entire file. You must read and update it carefully:
    *   **Preserve History**: All past version blocks (e.g., `## [1.0.0] - YYYY-MM-DD` and older) must remain completely unmodified.
    *   **Handling `[Unreleased]`**:
        *   If adding unreleased changes and an `## [Unreleased]` block already exists, merge your new entries into the existing categories, avoiding duplicates.
        *   If no `## [Unreleased]` block exists, insert it directly below the main introduction header.
    *   **Drafting a New Release**:
        *   Change the existing `## [Unreleased]` header to the new version header with today's date: `## [NEW_VERSION] - YYYY-MM-DD`.
        *   Insert a fresh, empty `## [Unreleased]` block directly above this new version block.
        *   Update the markdown reference links at the bottom of the file (e.g., update comparison URLs like `[Unreleased]: https://github.com/owner/repo/compare/vNEW_VERSION...HEAD` and add `[NEW_VERSION]: https://github.com/owner/repo/compare/vOLD_VERSION...vNEW_VERSION`).

### 3. Identify the Target Version and Date

*   Determine if you are drafting an `[Unreleased]` section or preparing a specific version release (e.g., `[1.0.0] - YYYY-MM-DD`).
*   Version headers must use the format `## [VERSION] - DATE` (where `VERSION` is a valid semver version without the "v" prefix, and `DATE` is in the `YYYY-MM-DD` ISO-8601 format).

### 4. Add Optional Notices (Common Changelog)

Immediately below the release heading, you may include a single-sentence *Notice* paragraph in italics if applicable:
*   For the initial release: `_Initial release._`
*   For major upgrades: `_If you are upgrading: please see [UPGRADING.md](UPGRADING.md)._`
*   For yanked releases or zero-code releases, clarify here.

### 5. Categorize Changes Strictly

Sort all notable changes into the six standard categories defined by Keep a Changelog:

1.  `### Added` - For new features.
2.  `### Changed` - For changes in existing functionality.
3.  `### Deprecated` - For soon-to-be removed features.
4.  `### Removed` - For now removed features.
5.  `### Fixed` - For any bug fixes.
6.  `### Security` - In case of vulnerabilities.

> [!IMPORTANT]
> Never use custom category names. If a change doesn't fit, rephrase it so it fits one of the six standard categories. Avoid listing chores, CI/CD setup, or formatting tweaks unless they are highly notable for developers.

### 6. Curate and Rewrite (The Common Changelog Standard)

*   **Remove Noise**: Filter out tracking commands (e.g., `bd close`, `bd update`, tracker refactors), tiny formatting commits, and minor merge commits.
*   **Synthesize Tasks**: If a feature or bug was implemented across multiple small tasks/commits (e.g. `abra-go-242.1`, `abra-go-242.2`, `abra-go-242.3`), synthesize them into a single, high-quality, high-level entry.
*   **Signaling Impact (Prefixes)**: Bold key impact signals inside change items, especially for breaking changes or critical performance notes (e.g., `- **Breaking:** remove write() method...` or `- **Performance:** transition to server-side cursor pagination...`).
*   **Link to Issues/PRs**: Add references to `bd` issue IDs (e.g. `[abra-go-242]`) or Pull Requests to give users full context.

### 7. Format and Write `CHANGELOG.md`

*   List versions in reverse chronological order (newest on top).
*   Use reference-style markdown links at the bottom of the file (e.g., `[1.0.0]: https://github.com/owner/repo/releases/tag/v1.0.0`) to keep the unrendered markdown clean and readable.
