---
name: go-security-audit
description: Audits and upgrades Go modules (go.mod/go.sum), runs govulncheck call-graph vs module-level vulnerability triage, and verifies Dockerfile Go toolchain alignment, OS package security patching, and .gcloudignore hygiene. Use when upgrading Go backends, resolving go >= 1.26.0 toolchain cascades, running govulncheck, or preparing Go services for Cloud Run deployment.
license: Apache-2.0
metadata:
  version: "1.1.0"
---

# Go & Container Security Audit Skill

## Overview

This skill provides a repeatable workflow and zero-dependency scanner to audit, upgrade, and harden Go backend repositories and their container images before Cloud Run or production deployment.

It covers four layers of Go and container security:
1. **Go Toolchain & Module Floor (`go >= 1.26.0`)**: Detecting when `go.mod` is on `go 1.25.x` or older, which causes `go get -u ./...` to fail against current Google Cloud, gRPC, OpenTelemetry, and `golang.org/x/{crypto,net,oauth2,sys,text}` releases unless the `go` directive in `go.mod` is bumped first.
2. **Call-Graph vs. Module Vulnerability Triage (`govulncheck`)**: Running `go run golang.org/x/vuln/cmd/govulncheck@latest ./...` to separate **reachable symbol vulnerabilities** (which must be `0`) from **uncalled module-level notices** (such as `GO-2026-5932` on deprecated `golang.org/x/crypto/openpgp` in `golang.org/x/crypto@v0.58.0`).
3. **Container Toolchain & Base OS Hardening (`Dockerfile`)**: Verifying that `FROM golang:<ver>-bookworm` in `Dockerfile` matches the `go` directive in `go.mod` (preventing Cloud Build failures or uncached toolchain downloads) and that runtime stages (`debian:bookworm-slim`) apply `apt-get update && apt-get upgrade -y`.
4. **Source Upload & Ignore Hygiene (`.gitignore` / `.gcloudignore`)**: Ensuring local agent and issue-tracker state directories (`.serena`, `.beads`, `.dolt`, `docs-bundle`) are excluded from git and Cloud Build source uploads.

## Bundled Resources

- `scripts/audit-go-repo.mjs` — Scans a repository or workspace directory (up to depth 5) for `go.mod` subprojects, checking `go` directive floors, `Dockerfile` builder/runtime alignment, `.gitignore` / `.gcloudignore` hygiene, git remote tracking status, and optional `govulncheck` summaries.
- [Go & Container Remediation Playbook](references/go-remediation-playbook.md) (`references/go-remediation-playbook.md`) — Detailed runbook for resolving `go >= 1.26.0` upgrade cascades, triaging `govulncheck` output, upgrading `mcp-go` / `genkit` / `genai` / `go-sqlite3`, and hardening multi-stage Dockerfiles.

## Workflow

### Step 1: Sync with `origin` & Run the Go Security Audit

Always fetch and verify git tracking status before modifying `go.mod` or `go.sum`, then run `./scripts/audit-go-repo.mjs` against a single repository or workspace:

```bash
git fetch origin
./scripts/audit-go-repo.mjs ~/projects/my-go-repo --vulncheck
./scripts/audit-go-repo.mjs ~/projects --vulncheck --json
```

For each discovered Go module (`go.mod`), `scripts/audit-go-repo.mjs` inspects:
- **Go Directive & Stdlib Security Floor**: Checks both whether `go` in `go.mod` meets `>= 1.26.0` (required for late-2026 module resolution) and whether it meets `>= 1.26.10` (preventing `GOTOOLCHAIN=auto` from pinning to an unpatched `go1.26.0`–`1.26.9` stdlib with 36 reachable CVEs).
- **Optional `govulncheck` Call-Graph Triage (`--vulncheck`)**: Runs `govulncheck -json ./...` and separates reachable **Symbol**, **Package**, and **Module** advisories while auto-identifying `GO-2026-5932` (`x/crypto/openpgp`) as an uncalled deprecation notice.
- **Dockerfile Alignment**: Compares `FROM golang:<ver>` in any repository `Dockerfile` against `go.mod`'s `go` major.minor version, and checks whether `apt-get upgrade -y` is present in Debian/Ubuntu stages.
- **Ignore File Parity**: Checks `.gitignore` and `.gcloudignore` for line-anchored `.serena`, `.beads`, and `.dolt` rules.
- **Git Sync Status**: Warns if the local branch is behind `origin` before dependency files are edited.

### Step 2: Upgrade Go Modules Without Toolchain Deadlock

Consult [Go & Container Remediation Playbook](references/go-remediation-playbook.md) for stack-specific upgrade guidance:

1. **Bump `go` Directive First**:
   - If `go.mod` declares `go 1.25.x` or older, update `go.mod` to `go 1.26.10` (or run `go get go@1.26.10`) **before** running `go get -u ./...`. Otherwise, `go get -u ./...` aborts when encountering `cloud.google.com/go/auth@v0.24.2`, `golang.org/x/crypto@v0.58.0`, or `google.golang.org/grpc@v1.85.0`.
2. **Upgrade & Tidy**:
   ```bash
   go get -u ./...
   go mod tidy
   ```
3. **Align `Dockerfile` Builder & OS Patching**:
   - Update `FROM golang:1.25-bookworm` to `FROM golang:1.26-bookworm` to match `go 1.26.x`.
   - Ensure `RUN apt-get update && apt-get upgrade -y && apt-get install -y --no-install-recommends ...` is present in both builder and runtime (`debian:bookworm-slim`) stages.

### Step 3: Build, Test & Run `govulncheck`

After upgrading `go.mod` and `Dockerfile`:
1. Build and run the full test suite (including CGO tags like `-tags "sqlite_fts5"` if applicable):
   ```bash
   go test -tags "sqlite_fts5" ./...
   ```
2. Run `govulncheck` across all packages:
   ```bash
   go run golang.org/x/vuln/cmd/govulncheck@latest ./...
   ```
3. Confirm **`Your code is affected by 0 vulnerabilities`** (0 reachable symbol vulnerabilities and 0 imported package vulnerabilities).
