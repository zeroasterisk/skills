---
name: repo-health-audit
description: Polyglot orchestrator for holistic repository code health, security, and dependency upgrade passes across Go, Node/TypeScript, Python, Swift/macOS, Rust, Dockerfiles, and GitHub Actions. Detects repo stacks and companion repos, delegates to specialist audit and readability skills, triages P0/P1/P2 upgrades, and choreographs safe remediation, lockstep releases, and Before/After scorecards. Use for full repo health sweeps, dependency freshness assessments, or pre-release maintenance passes.
license: Apache-2.0
metadata:
  version: "1.0.0"
---

# Repository Health & Dependency Upgrade Audit (Orchestrator)

## Overview

`repo-health-audit` is a lightweight orchestrator skill for running end-to-end **code health, security, and dependency upgrade** passes across single-language or polyglot repositories (and their sibling example or canary repositories).

Rather than duplicating language-specific linting or CVE rules, it:
1. **Auto-detects repository stacks, manifests, CI workflows, lockstep version markers, and git sync/dirty state** via `scripts/detect-stack.mjs`.
2. **Delegates to the appropriate specialist skills in parallel** (both intra-plugin and optional cross-plugin skills by skill ID).
3. **Applies a disciplined P0 / P1 / P2 upgrade rubric** (CVEs & floors vs. safe minor/patch freshness vs. holding clean major bumps) and filters intentional readability false positives.
4. **Choreographs safe remediation & release verification** (git sync preflight, preserving unrelated dirty files, MVS/lockstep propagation, CI-safe registry publish gating, and a verified Before → After scorecard).

> **Scope boundary:** For narrow single-domain tasks (e.g., only running `govulncheck`, only auditing `npm audit`, or only reviewing a Go PR for readability), invoke the individual specialist skill directly (`go-security-audit`, `node-security-audit`, `go-readability`, `python-readability`, etc.). Use `repo-health-audit` for **multi-axis health sweeps and dependency upgrade passes**.

## Bundled Resources

- `scripts/detect-stack.mjs` — Zero-dependency Node.js scanner that inspects one or more repositories for languages, manifests (`go.mod`, `package.json`, `pyproject.toml`, `Package.swift`, `*.xcodeproj`, `Cargo.toml`, `Dockerfile`, `.github/workflows`), lockstep version parity, git remote/dirty status, recommended specialist skills, and optional `--outdated` dependency freshness in Markdown or `--json`.
- [Dependency Triage, Readability Filtering & Release Playbook](references/triage-and-release-playbook.md) — P0/P1/P2 upgrade tiers, readability false-positive triage, multi-repo MVS/lockstep release sequencing, and the Before → After scorecard template.

## Specialist Skill Delegation Matrix

Delegate to each matching specialist skill discovered by `scripts/detect-stack.mjs` (invoke cross-plugin skills by skill ID; degrade gracefully if an optional plugin is not installed):

| Axis | Detected Signals | Delegate To (Skill ID) | Scope |
| :--- | :--- | :--- | :--- |
| **Go Security & Containers** | `go.mod`, `Dockerfile*` | `go-security-audit` | Same plugin (`repo-authoring`) |
| **Node / TS Security & CI** | `package.json`, `.github/workflows/*` | `node-security-audit` | Same plugin (`repo-authoring`) |
| **Go Code Health** | `*.go` | `go-readability` | Cross-plugin (`go-readability`) |
| **Python Code Health** | `*.py`, `pyproject.toml`, `requirements*.txt` | `python-readability` | Cross-plugin (`python-readability`) |
| **Swift / macOS Health** | `*.swift`, `Package.swift`, `*.xcodeproj` | `quick-bounce-assessor`, `macos-hig-reviewer` | Cross-plugin (`macos-performance`, `macos-hig`) |
| **GitHub Actions (Gemini CLI)** | Workflows using `run-gemini-cli` | `geminicli-github-action-review` | Cross-plugin (`mcp-security`) |
| **MCP Security** | `mcp.json`, `.mcp.json`, MCP server code | `mcp-auditor` | Cross-plugin (`mcp-security`) |
| **Release & Docs Hygiene** | `CHANGELOG.md`, `README.md` | `changelog-manager`, `make-readme` | Same plugin (`repo-authoring`) |
| **Issue Tracker Recovery** | `.beads/` Dolt lock or sync errors | `bd-dolt-troubleshooter` | Cross-plugin (`beads-workflow`) |

For ecosystems without a dedicated security skill yet (such as **Python** `pip-audit` / `uv`, **Swift** `Package.resolved`, or **Rust** `cargo audit` / `cargo outdated`), follow the ecosystem freshness checks in `references/triage-and-release-playbook.md`.

## Workflow

### Phase 1: Read-Only Discovery & Assessment (Plan First)

1. **Run Stack & Freshness Discovery** across the primary repository and any companion/canary sibling repositories:
   ```bash
   ./scripts/detect-stack.mjs /path/to/repo /path/to/companion-repo --outdated --json
   ```
   Or omit `--json` for a human-readable Markdown summary.
2. **Check Git Hygiene Signals**:
   - Note if `summary.anyBehindRemote` is `true` (must `git fetch && git pull --rebase` before any lockfile edits).
   - Note if `summary.anyDirtyWorktree` is `true` (inspect and preserve unrelated local edits; never blindly run `git add .`).
   - Note if `summary.anyLockstepMismatch` is `true`.
3. **Invoke Matching Specialist Skills in Parallel (Read-Only)**:
   - Load and run every applicable skill from `recommendedSkills` (e.g., `go-security-audit` with `--vulncheck`, `node-security-audit`, `go-readability` self-audit, `python-readability` Ruff/Mypy check, `quick-bounce-assessor`).
4. **Triage & Present Unified Plan** using `references/triage-and-release-playbook.md`:
   - Group findings into **P0** (CVEs, stdlib/runtime/CI floors), **P1** (safe minor/patch dependency bumps & actionable readability fixes), and **P2** (clean major bumps to hold/defer).
   - Filter readability false positives (keep documented intentional idioms such as process-wide ADC `context.Background()` or defensive nil guards).
   - Recommend whether a patch release is warranted (e.g., cutting a Go library patch release so downstream modules inherit CVE fixes via Go MVS).

### Phase 2: Safe Remediation & Verification (After Approval)

1. **Preflight Sync**: Fetch and sync any behind branches across primary and companion repos before touching lockfiles.
2. **Apply Upstream Fixes First**:
   - Bump language/runtime floors before running dependency upgrades (e.g., `go get go@1.26.10` before `go get -u ./...`).
   - Apply P0 and approved P1 dependency upgrades, CI/engine floor pins, and genuine readability fixes.
   - Rebuild any committed generated/embedded artifacts (e.g., `make bundle`).
3. **Verify Primary Repo**:
   - Run full lint, typecheck, unit/race tests, and vulnerability scanners (`govulncheck`, `npm audit`, `pip-audit`, etc.).
   - If direct cloud/API SDKs were upgraded and the user approves quota usage, run live smoke tests (e.g., `make test-live`).
4. **Cut Lockstep Release & Propagate Downstream** (when requested):
   - Update lockstep version files and `CHANGELOG.md` (delegating to `changelog-manager`).
   - Stage only explicit changed files (preserving any unrelated local work), commit, tag, push, and publish the GitHub Release.
   - Propagate Go MVS upgrades to in-repo `examples/*` (`GOWORK=off`) and companion repositories.
   - **CI-Safe Registry Gating**: Never point downstream `package.json` / `pyproject.toml` at an unpublished registry version; verify visibility first (`npm view <pkg> version`) or verify locally with tarballs while handing off interactive 2FA publish commands to the user.
5. **Re-Run Scanners & Emit Before → After Scorecard**:
   - Re-run every specialist scanner invoked in Phase 1 and report the compact **Before → After Scorecard** confirming `0` reachable CVEs, compliant runtime floors, and passing CI/tests.
