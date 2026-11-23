---
name: node-security-audit
description: Audits and remediates Node.js runtime, npm/pnpm/yarn dependency, and GitHub Actions supply-chain vulnerabilities across local and remote GitHub repositories, while respecting repository-specific version-pinning tests and CI guardrails. Use when reviewing Node or Astro/Vite/Starlight apps for CVEs, running fleet-wide security sweeps across ~/projects or GitHub repos, or upgrading pinned dependencies safely.
license: Apache-2.0
metadata:
  version: "1.0.0"
---

# Node Security Audit & Remediation Skill

## Overview

This skill provides a repeatable workflow and zero-dependency automation scripts to discover, triage, and remediate Node.js security vulnerabilities across a fleet of repositories without breaking repository-specific test suites, lockfile invariants, or CI workflows.

It covers three layers of Node.js security:
1. **Runtime & CI Floor**: Checking local Node binaries, `engines.node`, `.nvmrc` / `.node-version`, and `.github/workflows/*.yml` (`actions/setup-node`) against active Node.js security releases (e.g., the October 21, 2026 releases: `v22.23.4`, `v24.22.1`, `v26.12.1` fixing `CVE-2026-111497` Brotli RCE, `CVE-2026-105482` DNS NUL truncation, and `CVE-2026-105483` / `CVE-2026-106069` TLS hostname bypasses).
2. **Package Dependency Vulnerabilities**: Running structured `npm audit` (or `pnpm`/`yarn` audit) across root and subproject manifests (`site/`, `docs-site/`, `web/`, `ui/`, `frontend/`), separating direct vs. transitive advisories and identifying minimal non-breaking version upgrades (such as `astro >= 7.4.2` for `GHSA-26w7-cxv4-gfx2` AVIF RCE and `sharp >= 0.35.5` for `GHSA-wq5f-xc86-pv6w`).
3. **Pre-Flight Guardrail & Supply-Chain Detection**: Scanning test suites and workflows *before* modifying `package.json` to detect exact-pin gates (e.g., `pins.test.mjs`), forbidden semver range operators (`^` / `~`), and CI workflow meta-tests (`workflows.test.mjs`).

## Bundled Resources

- `scripts/discover-node-repos.sh` — Scans a local workspace directory (such as `~/projects`, up to depth 5) and optionally queries GitHub (`gh repo list`) to inventory all repositories and subprojects containing `package.json`.
- `scripts/scan-remote-repos.mjs` — Uses the GitHub Trees API (`gh api`) to inspect uncloned remote GitHub repositories and list every repository and path containing a `package.json` without needing to clone non-Node repositories first.
- `scripts/audit-repo.mjs` — Audits a target repository or workspace directory, outputting a structured JSON or Markdown report covering Node runtime floors, `npm`/`pnpm` audit vulnerability counts by severity, direct vs. transitive fix paths, pin policy (`exact` vs. `range`), and coupled test files that reference dependency versions.
- [Remediation Playbook](references/remediation-playbook.md) (`references/remediation-playbook.md`) — Detailed runbook for upgrading Node runtimes, patching Astro/Starlight/Vite/Sharp stacks, handling peer-dependency ceilings via `overrides`, avoiding false-fix downgrades (`braces@3.0.3`), updating coupled pin tests, and preserving shared host/container `node_modules`.

## Workflow

### Step 1: Discover Node Projects Across Local & Remote Repos

Run `scripts/discover-node-repos.sh` to enumerate all local Node subprojects (up to depth 5), and run `scripts/scan-remote-repos.mjs` to inspect uncloned GitHub repositories via the GitHub Trees API:

```bash
./scripts/discover-node-repos.sh ~/projects
./scripts/scan-remote-repos.mjs ~/projects --all-languages
```

### Step 1.5: Sync with `origin` Before Editing Lockfiles

Always run `git fetch && git pull --rebase` in each target repository **before** editing `package.json` or regenerating `package-lock.json` / `pnpm-lock.yaml`. Lockfiles do not auto-merge cleanly if `origin/main` has advanced since the local checkout was last pulled.

### Step 2: Run the Structured Security & Guardrail Audit

Run `scripts/audit-repo.mjs` against a single repository or across all discovered projects in `~/projects`:

```bash
# Audit a single repository (human-readable Markdown table + details)
./scripts/audit-repo.mjs ~/projects/my-target-repo

# Audit all local repositories in ~/projects and emit JSON
./scripts/audit-repo.mjs ~/projects --all --json
```

For each discovered Node subproject (`package.json`), `scripts/audit-repo.mjs` inspects:
- **Git Remote Parity**: Checks whether the repository's tracking branch is behind `origin` before lockfiles are modified.
- **Pin Style & Overrides**: Whether `dependencies` and `devDependencies` use exact pins (`7.4.2`) or semver ranges (`^7.4.2`), and lists active `"overrides"` / `"pnpm.overrides"` security pins (e.g., `@grpc/grpc-js`, `re2js`).
- **Node Floor**: `engines.node`, `.nvmrc`, `.node-version`, and `.github/workflows/*.yml` `node-version` entries vs. minimum patched Node security floors (`22.23.4`, `24.22.1`, `26.12.1`).
- **Guardrail Coupling**: Any test files under `tests/` or `test/` that assert exact version strings, `PINNED` maps, `engines.node` floors, or lockfile invariants.
- **Vulnerability Triage**: Direct and transitive vulnerabilities from `npm audit --json`, grouped by severity (`critical`, `high`, `moderate`, `low`) and whether a non-breaking semver fix is available.

### Step 3: Remediate Following Repository Conventions

Consult [Remediation Playbook](references/remediation-playbook.md) for stack-specific guidance. Always follow these rules when applying fixes:

1. **Preserve Pin Policy**:
   - If the subproject uses **exact pins** (no `^` or `~`), never run bare `npm audit fix` if it introduces range operators or leaves `package.json` out of sync with `package-lock.json`. Instead, query the patched versions (`npm view <pkg> version`), update `package.json` with exact `X.Y.Z` versions, and regenerate `package-lock.json`.
   - Avoid unnecessary major-version bumps on clean packages (e.g., keep `typescript` on `5.9.x` during a security patch if `5.9.3` has zero advisories and `7.x` is a major bump).
2. **Update Coupled Guardrail Tests in Lockstep**:
   - When `scripts/audit-repo.mjs` flags coupled test files (such as `site/tests/pins.test.mjs`), update the `PINNED` constant map and any `engines.node` floor assertions in the same change.
   - Distinguish between **real manifest assertions** and **synthetic control fixtures** in test files—only update assertions bound to the live manifest unless the control fixture imports from the manifest.
3. **Avoid Cross-Device Link (`EXDEV`) & Cross-Platform `node_modules` Clobbering**:
   - In shared host/container workspaces (where macOS and Linux share a mounted directory), **never overwrite `node_modules` with container-specific native binaries** (`esbuild`, `rollup`, `rolldown`, `oxc`). Use `--package-lock-only` (`npm`) or `--lockfile-only` (`pnpm`) to refresh lockfiles and clear `npm audit` / `pnpm audit` without touching `node_modules`:
     ```bash
     # npm lockfile-only refresh
     rm -f package-lock.json && npm install --package-lock-only

     # pnpm lockfile-only refresh (preserving v9.0 lockfile format)
     COREPACK_ENABLE_AUTO_PIN=0 corepack pnpm@10.34.6 install --lockfile-only
     ```
   - If a full install or build is required in a container environment where `/tmp` is `tmpfs`, set `TMPDIR` on the home filesystem (`mkdir -p ~/.tmp && export TMPDIR="$HOME/.tmp"`) or build in an isolated `/tmp/opencode/` copy.

### Step 4: Two-Tier Verification

After applying updates to a subproject:
1. Verify `npm audit` reports **0 vulnerabilities**.
2. Run the project build (`npm run build`).
3. Run fast unit/guardrail tests first (`npm run test:fast` if available), followed by full typechecking and end-to-end tests (`npm test`).
