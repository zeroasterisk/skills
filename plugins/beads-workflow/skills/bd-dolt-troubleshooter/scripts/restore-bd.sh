#!/usr/bin/env bash
#
# restore-bd.sh - Rebuild, restore, and synchronize beads (bd) with full CGO & ICU capabilities.
# Resolves schema drift and CGO degradation across macOS and Linux environments.
#
set -euo pipefail

TARGET="latest"
AUTO_MIGRATE=0
AUTO_CLEAN=0

while [ $# -gt 0 ]; do
    case "$1" in
        --main)
            TARGET="main"
            shift
            ;;
        --migrate)
            AUTO_MIGRATE=1
            shift
            ;;
        --clean-cache)
            AUTO_CLEAN=1
            shift
            ;;
        --help|-h)
            echo "Usage: restore-bd.sh [--main] [--migrate] [--clean-cache] [revision/tag]"
            echo ""
            echo "Options:"
            echo "  --main         Build against @main instead of @latest (use only when DB is ahead of all release tags)"
            echo "  --migrate      Automatically apply pending schema migrations (--force) and update repo ID"
            echo "  --clean-cache  Automatically run 'go clean -cache' if disk space is low (<1500 MB)"
            echo "  revision/tag   Target Git branch, tag, or commit on beads repo (default: latest)"
            exit 0
            ;;
        -*)
            echo "Unknown flag: $1"
            echo "Usage: restore-bd.sh [--main] [--migrate] [--clean-cache] [revision/tag]"
            exit 1
            ;;
        *)
            TARGET="$1"
            shift
            ;;
    esac
done

PKG_URL="github.com/steveyegge/beads/cmd/bd"
GO_BIN_DIR="${GOBIN:-$HOME/go/bin}"

echo "==> Restoring 'bd' client (target revision/tag: @${TARGET})..."

# 0. Disk Space Pre-flight Check
CHECK_DIR="$(go env GOCACHE 2>/dev/null || echo "$HOME")"
[ -d "$CHECK_DIR" ] || CHECK_DIR="$HOME"
AVAIL_KB=$(df -k "$CHECK_DIR" 2>/dev/null | awk 'NR==2 {print $(NF-2)}')
if [ -n "$AVAIL_KB" ] && [ "$AVAIL_KB" -eq "$AVAIL_KB" ] 2>/dev/null; then
    AVAIL_MB=$((AVAIL_KB / 1024))
    echo "    Disk space check: ${AVAIL_MB} MB available in $(dirname "$CHECK_DIR")."
    if [ "$AVAIL_MB" -lt 1500 ]; then
        if [ "$AUTO_CLEAN" -eq 1 ]; then
            echo "    [WARN] Available disk space is below 1500 MB. Automatically running 'go clean -cache'..."
            go clean -cache || true
        else
            echo "    [WARN] Available disk space is low (${AVAIL_MB} MB < 1500 MB). Beads dependencies require ~1-1.5 GB."
            echo "    Hint: If 'go install' fails with 'no space left on device', run 'go clean -cache' or pass --clean-cache."
        fi
    fi
fi

# 1. OS and ICU detection for CGO support (with gms_pure_go fallback)
OS="$(uname -s)"
export CGO_ENABLED=1
GO_TAGS=()

if [ "$OS" = "Darwin" ]; then
    echo "    Detected macOS (Darwin). Probing Homebrew for ICU C++ headers..."
    ICU_PREFIX=""
    if command -v brew >/dev/null 2>&1; then
        # Probe default icu4c first, then check for versioned formulas (e.g. icu4c@78)
        if brew --prefix icu4c >/dev/null 2>&1; then
            ICU_PREFIX="$(brew --prefix icu4c)"
        else
            for formula in $(brew list -1 2>/dev/null | grep -E '^icu4c@' | sort -V); do
                ICU_PREFIX="$(brew --prefix "$formula" 2>/dev/null || true)"
                if [ -n "$ICU_PREFIX" ]; then break; fi
            done
        fi
    fi

    if [ -n "$ICU_PREFIX" ] && [ -d "$ICU_PREFIX/include/unicode" ]; then
        echo "    Found ICU library prefix at: $ICU_PREFIX"
        export CGO_CFLAGS="-I$ICU_PREFIX/include ${CGO_CFLAGS:-}"
        export CGO_CPPFLAGS="-I$ICU_PREFIX/include ${CGO_CPPFLAGS:-}"
        export CGO_LDFLAGS="-L$ICU_PREFIX/lib ${CGO_LDFLAGS:-}"
    else
        echo "    [INFO] ICU C++ headers not found; building with CGO_ENABLED=1 -tags gms_pure_go (matches upstream release builds; full CGO & embeddeddolt enabled)."
        GO_TAGS=(-tags gms_pure_go)
    fi

elif [ "$OS" = "Linux" ]; then
    echo "    Detected Linux. Verifying ICU development libraries..."
    if command -v pkg-config >/dev/null 2>&1 && pkg-config --exists icu-uc icu-i18n 2>/dev/null; then
        echo "    Found ICU via pkg-config."
        export CGO_CFLAGS="$(pkg-config --cflags icu-uc icu-i18n) ${CGO_CFLAGS:-}"
        export CGO_LDFLAGS="$(pkg-config --libs icu-uc icu-i18n) ${CGO_LDFLAGS:-}"
    elif [ -f "/usr/include/unicode/regex.h" ] || [ -f "/usr/local/include/unicode/regex.h" ] || ls /usr/include/*/unicode/regex.h >/dev/null 2>&1; then
        echo "    Found ICU headers in system include directories."
    else
        echo "    [INFO] ICU C++ development headers not found; building with CGO_ENABLED=1 -tags gms_pure_go (matches upstream release builds; full CGO & embeddeddolt enabled)."
        GO_TAGS=(-tags gms_pure_go)
    fi
else
    echo "    [WARN] Unrecognized OS ($OS); proceeding with default CGO compilation flags."
fi

# 2. Compile and install target release
if [ "${#GO_TAGS[@]}" -gt 0 ]; then
    echo "==> Compiling with CGO_ENABLED=1 ${GO_TAGS[*]} from ${PKG_URL}@${TARGET}..."
    INSTALL_CMD=(go install "${GO_TAGS[@]}" "${PKG_URL}@${TARGET}")
else
    echo "==> Compiling with CGO_ENABLED=1 from ${PKG_URL}@${TARGET}..."
    INSTALL_CMD=(go install "${PKG_URL}@${TARGET}")
fi
if ! "${INSTALL_CMD[@]}"; then
    echo "    [ERROR] 'go install' failed."
    echo "    Hint: If this is an untagged branch or revision on main, verify that your network and Go module proxies are accessible."
    exit 1
fi

COMPILED_BIN="${GO_BIN_DIR}/bd"
if [ ! -f "$COMPILED_BIN" ]; then
    COMPILED_BIN="$(go env GOPROXY 2>/dev/null && go env GOPATH)/bin/bd"
    if [ ! -f "$COMPILED_BIN" ]; then
        echo "    [ERROR] Could not locate compiled 'bd' binary after go install."
        exit 1
    fi
fi
echo "    Successfully built binary at: $COMPILED_BIN"

# 3. PATH Synchronization (resolve PATH shadowing)
echo "==> Scanning system PATH for shadowed 'bd' binaries..."
ACTIVE_BIN="$(command -v bd 2>/dev/null || true)"
ALL_BINS="$(which -a bd 2>/dev/null | sort -u || echo "$COMPILED_BIN")"

for bin in $ALL_BINS; do
    if [ "$bin" != "$COMPILED_BIN" ]; then
        if [ "$(realpath "$bin" 2>/dev/null || true)" = "$(realpath "$COMPILED_BIN" 2>/dev/null || true)" ]; then
            echo "    Symlink to primary binary: $bin (up-to-date)"
            continue
        fi
        echo "    Symlinking shadowed binary: $bin -> $COMPILED_BIN"
        if [ -w "$bin" ] || [ -w "$(dirname "$bin")" ]; then
            ln -sf "$COMPILED_BIN" "$bin" || cp -f "$COMPILED_BIN" "$bin"
        else
            echo "    [INFO] Root/sudo permission required to update $bin"
            sudo ln -sf "$COMPILED_BIN" "$bin" || sudo cp -f "$COMPILED_BIN" "$bin"
        fi
    else
        echo "    Primary Go install directory binary: $bin (up-to-date)"
    fi
done

# Refresh command hash cache if running in a shell that supports it
hash -r 2>/dev/null || true

echo "==> Verification..."
FINAL_BIN="$(command -v bd 2>/dev/null || echo "$COMPILED_BIN")"
echo "    Active binary  : $FINAL_BIN"
echo "    Module details : $(go version -m "$FINAL_BIN" 2>/dev/null | grep -E '(mod|dep)\s+' | head -n 2 | tr -d '\n' || echo "built from source")"
echo ""

# 4. Post-build schema check & migration
if [ -d .beads ] && command -v "$FINAL_BIN" >/dev/null 2>&1; then
    echo "==> Checking local repository schema & fingerprint status..."
    SKEW_OR_MIG="$("$FINAL_BIN" migrate --inspect 2>&1 || true)"
    REPO_MISMATCH="$("$FINAL_BIN" doctor 2>&1 | grep -i "Database belongs to different repository" || true)"

    if echo "$SKEW_OR_MIG" | grep -qi -E "refusing to auto-apply|pending schema migration|schema version mismatch"; then
        if [ "$AUTO_MIGRATE" -eq 1 ]; then
            echo "    Pending schema migrations detected. Applying schema + metadata migrations with --force (--migrate active)..."
            "$FINAL_BIN" migrate schema --force || true
            "$FINAL_BIN" migrate --force || true
            "$FINAL_BIN" vc commit -m "chore(bd): commit config working set" 2>/dev/null || true
        else
            echo "    [NOTE] Pending schema migrations detected."
            echo "    To apply migrations as the designated migrator, run:"
            echo "      bd migrate schema --force && bd migrate --force"
            echo "    (Or re-run: $0 --migrate ${TARGET})"
        fi
    fi

    if [ -n "$REPO_MISMATCH" ]; then
        if [ "$AUTO_MIGRATE" -eq 1 ]; then
            echo "    Repo ID mismatch detected. Updating repo fingerprint (--migrate active)..."
            "$FINAL_BIN" migrate --update-repo-id --yes || true
        else
            echo "    [NOTE] Repo ID mismatch detected."
            echo "    To update repo fingerprint, run:"
            echo "      bd migrate --update-repo-id --yes"
        fi
    fi
fi

echo "==> Restoration complete! Run 'bd doctor' and 'bd list' to verify schema and CGO diagnostics."
