# Go & Container Security Remediation Playbook

## 1. Resolving the `go >= 1.26.0` Minimum Version Cascade

Late-2026 releases of core Google Cloud, gRPC, OpenTelemetry, and `golang.org/x/*` packages declare `go 1.26.0` in their upstream `go.mod` manifests:
- `cloud.google.com/go/auth@v0.24.2`, `cloud.google.com/go/firestore@v1.29.2`, `cloud.google.com/go/storage@v1.70.0`
- `golang.org/x/crypto@v0.58.0`, `golang.org/x/net@v0.62.0`, `golang.org/x/oauth2@v0.37.0`, `golang.org/x/sys@v0.49.0`, `golang.org/x/text@v0.43.0`
- `go.opentelemetry.io/otel@v1.47.0` and `go.opentelemetry.io/contrib/*@v0.72.0`
- `google.golang.org/api@v0.310.0` and `google.golang.org/grpc@v1.85.0`

### Why `go get -u ./...` Fails on `go 1.25.x`
When a project's `go.mod` specifies `go 1.25.5` (even with `GOTOOLCHAIN=auto`), running `go get -u ./...` attempts to resolve the latest versions of all transitive dependencies under the current `1.25.5` module floor and aborts with:
```text
go: cloud.google.com/go/auth@v0.24.2 requires go >= 1.26.0 (running go 1.25.5; GOTOOLCHAIN=go1.25.5+auto)
```

### The Fix Sequence & The `GOTOOLCHAIN=auto` Patch-Pin Trap
1. Update the `go` directive in `go.mod` **first** to **`go 1.26.10`** (`go get go@1.26.10`) so `GOTOOLCHAIN=auto` activates the patched `go1.26.10` toolchain immediately.
   - **Beware `go 1.26.0`**: If the host's base binary is `go1.25.5` with `GOTOOLCHAIN=go1.25.5+auto` and `go.mod` declares `go 1.26.0` (with no `toolchain` directive), Go downloads and compiles against `go1.26.0` rather than `go1.26.10`, leaving **36 reachable standard-library vulnerabilities** (`GO-2026-4599` through `GO-2026-6809` in `net/http`, `crypto/tls`, `crypto/x509`, `html/template`, `mime/multipart`, and `os`) unpatched.
2. Run the full upgrade and tidy pass:
   ```bash
   go get go@1.26.10
   go get -u ./...
   go mod tidy
   ```

---

## 2. Triaging `govulncheck` Call-Graph vs. Module Advisories

Always run `govulncheck` after upgrading `go.mod`:

```bash
go run golang.org/x/vuln/cmd/govulncheck@latest ./...
```

### Interpreting the Three Output Tiers
1. **Symbol Results (`Your code is affected by N vulnerabilities`)**:
   - Must be **0**. Any non-zero count means your compiled binary actively calls a vulnerable function.
2. **Package Results (`N vulnerabilities in packages you import`)**:
   - Should be **0**. Indicates an imported package contains a vulnerability even if the vulnerable symbol isn't directly reached.
3. **Module Results (`N vulnerabilities in modules you require`)**:
   - Use `-show verbose` to inspect module-level findings.
   - **Known Uncalled Deprecation Notice (`GO-2026-5932`)**: `golang.org/x/crypto@v0.58.0` triggers a module-level informational notice for `golang.org/x/crypto/openpgp` (`Fixed in: N/A` because the subpackage is deprecated and unmaintained). As long as your code does not import `golang.org/x/crypto/openpgp`, your code is unaffected (`0` symbol and `0` package vulnerabilities).

---

## 3. Key Direct Dependency Upgrade Notes (Genkit, MCP, GenAI, SQLite)

| Module | Patched Target | Notes & Build Flags |
| :--- | :--- | :--- |
| `github.com/firebase/genkit/go` | `v1.14.0` | Compatible with `google.golang.org/genai@v1.77.0` and `dotprompt/go`. |
| `github.com/mark3labs/mcp-go` | `v1.5.0` | `v0.58.0` $\rightarrow$ `v1.5.0` is drop-in compatible when handlers use `req.GetString`, `req.RequireString`, `req.GetFloat`, `req.GetInt`, and `req.GetStringSlice`. |
| `google.golang.org/genai` | `v1.77.0` | Latest Google GenAI SDK for Go. |
| `github.com/mattn/go-sqlite3` | `v1.14.52` | When using SQLite FTS5 virtual tables, always pass `-tags "sqlite_fts5"` to `go build` and `go test`. |

---

## 4. Container (`Dockerfile`) & Cloud Build Hardening

1. **Match `FROM golang:<ver>-bookworm` to `go.mod`**:
   - When `go.mod` is bumped to `go 1.26.x`, update `Dockerfile` Stage 1 from `FROM golang:1.25-bookworm` to `FROM golang:1.26-bookworm`. Leaving the builder image on `1.25` forces Docker/Cloud Build to download a newer Go toolchain inside the container on every build or fail outright.
2. **Apply Debian Security Upgrades in Both Stages**:
   - Always include `apt-get upgrade -y` before installing packages in `debian:bookworm-slim` runtime images so base libraries (`openssl`, `libc6`, `libsqlite3-0`, `ca-certificates`) receive the latest security patches:
     ```dockerfile
     RUN apt-get update && apt-get upgrade -y && apt-get install -y --no-install-recommends \
         ca-certificates \
         libsqlite3-0 \
         && rm -rf /var/lib/apt/lists/*
     ```
3. **Keep `.gitignore` and `.gcloudignore` Synchronized**:
   - Exclude `.serena`, `.beads`, `.dolt`, and `docs-bundle` in both `.gitignore` and `.gcloudignore` so local MCP/IDE caches and issue-tracker databases are never uploaded to Cloud Build during `gcloud run deploy --source`.
