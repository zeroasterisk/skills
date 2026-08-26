---
name: aaif-notebooklm-sync
description: Synchronizes all AAIF Working Group (wg-*) and foundation repositories, meeting minutes, charters, monthly reports, deliverables, reference architectures, and open pull requests from https://github.com/aaif/* into Google NotebookLM (https://notebooklm.google.com/notebook/3f4ea1ea-fe19-4afe-8cbe-ac5f9950412d). Features full state-based lifecycle management (skip unchanged, update modified, add new, remove deleted/merged) with gcert LOAS validation, bi-weekly lookback synthesis, and automated public GitHub Gist reporting.
license: Apache-2.0
---

# AAIF Working Groups to NotebookLM Sync & Bi-Weekly Executive Reporting

Directly synchronizes all documentation from `https://github.com/aaif/*` into Google NotebookLM using the NotebookLM MCP proxy (`corp-mcp-proxy`), generates 2-week lookback executive syntheses and visual artifacts (Bento Grid Infographic and Presentation Slide Deck), and automatically publishes dated public GitHub Gists.

## Pipeline Features
- **Direct Markdown Ingestion**: Ingests files directly as `textContent` markdown sources into NotebookLM without external Drive dependencies.
- **Full Lifecycle Management**:
  - **SKIP**: If content has not changed (SHA-256 hash match), skips API calls.
  - **UPDATE**: If a file or report was edited, updates the source in NotebookLM.
  - **ADD**: Automatically ingests new meeting notes, monthly reports, charters, and open PR drafts.
  - **REMOVE**: Automatically removes stale sources when PRs merge or files are deleted.
- **Bi-Weekly Lookback Executive Digest & Artifacts**:
  - Synthesizes 2-week activity lookback across all 8 Working Groups.
  - Generates NotebookLM Infographic (Bento Grid) and Presentation Slide Deck (PDF).
  - Automatically publishes a dated public GitHub Gist under Alan's account (`zeroasterisk`).
- **Smart Session & `gcert` Awareness**:
  - Validates `gcert` LOAS credentials before making MCP calls.
  - Automatically runs when logging in or opening a shell if $\ge 7$ days have passed since the last sync.

## Target Notebook & Canonical Gist
- **Notebook URL**: [https://notebooklm.google.com/notebook/3f4ea1ea-fe19-4afe-8cbe-ac5f9950412d](https://notebooklm.google.com/notebook/3f4ea1ea-fe19-4afe-8cbe-ac5f9950412d)
- **Latest Gist**: [https://gist.github.com/zeroasterisk/59c7333a9ce97c41935dc0ec66358ee1](https://gist.github.com/zeroasterisk/59c7333a9ce97c41935dc0ec66358ee1)

## CLI Commands

### Run Full Sync & Publish Gist
```bash
python3 /usr/local/google/home/alanblount/Code/AAIF/scripts/sync_aaif_to_notebooklm.py --force
```

### Run Bi-Weekly Digest & Gist Generator Only
```bash
python3 /usr/local/google/home/alanblount/Code/AAIF/scripts/generate_weekly_digest.py
```

### Run If Due ($\ge 7$ Days & `gcert` Active)
```bash
python3 /usr/local/google/home/alanblount/Code/AAIF/scripts/sync_aaif_to_notebooklm.py --if-due
```
