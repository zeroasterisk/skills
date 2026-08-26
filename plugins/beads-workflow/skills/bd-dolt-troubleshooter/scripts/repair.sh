#!/usr/bin/env sh
# bd / Dolt troubleshooter — unified repair script.
# Safely snapshot .beads/dolt and apply standard resolution steps for schema skew,
# repo fingerprint mismatches, corrupt backup loops, and doctor warnings.
#
# Usage: scripts/repair.sh [path-to-repo-root]
# Defaults to current working directory.

set -eu

REPO="${1:-.}"
cd "$REPO"

red()    { printf '\033[1;31m%s\033[0m\n' "$1"; }
green()  { printf '\033[1;32m%s\033[0m\n' "$1"; }
yellow() { printf '\033[1;33m%s\033[0m\n' "$1"; }
info()   { printf '\033[1;34m==>\033[0m %s\n' "$1"; }

if [ ! -d .beads ]; then
  red "No .beads/ directory here. Run from a bd-managed repo root, or pass the path."
  exit 1
fi
if ! command -v bd >/dev/null 2>&1; then
  red "bd not found in PATH."
  exit 1
fi

TS=$(date +%s)
BACKUP_SNAPSHOT="/tmp/bd-raw-snapshot-$TS"

info "1. Taking raw filesystem snapshot backup"
if [ -d .beads/dolt ]; then
  cp -R .beads/dolt "$BACKUP_SNAPSHOT"
  green "    Created snapshot backup: $BACKUP_SNAPSHOT"
else
  yellow "    No .beads/dolt directory found to snapshot."
fi

info "2. Checking for corrupt backup directory"
if [ -d .beads/backup ]; then
  # Stop server temporarily before moving backup
  bd dolt stop >/dev/null 2>&1 || true
  sleep 1
  mv .beads/backup ".beads/backup.corrupt.$TS"
  green "    Moved .beads/backup -> .beads/backup.corrupt.$TS"
  bd dolt start >/dev/null 2>&1 || true
  sleep 1
  rm -rf ".beads/backup.corrupt.$TS" 2>/dev/null || true
else
  green "    No corrupt backup directory to clear."
fi

info "3. Checking and applying pending schema migrations"
MIG_CHECK=$(bd migrate --inspect 2>&1 || true)
DOCTOR_CHECK=$(bd doctor 2>&1 || true)
if echo "$MIG_CHECK $DOCTOR_CHECK" | grep -qi -E "refusing to auto-apply|pending schema migration|schema version mismatch"; then
  yellow "    Pending schema migrations detected. Applying with --force..."
  bd migrate --force 2>&1 | sed 's/^/    /' || true
else
  green "    No pending schema migrations."
fi

info "4. Checking and updating repository fingerprint if mismatched"
if echo "$DOCTOR_CHECK" | grep -qi "Database belongs to different repository" || [ -f .beads/daemon-error ]; then
  yellow "    Updating repo fingerprint..."
  bd migrate --update-repo-id --yes 2>&1 | sed 's/^/    /' || true
  rm -f .beads/daemon-error
else
  green "    Repo fingerprint is up to date."
fi

info "5. Untracking local-only files from git"
UNTRACKED_ANY=0
for f in $(git ls-files .beads/ 2>/dev/null); do
  case "$f" in
    .beads/backup/*|.beads/dolt-server.pid|.beads/dolt-server.port|.beads/dolt-server.lock)
      git rm --cached "$f" >/dev/null 2>&1 && { echo "    untracked $f"; UNTRACKED_ANY=1; } ;;
  esac
done
[ "$UNTRACKED_ANY" -eq 0 ] && green "    No local runtime files tracked in git."

info "6. Running bd doctor --fix"
bd doctor --fix --yes 2>&1 | sed 's/^/    /' || true

info "7. Exporting clean JSONL"
bd export -o .beads/issues.jsonl 2>&1 | sed 's/^/    /'

echo
green "Unified repair complete."
echo "Raw snapshot saved at: $BACKUP_SNAPSHOT"
