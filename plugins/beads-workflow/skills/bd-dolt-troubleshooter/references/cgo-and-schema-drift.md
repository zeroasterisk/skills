# CGO Requirements & Schema Drift Resolution

When interacting with a shared beads (`bd`) Dolt database across automated agents, CI pipelines, or multiple team machines, developers often encounter database schema version mismatches. Understanding why built-in terminal suggestions can backfire is essential to maintaining database consistency and full diagnostic capabilities.

## 1. The CLI Error Recommendation Trap

When your local `bd` binary encounters a database schema ahead of its compiled version, it throws an error such as:
```
schema version mismatch: database is at v58, binary knows up to v53 (5 migrations ahead)

  Your bd binary is stale. Queries for dropped or renamed columns will fail
  with cryptic SQL errors (e.g. "column X could not be found in any table in scope").

  Rebuild from main:
    CGO_ENABLED=0 go build -tags gms_pure_go ./cmd/bd

  Or install the latest release:
    CGO_ENABLED=0 go install -tags gms_pure_go github.com/steveyegge/beads/cmd/bd@latest
```

**WARNING:** Following the built-in terminal recommendation above creates a **Double Trap** in multi-agent workflows:

1. **The `@latest` vs. `@main` Trap:** In active repositories, automated coding agents frequently compile `bd` directly from `@main`, automatically applying schema migrations forward (e.g., to v58). Running `go install ...@latest` re-downloads the last published release tag (e.g., `v1.1.0`), which only incorporates earlier schemas (e.g., v53). You remain permanently stranded behind the database schema.
2. **The `CGO_ENABLED=0` Trap:** Compiling with `CGO_ENABLED=0 -tags gms_pure_go` bypasses native CGO C++ ICU regex bindings (`unicode/regex.h`). While this allows compilation on systems lacking local ICU headers, it disables embedded SQLite and Dolt diagnostic test suites in `bd doctor`. Over 15 core database and maintenance checks degrade and report `Skipped: requires CGO`.

---

## 2. Why Pure-Go Mode (`CGO_ENABLED=0`) Degrades `bd doctor`

Beads integrates embedded SQLite and Dolt SQL syntax checkers, dependency DAG analyzers, and lock contention tests that depend on native CGO drivers and `dolthub/go-icu-regex`. 

When compiled in pure-Go mode (`CGO_ENABLED=0`), `bd doctor` silently degrades, outputting:
```
MAINTENANCE (2/3 passed)
  ⚠  Dolt Locks: Skipped: requires CGO

OTHER
  ⚠  Orphaned Dependencies: Skipped: requires CGO
  ⚠  Child-Parent Dependencies: Skipped: requires CGO
  ⚠  Duplicate Issues: Skipped: requires CGO
  ⚠  Test Pollution: Skipped: requires CGO
  ⚠  Stale Closed Issues: Skipped: requires CGO
  ⚠  Stale Molecules: Skipped: requires CGO
  ⚠  Persistent Mol Issues: Skipped: requires CGO
  ⚠  Stale MQ Files: Skipped: requires CGO
  ⚠  Patrol Pollution: Skipped: requires CGO
```

To retain complete diagnostic integrity and prevent hidden database corruption or lock contention, **always compile with `CGO_ENABLED=1` and linked ICU library headers**.

---

## 3. Automated Resolution (Recommended)

Instead of manually resolving ICU compiler flags or hunting down shadowed binary installations across your PATH, execute the bundled cross-platform restoration utility:

```bash
# Safe default — rebuild against @latest (highest stable tag) with full CGO + ICU support
# and symlink shadowed PATH binaries:
scripts/restore-bd.sh

# If the DB was already migrated past @latest by an unreleased main build:
scripts/restore-bd.sh --main

# Or target a specific release tag/pseudo-version:
scripts/restore-bd.sh v1.3.4
```

What `scripts/restore-bd.sh` does automatically:
* **Safe Target Selection:** Defaults to `@latest` so routine upgrades do not pull unreleased `@main` SQL migrations that would skew sibling repos; accepts `--main` or an explicit `<tag|commit>` when needed.
* **OS & ICU Discovery:** Probes macOS Homebrew (`brew --prefix icu4c` or versioned packages like `icu4c@78`) or Linux system include paths / `pkg-config`, exporting required `CGO_CFLAGS`, `CGO_CPPFLAGS`, and `CGO_LDFLAGS`.
* **CGO Compilation:** Invokes `CGO_ENABLED=1 go install github.com/steveyegge/beads/cmd/bd@<target>`.
* **PATH Symlink Synchronization:** Scans `which -a bd` to identify duplicate or shadowed binary installations (such as `~/.local/bin/bd` taking precedence over `~/go/bin/bd`) and symlinks them (`ln -sf`) to the primary Go binary so both immediate and future `go install` upgrades stay synchronized.

---

## 4. Cross-Platform CGO & ICU Manual Setup

If you prefer to compile manually or are configuring an automated CI runner, ensure native ICU development libraries are installed and referenced before building with `CGO_ENABLED=1`.

### macOS (`Darwin`)
Apple macOS does not bundle ICU development headers in standard Xcode toolchain paths (`/usr/include`). You must install ICU via Homebrew and explicitly instruct the CGO compiler where to locate the library:

```bash
# 1. Install icu4c via Homebrew
brew install icu4c

# 2. Resolve prefix and export CGO flags before running go install or go build
ICU="$(brew --prefix icu4c)"    # Or icu4c@<N>, e.g. $(brew --prefix icu4c@78)
export CGO_ENABLED=1
export CGO_CFLAGS="-I$ICU/include"
export CGO_CPPFLAGS="-I$ICU/include"
export CGO_LDFLAGS="-L$ICU/lib"

# 3. Compile and install against main
go install github.com/steveyegge/beads/cmd/bd@main
```

### Linux (`Linux`)
On most Linux distributions, ICU libraries lodge directly inside system compiler include paths (`/usr/include/unicode/regex.h`) or can be discovered via `pkg-config`, requiring zero custom flag export once installed:

| Distribution | Package Installation Command |
|---|---|
| **Debian / Ubuntu** | `sudo apt-get update && sudo apt-get install -y libicu-dev build-essential` |
| **RHEL / Fedora / Alma** | `sudo dnf install -y libicu-devel gcc gcc-c++` |
| **Alpine Linux** *(Docker/CI)* | `sudo apk add icu-dev gcc g++ musl-dev` |
| **Arch Linux** | `sudo pacman -S --needed icu gcc` |

Manual Linux compilation command after installing development packages:
```bash
CGO_ENABLED=1 go install github.com/steveyegge/beads/cmd/bd@main
```

---

## 5. PATH Shadowing & Version Verification

After compiling or upgrading `bd`, always verify that your system shell is not running a stale, shadowed binary located earlier in your PATH (e.g. `~/.local/bin/bd` shadowing `~/go/bin/bd`):

```bash
# Use inspect-binary.sh to detect shadowed executables and check module pseudo-versions:
scripts/inspect-binary.sh

# Or synchronize manually:
cp -f ~/go/bin/bd "$(which bd)" && hash -r
go version -m "$(which bd)"
```
