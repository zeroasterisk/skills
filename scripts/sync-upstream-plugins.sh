#!/usr/bin/env bash
# Wrapper to run sync-upstream-plugins.py with proper directory context
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
exec python3 "$SCRIPT_DIR/sync-upstream-plugins.py" "$@"
