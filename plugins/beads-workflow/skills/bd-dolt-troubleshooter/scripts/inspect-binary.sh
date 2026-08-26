#!/usr/bin/env sh
# bd / Dolt troubleshooter — binary inspector.
#
# Inspects all installed copies of the 'bd' client CLI across PATH and common
# directories (~/go/bin, ~/.local/bin, /usr/local/bin, /opt/homebrew/bin).
# Extracting Go build metadata (module pseudo-versions, git commit revisions, and
# build timestamps) is critical for diagnosing Schema Version Skew across multiple
# machines, multi-agent setups, and shadowed local installations.
#
# Usage:
#   scripts/inspect-binary.sh

set -eu

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m'

red()    { printf "${RED}%s${NC}\n" "$*"; }
green()  { printf "${GREEN}%s${NC}\n" "$*"; }
yellow() { printf "${YELLOW}%s${NC}\n" "$*"; }
cyan()   { printf "${CYAN}%s${NC}\n" "$*"; }
bold()   { printf "${BOLD}%s${NC}\n" "$*"; }

info()   { printf "\n${BOLD}==> %s${NC}\n" "$*"; }

info "Searching for installed 'bd' binaries..."
ACTIVE_BIN=$(command -v bd || echo "")
if [ -z "$ACTIVE_BIN" ]; then
  red "No 'bd' binary found in current PATH."
  exit 1
fi

# Collect unique candidates from PATH and common locations
CANDIDATES=""
for path in $(which -a bd 2>/dev/null) "$HOME/go/bin/bd" "$HOME/.local/bin/bd" "/usr/local/bin/bd" "/opt/homebrew/bin/bd"; do
  [ -f "$path" ] || continue
  # check if path is already in CANDIDATES
  case " $CANDIDATES " in
    *" $path "*) ;;
    *) CANDIDATES="$CANDIDATES $path" ;;
  esac
done

COUNT=0
for bin in $CANDIDATES; do
  COUNT=$((COUNT+1))
done

bold "Found $COUNT binary installation(s)."

for bin in $CANDIDATES; do
  printf "\n"
  if [ "$bin" = "$ACTIVE_BIN" ]; then
    cyan "-----------------------------------------------------------------------"
    bold "[ACTIVE PATH BINARY] $bin"
    cyan "-----------------------------------------------------------------------"
  else
    yellow "-----------------------------------------------------------------------"
    bold "[SHADOWED BINARY]   $bin"
    yellow "-----------------------------------------------------------------------"
  fi
  
  # File metadata
  ls -lh "$bin" 2>/dev/null || true
  if [ -L "$bin" ]; then
    cyan "  Symlink Target: $(readlink "$bin")"
  fi
  
  # Check go build metadata
  if command -v go >/dev/null 2>&1; then
    MOD_INFO=$(go version -m "$bin" 2>/dev/null || true)
    if [ -n "$MOD_INFO" ]; then
      GO_VER=$(echo "$MOD_INFO" | head -1 | awk '{print $2}')
      MOD_VER=$(echo "$MOD_INFO" | grep "^\s*mod" | awk '{print $3}')
      VCS_REV=$(echo "$MOD_INFO" | grep "^\s*build\s*vcs.revision=" | awk -F= '{print $2}' || true)
      VCS_TIME=$(echo "$MOD_INFO" | grep "^\s*build\s*vcs.time=" | awk -F= '{print $2}' || true)
      VCS_MOD=$(echo "$MOD_INFO" | grep "^\s*build\s*vcs.modified=" | awk -F= '{print $2}' || true)

      if [ -z "$VCS_REV" ] && echo "${MOD_VER:-}" | grep -q -E "[0-9]{14}-[a-f0-9]{12}"; then
        VCS_REV="$(echo "$MOD_VER" | awk -F- '{print $NF}' | sed 's/+.*$//') (from pseudo-version)"
        RAW_TIME=$(echo "$MOD_VER" | grep -o -E "[0-9]{14}" || echo "")
        VCS_TIME="$(echo "$RAW_TIME" | sed 's/^\([0-9]\{4\}\)\([0-9]\{2\}\)\([0-9]\{2\}\)\([0-9]\{2\}\)\([0-9]\{2\}\)\([0-9]\{2\}\)$/\1-\2-\3 \4:\5:\6 UTC/') (from pseudo-version)"
      fi

      printf "  Go Toolchain : %s\n" "${GO_VER:-unknown}"
      printf "  Module Ver   : %s\n" "${MOD_VER:-unknown}"
      printf "  Git Revision : %s\n" "${VCS_REV:-unknown}"
      printf "  Commit Time  : %s\n" "${VCS_TIME:-unknown}"
      [ "$VCS_MOD" = "true" ] && yellow "  Warning      : Built from modified (dirty) working directory"
    else
      yellow "  Unable to extract Go build metadata (binary stripped or non-Go binary)."
    fi
  else
    yellow "  'go' command not available; skipping detailed module inspection."
  fi
done

info "Diagnostics & Recommendations:"
if [ "$COUNT" -gt 1 ]; then
  red "  [WARN] Multiple 'bd' binaries exist on your system."
  if [ -f "$HOME/go/bin/bd" ] && [ "$ACTIVE_BIN" != "$HOME/go/bin/bd" ]; then
    if [ -L "$ACTIVE_BIN" ] && [ "$(realpath "$ACTIVE_BIN" 2>/dev/null || true)" = "$(realpath "$HOME/go/bin/bd" 2>/dev/null || true)" ]; then
      green "  ✓ Active binary is symlinked to ~/go/bin/bd. 'go install' directly updates it."
    else
      yellow "  Upgrade Trap Detected:"
      yellow "  Your active binary ($ACTIVE_BIN) takes precedence over ~/go/bin/bd in your PATH."
      yellow "  When you execute 'go install github.com/steveyegge/beads/cmd/bd@main', the updated"
      yellow "  binary lands in ~/go/bin/bd, leaving your active binary stale."
      printf "\n"
      bold "  To permanently fix this so 'go install' auto-updates your active binary:"
      green "    ln -sf \"$HOME/go/bin/bd\" \"$ACTIVE_BIN\" && hash -r"
      bold "  Or if ~/go/bin is already in your PATH, remove the shadowed copy:"
      green "    rm \"$ACTIVE_BIN\" && hash -r"
    fi
  fi
  printf "\n"
  yellow "  Multi-Agent Rule: When multiple machines or autonomous agents access the same Dolt"
  yellow "  database, ensure their Module Ver / Git Revision precisely match to avoid schema skew."
else
  green "  ✓ Only a single 'bd' binary found in PATH. No shadowing risks."
fi

printf "\n"
