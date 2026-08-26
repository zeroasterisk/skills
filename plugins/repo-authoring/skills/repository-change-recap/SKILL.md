---
name: repository-change-recap
description: Generates a structured weekly or custom timeframe commit recap for a repository. Looks for repository-specific categorization rules in .gemini/recap-rules.md or GEMINI.md before fetching git logs via git log --stat to accurately organize changes (e.g. core vs experiments). Supports optional audio generation.
license: Apache-2.0
metadata:
  version: "1.0.0"
---

# Repository Change Recap

This skill provides an expert workflow for generating high-quality, structured summaries of repository changes over a specific time window.

## Workflow

Follow these steps precisely when asked to generate a repository recap:

### 1. Determine the Time Window
*   Check the user's request for a specific time window.
*   If `--last-week`, use the last 7 days.
*   If `--previous-week`, use 14 to 7 days ago.
*   If no time window is specified, default to the last 7 days (`--since="7 days ago"`).

### 2. Discover Repository-Specific Rules (CRITICAL)
Before fetching commits, you **MUST** check if the current repository has specific rules for how to categorize changes.
*   Check for the existence of `.gemini/recap-rules.md` or look inside `GEMINI.md` for a "Recap Instructions" section.
*   If found, read these instructions carefully. They will tell you how to categorize changes based on directory structures (e.g., distinguishing between a core application and independently versioned monorepo packages/experiments).
*   If no specific rules are found, use default categorization (Features, Bug Fixes, Tooling, Docs).

### 3. Fetch Commits
*   Execute `git log --stat` (or `--name-only`) for the determined time window.
*   It is critical to fetch the *files modified* in each commit so you can accurately categorize them according to the repository-specific rules.

### 4. Analyze and Categorize Commits
*   Analyze the file paths modified in each commit to accurately bucket the changes into distinct categories, as defined by the repository's rules.
*   Pay special attention to version bumps in configuration files (like `package.json`, `pyproject.toml`, or Go modules) to note releases.

### 5. Generate the Recap
Generate a human-readable recap using the following strict structure:
*   **Executive Summary / Key Highlights:** A brief paragraph summarizing the most impactful changes across all categories.
*   **Categorized Sections:** Create detailed bullet points grouped by the categories determined in Step 4. Ensure you mention specific PR numbers and version bumps where applicable.
*   Save the recap to a markdown file in a `recaps/` directory (create it if it doesn't exist) with the filename `weekly_recap_YYYY-MM-DD.md`.

### 6. Generate Audio (Optional)
If the user specified `--with-audio`:
*   Read the content of the generated recap file.
*   Clean up the text to make it suitable for text-to-speech (e.g., remove markdown symbols, expand PR numbers to "Pull Request").
*   Split the text into chunks to avoid timeouts.
*   Use the `gemini_audio_tts` tool to generate a WAV audio file for each chunk.
*   Use the `ffmpeg_concatenate_media_files` tool to combine the audio chunks into a single WAV file.
*   Save the final audio file to the `recaps/` directory with the same name as the markdown file, but with a `.wav` extension.
*   Clean up the temporary audio files.

## Example Per-Repository Rules (`.gemini/recap-rules.md`)
```markdown
# Recap Rules

1. **Core Application**: Any changes outside of the `experiments/` directory. Look for version bumps in `pyproject.toml`.
2. **MCP Servers**: Changes within `experiments/mcp-genmedia/`. Check for Go module version bumps.
3. **Other Experiments**: Changes in `experiments/<name>/`.
```

## Macro Configuration (`~/.gemini/commands/recap.toml`)
```toml
description = "Generates a weekly commit recap"
prompt = "Generate a repository change recap for {{args}}. If --with-audio is provided, generate an audio narration."
```

