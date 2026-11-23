# Dependency Triage, Readability Filtering & Release Playbook

Reference guide for `repo-health-audit` covering upgrade priority tiers, cross-ecosystem dependency freshness triage, readability false-positive handling, and safe multi-repo release choreography.

---

## 1. Upgrade Classification Rubric (P0 / P1 / P2)

Security audits identify **vulnerabilities**; a health pass also encounters **non-vulnerable outdated dependencies**. Classify every finding into one of three tiers before editing manifests:

| Tier | Criteria | Action | Examples |
| :--- | :--- | :--- | :--- |
| **P0 — Security & Runtime Floors** | Reachable CVEs (`govulncheck` Symbol/Package > 0, `npm audit` > 0, `pip-audit` > 0), unpatched stdlib/runtime floors (`go < 1.26.10`, Node `< 22.23.4`), CI workflow floating/vulnerable pins, container OS patches, or `run-gemini-cli` prompt-injection gaps. | **Remediate immediately.** | `golang.org/x/net v0.38.0 -> v0.63.0`, `google.golang.org/grpc v1.66.2 -> v1.85.0`, `go 1.26.1 -> 1.26.10`, CI `node-version: '22' -> '22.23.4'`. |
| **P1 — Safe Minor / Patch Freshness** | Non-breaking patch or minor upgrades on active direct dependencies or test runners, plus actionable code-health / readability fixes. | **Upgrade & verify with full tests (and live smoke tests if SDKs changed).** | `google.golang.org/genai v1.77.0 -> v1.79.1`, `go-cmp v0.6.0 -> v0.7.0`, `vitest 5.1.0 -> 5.1.1`, `ruff` minor bump. |
| **P2 — Clean Major Upgrades (0 CVEs)** | Major-version jumps on packages with zero known vulnerabilities that risk breaking compiler, type, or API changes. | **Hold & document.** Defer to a dedicated migration task unless the user explicitly asks for the major jump. | `typescript 6.0.3 -> 7.0.2`, `@types/node 24 -> 26` while `engines.node` is `>=22.23.4`, Swift language-mode 5 -> 6. |

### Ecosystem-Specific Freshness Checks (Read-Only)

- **Go**: `GOWORK=off go list -m -u all` (distinguish direct vs. indirect; remember Go Minimal Version Selection (MVS) propagates minimum patched versions from a library's `go.mod` to all downstream consumers once released).
- **Node / TypeScript**: `npm outdated` / `pnpm outdated` + `npm audit` (respect exact-pin vs. range policies and coupled pin tests detected by `node-security-audit`).
- **Python**: Inspect `pyproject.toml` (`requires-python`, dependencies) and run `uv pip list --outdated` or `.venv/bin/pip list --outdated` inside the project's virtualenv; if `pip-audit` or `uvx pip-audit` is available, run it against the lockfile/venv.
- **Swift / macOS**: Inspect `Package.swift` and `Package.resolved` pins, Swift tools version, strict concurrency settings (`SwiftLanguageMode`), and Xcode deployment targets; delegate performance/HIG checks to `quick-bounce-assessor` and `macos-hig-reviewer`.
- **Rust (if detected)**: `cargo outdated` / `cargo audit` when installed, checking `rust-version` MSRV in `Cargo.toml`.

---

## 2. Readability & Static-Analysis False-Positive Filtering

Automated readability scanners (such as `go-readability`'s self-audit or `ruff` / `SwiftLint`) flag syntactic patterns that are occasionally **intentional**. Never blindly refactor every scanner match:

1. **Inspect context before editing**: Read the surrounding comments and docstrings.
2. **Preserve documented intentional idioms**:
   - Process-wide `context.Background()` used intentionally so auth/ADC token refresh outlives individual HTTP requests.
   - Defensive nil-context guards (`if parentCtx == nil { parentCtx = context.Background() }`) inside constructors.
   - Intentional `//nolint:...` or `# noqa: ...` directives accompanied by a rationale comment.
3. **Fix genuine nits**: Empty-parens test failure strings (`Func() failed` when inputs/env can be shown), unformatted code, missing doc comments on exported symbols, unused imports, or dead code.
4. **Report both fixed and intentionally kept items** in the final summary so reviewers know every scanner hit was triaged.

---

## 3. Safe Execution & Multi-Repo Release Choreography

When remediating a library repository and its companion consumer/canary repositories (e.g., `my-lib` + `my-lib-examples`), follow this exact sequence to avoid lockfile merge conflicts, broken CI, or stale bundles:

### Step A: Git Preflight (Every Target Repo)
1. Run `git fetch origin` in **every** target and companion repository before modifying any files.
2. If any branch is behind `origin` (`behind > 0`), pull/rebase cleanly first — lockfiles (`go.sum`, `package-lock.json`, `uv.lock`) do not auto-merge cleanly.
3. Inspect `git status --short`. If unfamiliar local modifications exist (e.g., local editor/harness files or uncommitted user notes), **preserve them untouched** and stage only explicit paths (`git add <files...>`), never blind `git add .` or `git add -A`.

### Step B: Upstream Library Remediation & Build
1. Apply toolchain floor bumps first (e.g., `go get go@1.26.10` before `go get -u ./...`).
2. Apply P0 and approved P1 dependency updates, CI floor pins, and readability fixes.
3. Rebuild any committed generated/embedded artifacts (e.g., `make bundle` / `browser/dist/*.js`, generated schemas, or lockfiles).
4. Run full local verification: lint, typecheck, unit/race tests, bundle-freshness checks, and vulnerability scans (`govulncheck`, `npm audit`, `pip-audit`).
5. When direct SDKs changed (e.g., `google.golang.org/genai`), run optional live smoke tests (`make test-live`) if credentials/quota are available and approved.

### Step C: Lockstep Patch Release & Downstream Propagation
1. Update lockstep version markers (`version.go`, `package.json`, `ts/index.ts`, `pyproject.toml`, etc.) and curate `CHANGELOG.md` (via `changelog-manager`).
2. Commit, tag (`git tag -a vX.Y.Z -m "..."`), push `main` and tag, and create the GitHub Release (`gh release create`).
3. **Go MVS Propagation**: Once the tag is pushed and indexed by `proxy.golang.org`, upgrade standalone in-repo `examples/*/go.mod` (`GOWORK=off go get <mod>@vX.Y.Z && GOWORK=off go mod tidy`) and companion repos' `go.mod` files. Verify `govulncheck` drops to `0 / 0 / 0` downstream.
4. **CI-Safe npm / PyPI Publish Gating**:
   - If registry publishing requires interactive 2FA/OTP, **never** bump downstream `package.json` or `pyproject.toml` to the unpublished version before verifying registry visibility (`npm view <pkg> version`).
   - Instead, verify locally via tarball (`make use-tarball && make verify`), keep downstream manifests pointed at the latest *published* registry version until publish completes, and hand the user the exact publish + follow-up command.

---

## 4. Standard Before → After Scorecard Template

Always re-run every applicable specialist scanner after remediation and present a compact scorecard:

```markdown
### Before → After Audit Scorecard

| Check | `<primary-repo>` | `<companion-repo>` |
| :--- | :--- | :--- |
| **Go Security (`govulncheck` Sym/Pkg/Mod)** | 10 / 2 / 33 → **0 / 0 / 0** | 10 / 2 / 33 → **0 / 0 / 0** |
| **Go Stdlib Floor (`>= 1.26.10`)** | 5 below → **5/5 OK** | 5 below → **5/5 OK** |
| **Node Audit + Runtime Floor (`>= 22.23.4`)** | 3 CI/engines → **0 findings** | 4 CI/engines → **0 findings** |
| **Code Health / Readability** | 1 nit fixed; 2 intentional kept | **Clean** |
| **Verification Gates** | `make lint`, `make test`, `make build`, `make test-live` PASS | `make verify` PASS |
```
