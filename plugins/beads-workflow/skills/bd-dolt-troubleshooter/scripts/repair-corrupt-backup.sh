#!/usr/bin/env sh
# bd / Dolt troubleshooter — repair the corrupt-backup write-rollback loop.
# MAKES CHANGES. Review output, verify, then commit the resulting issues.jsonl.
#
# Usage: scripts/repair-corrupt-backup.sh [path-to-repo-root]
# Defaults to the current directory.

set -eu

REPO="${1:-.}"
cd "$REPO"

red()   { printf '\033[1;31m%s\033[0m\n' "$1"; }
green() { printf '\033[1;32m%s\033[0m\n' "$1"; }
info()  { printf '\033[1;34m==>\033[0m %s\n' "$1"; }

if [ ! -d .beads ]; then
  red "No .beads/ directory here. Run from a bd-managed repo root, or pass the path."
  exit 1
fi
if ! command -v bd >/dev/null 2>&1; then
  red "bd not found in PATH."
  exit 1
fi

TS=$(date +%s)

info "1. Stopping Dolt server"
bd dolt stop 2>&1 | sed 's/^/    /' || true
sleep 1

info "2. Moving corrupt backup aside (if present)"
if [ -d .beads/backup ]; then
  mv .beads/backup ".beads/backup.corrupt.$TS"
  green "    Moved .beads/backup -> .beads/backup.corrupt.$TS"
else
  green "    No .beads/backup to move."
fi

info "3. Restarting Dolt server (bd will recreate a fresh backup)"
bd dolt start 2>&1 | sed 's/^/    /' || true
sleep 1

info "4. Untracking local files that must not be in git"
UNTRACKED_ANY=0
for f in $(git ls-files .beads/ 2>/dev/null); do
  case "$f" in
    .beads/backup/*|.beads/dolt-server.pid|.beads/dolt-server.port|.beads/dolt-server.lock)
      git rm --cached "$f" >/dev/null 2>&1 && { echo "    untracked $f"; UNTRACKED_ANY=1; } ;;
  esac
done
[ "$UNTRACKED_ANY" -eq 0 ] && green "    Nothing needed untracking."

info "5. Removing the moved-aside corrupt copy"
rm -rf ".beads/backup.corrupt.$TS" 2>/dev/null || true
green "    Done."

info "6. Forcing a clean JSONL export from Dolt"
bd export -o .beads/issues.jsonl 2>&1 | sed 's/^/    /'

echo
green "Repair complete."
echo "Next steps:"
echo "  1. Verify Dolt and JSONL agree (see SKILL.md 'Manual Verification Snippet')."
echo "  2. git add .beads/issues.jsonl"
echo "  3. git commit -m 'chore(bd): untrack corrupt dolt backup; resync issues.jsonl'"
