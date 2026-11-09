# Node.js & Astro/Starlight Security Remediation Playbook

## 1. October 2026 Node.js Runtime Security Advisories

On October 21, 2026, the Node.js project published security releases for all active release lines:
- **Node 22 LTS**: `v22.23.4`
- **Node 24 LTS**: `v24.22.1`
- **Node 26 Current**: `v26.12.1`

### Key Vulnerabilities Addressed
- **`CVE-2026-111497` (High)**: Node.js Brotli decoder out-of-bounds write permitting Remote Code Execution (RCE) across 22.x, 24.x, and 26.x.
- **`CVE-2026-105482` (High)**: `dns.resolve` truncates domain names containing NUL characters (`22.x`, `24.x`, `26.x`).
- **`CVE-2026-106069` (High)**: TLS certificate hostname bypass when the host loosely resolves to an IP address (`22.x`, `24.x`, `26.x`).
- **`CVE-2026-105483` (High)**: TLS certificate hostname bypass when the IP is written with fullwidth digits (`24.x`, `26.x`).
- **Dependency Updates**: Bundled `undici`, `c-ares`, `OpenSSL`, `SQLite`, and `ca-cert` (eMudhra Intermediate CA compromise).

### Runtime Upgrade Checklist
1. **Local Binary (`~/.local/lib/nodejs` or `nvm`)**:
   - Verify `node -v` meets `>=22.23.4` (for 22.x) or `>=24.22.1` (for 24.x).
   - When installing official tarballs into `~/.local/lib/nodejs/`, always verify against `SHASUMS256.txt` before updating symlinks in `~/.local/bin/{node,npm,npx}`.
2. **`package.json` `engines.node`**:
   - If a project declares `"engines": { "node": ">=22.19.0" }`, bump to `">=22.23.4"`.
   - Check if `tests/pins.test.mjs` or `tests/workflows.test.mjs` asserts the exact string `">=22.19.0"` or compares `process.versions.node` against `[22, 19, 0]`, and update both in lockstep.

---

## 2. Astro / Starlight / Sharp Stack Vulnerabilities

Documentation and catalog sites built on Astro 7.x and `@astrojs/starlight` commonly exhibit the following cluster of advisories when pinned to pre-October 2026 versions:

| Package | Vulnerable Range | Patched Pin | Advisories Fixed |
| :--- | :--- | :--- | :--- |
| `astro` | `<=7.3.2` | `7.4.2` | `GHSA-26w7-cxv4-gfx2` (Critical 9.8 AVIF RCE), `GHSA-98hj-9722-w3j8` (JSX/MDX `<script>`/`<style>` XSS), `GHSA-mpr7-6m5w-76rw` (View Transitions CSS injection) |
| `sharp` | `<0.35.5` | `0.35.5` | `GHSA-rgj7-g3m4-5g8c` (`libheif` heap overflow), `GHSA-wq5f-xc86-pv6w` (`librsvg` `CVE-2026-96889`) |
| `@astrojs/starlight` | `<=0.41.7` | `0.42.6` | Updates `@expressive-code/core` (`postcss-selector-parser` `<7.1.6`) and `smol-toml` (`<=1.8.0`) |
| `@astrojs/check` | `<=0.9.10` | `0.9.12` | Aligns typecheck diagnostics with Astro `7.4.2` |
| `yaml` | `<=2.8.3` | `2.9.1` | Latest stable 2.x release |
| Transitive (`vite`, `undici`, `devalue`, `fast-uri`, `svgo`, `js-yaml`, `http-cache-semantics`, `source-map-js`) | Various | Resolved via lockfile | Refreshing `package-lock.json` after bumping the direct pins above resolves all transitive High/Moderate findings to `0 vulnerabilities`. |

---

## 3. Handling Exact-Pin Guardrail Suites (`pins.test.mjs`)

Several repositories enforce strict dependency reproducibility via `tests/pins.test.mjs`:
1. **No Range Operators**: Every entry in `dependencies` and `devDependencies` is matched against `/^\d+\.\d+\.\d+(?:-[0-9A-Za-z.-]+)?$/`. Caret (`^`) or tilde (`~`) ranges will fail the test suite.
2. **Explicit `PINNED` Map**: Update `const PINNED = { ... }` in `tests/pins.test.mjs` to match the new exact versions in `package.json`.
3. **Leave Control Fixtures Intact**: `pins.test.mjs` includes synthetic control tests (e.g., `pins control: the range detector rejects...` and `duplicate-key control:...`) that use literal version strings like `"7.2.4"` or `"5.9.3"` inside inline JSON strings to test the detector functions themselves. Do not blindly find-and-replace version strings across the entire test file; only update `PINNED` and `engines.node` assertions.
4. **Clean Lockfile Regeneration**:
   ```bash
   # If node_modules is shared across macOS host and Linux container, prefer --package-lock-only:
   rm -f package-lock.json
   npm install --package-lock-only
   npm audit

   # For cross-platform devDependencies (e.g., @tauri-apps/cli-darwin-arm64 on Linux), pass --force:
   rm -f package-lock.json
   npm install --package-lock-only --force
   npm audit

   # For pnpm v9.0 lockfiles, preserve lockfileVersion '9.0' and any license header:
   COREPACK_ENABLE_AUTO_PIN=0 corepack pnpm@10.34.6 install --lockfile-only
   pnpm audit
   ```
   Confirm `lockfileVersion: 3` (for npm) and that `lock.packages[""].dependencies` matches `package.json`.

---

## 4. Field-Tested Lessons from Fleet Remediation

1. **Always `git pull --rebase` Before Touching Lockfiles**:
   - If `origin/main` has advanced (e.g., Dependabot or a teammate bumped a package), rebasing a newly generated `package-lock.json` or `pnpm-lock.yaml` will always conflict. Pull first, then audit and regenerate.
2. **Deep Subproject Nesting (`maxDepth: 5`)**:
   - Subprojects frequently live 3–4 levels inside a repository (`samples/desktop-app/frontend`, `experimental/webmcp-live/frontend`, `experiments/run-veo-run/frontend`). Always scan to depth 5 when auditing from a top-level workspace like `~/projects`.
3. **Peer-Dependency Ceilings & Targeted `overrides` (`astro-mermaid`, `rehype-katex`)**:
   - When `npm audit` suggests a major upgrade (e.g., `mermaid@12.2.0`) that conflicts with a wrapper's peer range (`astro-mermaid@2.1.0` requires `mermaid@^10.0.0 || ^11.0.0`), stay on the latest compatible minor (`mermaid@^11.17.2`) and add an `"overrides"` (npm) or `"pnpm": { "overrides": ... }` (`pnpm@10.x`) entry for the vulnerable transitive dependency (such as `"katex": "^0.19.0"` or `"postcss-selector-parser": "^7.1.6"`).
4. **False-Fix Downgrades & Unpatched `braces <=3.0.3` (`GHSA-vfj7-8cjw-p6xm`)**:
   - `braces@3.0.3` has no upstream patched version (`>3.0.3`), which causes `npm audit` to recommend either a major upgrade to `tailwindcss@4.3.3` or a *downgrade* of `@custom-elements-manifest/analyzer` from `0.11.0` to `0.2.4` (before it used `globby`). Never run `npm audit fix --force` blindly; inspect whether `fixAvailable.version` is actually a downgrade or a breaking major change for a dev-only CLI tool.
5. **Minimal Major-Line Patched Targets for `vite`**:
   - Rather than jumping every project to `vite@8.3.5`, use the lowest patched release for the project's current major line:
     - `vite 8.x` $\rightarrow$ `^8.3.5`
     - `vite 7.x` $\rightarrow$ `^7.3.7`
     - `vite 5.x / 6.x` $\rightarrow$ `^6.4.5` (resolves both `esbuild <=0.24.2` and `vite <=6.4.3`)
6. **Respect Repository `AGENTS.md` Scope Exclusions**:
   - Check each repository's `AGENTS.md` before modifying subprojects (for example, `genmedia-creative-studio/AGENTS.md` explicitly prohibits modifying `experiments/`).
7. **Sync `overrides.<pkg>` When Updating Direct Dependencies (`EOVERRIDE`)**:
   - If `package.json` already declares `"overrides": { "vite": "..." }` (common in `rolldown-vite` or beta Vite projects), updating `devDependencies.vite` without updating `overrides.vite` to the exact same version string causes `npm install` to fail with `EOVERRIDE`. Always update both together.
8. **Targeted Overrides for False-Downgrade Chains (`firebase`, `gts`, `lit-audio-ui`)**:
   - **`firebase@12.x` / `firebase@13.x` / `@firebase/rules-unit-testing@4.x`**: Even in `firebase@13.1.0` (`@firebase/firestore@4.19.0`), upstream pins `@grpc/grpc-js` to `~1.9.0` and pulls vulnerable `re2js` (`GHSA-gg6h-894w-4m9c`), causing `npm audit` to recommend a breaking downgrade to `firebase@9.14.0` or `@firebase/rules-unit-testing@2.0.7`. Fix both cleanly in `package.json`:
     ```json
     "overrides": {
       "@grpc/grpc-js": "^1.14.7",
       "re2js": "^2.8.7"
     }
     ```
     *Note*: `firebase@13.x` subpackages (`@firebase/app`, `@firebase/auth`, `@firebase/firestore`) declare `engines: { "node": ">=24.12.0" }`, which emits non-fatal `npm warn EBADENGINE` warnings when building on Node 22 LTS.
   - **`gts@7.x` (`tmp <=0.2.5`)**: Fix via `"overrides": { "tmp": "^0.2.6" }`.
   - **`@ghchinoy/lit-audio-ui` (`@chenglou/pretext <=0.0.4`)**: Fix via `"overrides": { "@chenglou/pretext": "^1.0.0" }`.
9. **TypeScript 7 (`typescript@7.x`) Side-Effect CSS Imports (`TS2882`)**:
   - Upgrading `typescript` from `5.9.x` to `7.0.x` enables `noUncheckedSideEffectImports` by default. In Vite/Lit projects that import stylesheets directly (`import './styles/theme.css'`), `tsc` will fail with `error TS2882: Cannot find module or type declarations for side-effect import of './styles/theme.css'` unless `"types": ["vite/client"]` is added to `compilerOptions` in `tsconfig.json`.
10. **Vite 8 (Rolldown) `manualChunks` Function Syntax & Firebase Code Splitting**:
    - Upgrading from Vite 6 to Vite 8 (`^8.3.5`, powered by Rolldown) requires `build.rollupOptions.output.manualChunks` in `vite.config.ts` to use the function form `manualChunks(id)` rather than an object map.
    - To prevent monolithic bundles exceeding 500 kB, split `@firebase/firestore` (`vendor-firestore`) separately from `@firebase/app` + `@firebase/auth` (`vendor-firebase`), `lit` (`vendor-lit`), and `marked` (`vendor-marked`).
11. **Fast Remote Fleet Remediation via Blobless Clones**:
    - When remediating uncloned remote repositories discovered by `scripts/scan-remote-repos.mjs`, clone with `git clone --depth=1 --filter=blob:none` into `/tmp/opencode/remote-audit`, apply lockfile-only fixes, verify `0` vulnerabilities with `scripts/audit-repo.mjs`, push, and remove `/tmp/opencode/remote-audit`.
