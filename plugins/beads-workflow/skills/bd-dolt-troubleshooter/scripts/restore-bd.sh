#!/usr/bin/env bash
#
# restore-bd.sh - Rebuild, restore, and synchronize beads (bd) with full CGO & ICU capabilities.
# Resolves schema drift and CGO degradation across macOS and Linux environments.
#
set -euo pipefail

TARGET="${1:-main}"
PKG_URL="github.com/steveyegge/beads/cmd/bd"
GO_BIN_DIR="${GOBIN:-$HOME/go/bin}"

echo "==> Restoring 'bd' client (target revision/tag: @${TARGET})..."

# 1. OS and ICU detection for CGO support
OS="$(uname -s)"
export CGO_ENABLED=1

if [ "$OS" = "Darwin" ]; then
    echo "    Detected macOS (Darwin). Probing Homebrew for ICU C++ headers..."
    if ! command -v brew >/dev/null 2>&1; then
        echo "    [ERROR] Homebrew is not installed or not in PATH."
        echo "    Please install Homebrew and run: brew install icu4c"
        exit 1
    fi

    # Probe default icu4c first, then check for versioned formulas (e.g. icu4c@78)
    ICU_PREFIX=""
    if brew --prefix icu4c >/dev/null 2>&1; then
        ICU_PREFIX="$(brew --prefix icu4c)"
    else
        for formula in $(brew list -1 2>/dev/null | grep -E '^icu4c@' | sort -V); do
            ICU_PREFIX="$(brew --prefix "$formula" 2>/dev/null || true)"
            if [ -n "$ICU_PREFIX" ]; then break; fi
        done
    fi

    if [ -z "$ICU_PREFIX" ] || [ ! -d "$ICU_PREFIX/include/unicode" ]; then
        echo "    [ERROR] Missing ICU C++ header files ('unicode/regex.h')."
        echo "    To fix CGO ICU compilation on macOS, run: brew install icu4c"
        exit 1
    fi

    echo "    Found ICU library prefix at: $ICU_PREFIX"
    export CGO_CFLAGS="-I$ICU_PREFIX/include ${CGO_CFLAGS:-}"
    export CGO_CPPFLAGS="-I$ICU_PREFIX/include ${CGO_CPPFLAGS:-}"
    export CGO_LDFLAGS="-L$ICU_PREFIX/lib ${CGO_LDFLAGS:-}"

elif [ "$OS" = "Linux" ]; then
    echo "    Detected Linux. Verifying ICU development libraries..."
    if command -v pkg-config >/dev/null 2>&1 && pkg-config --exists icu-uc icu-i18n 2>/dev/null; then
        echo "    Found ICU via pkg-config."
        export CGO_CFLAGS="$(pkg-config --cflags icu-uc icu-i18n) ${CGO_CFLAGS:-}"
        export CGO_LDFLAGS="$(pkg-config --libs icu-uc icu-i18n) ${CGO_LDFLAGS:-}"
    elif [ -f "/usr/include/unicode/regex.h" ] || [ -f "/usr/local/include/unicode/regex.h" ] || ls /usr/include/*/unicode/regex.h >/dev/null 2>&1; then
        echo "    Found ICU headers in system include directories."
    else
        echo "    [ERROR] Missing ICU C++ development libraries ('unicode/regex.h')."
        echo "    Please install ICU development libraries for your distribution:"
        echo "      Debian / Ubuntu : sudo apt-get install -y libicu-dev build-essential"
        echo "      RHEL / Fedora   : sudo dnf install -y libicu-devel gcc gcc-c++"
        echo "      Alpine Linux    : sudo apk add icu-dev gcc g++ musl-dev"
        echo "      Arch Linux      : sudo pacman -S --needed icu gcc"
        exit 1
    fi
else
    echo "    [WARN] Unrecognized OS ($OS); proceeding with default CGO compilation flags."
fi

# 2. Compile and install target release
echo "==> Compiling with CGO_ENABLED=1 from ${PKG_URL}@${TARGET}..."
if ! go install "${PKG_URL}@${TARGET}"; then
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
        echo "    Synchronizing shadowed binary: $bin <- $COMPILED_BIN"
        if [ -w "$bin" ] || [ -w "$(dirname "$bin")" ]; then
            cp -f "$COMPILED_BIN" "$bin"
        else
            echo "    [INFO] Root/sudo permission required to overwrite $bin"
            sudo cp -f "$COMPILED_BIN" "$bin"
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
echo "==> Restoration complete! Run 'bd doctor' and 'bd list' to verify schema and CGO diagnostics."
