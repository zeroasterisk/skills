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

CROSS_ERA_CHECK=$(bd dolt show 2>&1 || true)
if echo "$CROSS_ERA_CHECK" | grep -qi -E "legacy Dolt server workspace|cross-era-upgrades|explicit migration is required"; then
  red "Cross-era legacy Dolt workspace detected (bd v0.55–v0.62 -> v1.3+ guard):"
  printf "%s\n" "$CROSS_ERA_CHECK" | sed 's/^/  /'
  red "Aborting automated repair — bd migrate and bd export are blocked by the cross-era guard."
  red "Follow references/recovery-playbook.md Case J (inspect raw Dolt count vs issues.jsonl, snapshot, re-init, bd import)."
  exit 2
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

info "1b. Checking for missing or misplaced server-mode database"
META_MODE=""
META_DB=""
if [ -f .beads/metadata.json ]; then
  META_MODE=$(sed -n 's/.*"dolt_mode"[[:space:]]*:[[:space:]]*"\([^"]*\)".*/\1/p' .beads/metadata.json | head -1)
  META_DB=$(sed -n 's/.*"dolt_database"[[:space:]]*:[[:space:]]*"\([^"]*\)".*/\1/p' .beads/metadata.json | head -1)
fi
if [ -z "$(git config --get beads.role 2>/dev/null || true)" ]; then
  git config beads.role maintainer 2>/dev/null || true
fi
if [ "$META_MODE" = "server" ] && [ -n "$META_DB" ] && [ ! -d ".beads/dolt/$META_DB" ]; then
  if [ ! -d ".beads/embeddeddolt/$META_DB" ]; then
    yellow "    Server-mode database '$META_DB' missing locally; running 'bd bootstrap --yes' (may retry up to ~70s)..."
    BOOT_RC=0
    BOOT_OUT=$(bd bootstrap --yes 2>&1) || BOOT_RC=$?
    [ -n "$BOOT_OUT" ] && printf '%s\n' "$BOOT_OUT" | sed 's/^/    /'
    if [ "$BOOT_RC" -ne 0 ] && [ ! -d ".beads/dolt/$META_DB" ] && [ ! -d ".beads/embeddeddolt/$META_DB" ]; then
      red "    bd bootstrap failed (exit $BOOT_RC) and database '$META_DB' was not created."
      if echo "$BOOT_OUT" | grep -qi -E "AccessDenied|403|storage\.objects|credentials|unreachable|clone from remote"; then
        red "    Remote sync.remote could not be cloned (auth/403 or offline)."
        red "    Either fix remote credentials and re-run, or follow references/recovery-playbook.md Case I (Sub-case I.2) to initialize locally from .beads/issues.jsonl."
      fi
      exit 1
    fi
  fi
  if [ -d ".beads/embeddeddolt/$META_DB" ] && [ ! -d ".beads/dolt/$META_DB" ]; then
    yellow "    Relocating bootstrapped database from .beads/embeddeddolt/$META_DB -> .beads/dolt/$META_DB..."
    bd dolt stop >/dev/null 2>&1 || true
    BEADS_ABS=$(cd .beads 2>/dev/null && pwd || true)
    if [ -n "$BEADS_ABS" ] && command -v pgrep >/dev/null 2>&1; then
      for pid in $(pgrep -f "dolt sql-server" 2>/dev/null || true); do
        pcwd=""
        if [ -r "/proc/$pid/cwd" ]; then
          pcwd=$(readlink -f "/proc/$pid/cwd" 2>/dev/null || true)
        elif command -v lsof >/dev/null 2>&1; then
          pcwd=$(lsof -a -p "$pid" -d cwd -Fn 2>/dev/null | sed -n 's/^n//p' || true)
        fi
        case "$pcwd" in
          "$BEADS_ABS"*) kill -TERM "$pid" 2>/dev/null || true; sleep 1 ;;
        esac
      done
    fi
    mkdir -p .beads/dolt
    mv ".beads/embeddeddolt/$META_DB" ".beads/dolt/$META_DB"
    rm -rf .beads/embeddeddolt
    rm -f .beads/dolt-server.lock .beads/dolt-server.port .beads/dolt-server.info .beads/dolt-server.pid .beads/dolt-server-config.yaml
    bd dolt start 2>&1 | sed 's/^/    /' || true
    green "    Server-mode database '$META_DB' restored and Dolt server started."
  fi
  if [ ! -d ".beads/dolt/$META_DB" ]; then
    red "    Server-mode database '$META_DB' is still missing under .beads/dolt/. Aborting repair."
    exit 1
  fi
else
  green "    Server-mode database directory present (or not in server mode)."
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
if echo "$MIG_CHECK $DOCTOR_CHECK" | grep -qi -E "refusing to auto-apply|pending schema migration|schema version mismatch|Database: version .* \(CLI:"; then
  yellow "    Pending schema migrations detected. Applying schema + metadata migrations with --force..."
  bd migrate schema --force 2>&1 | sed 's/^/    /' || true
  bd migrate --force 2>&1 | sed 's/^/    /' || true
  bd vc commit -m "chore(bd): commit config working set" >/dev/null 2>&1 || true
  bd recompute-blocked --json 2>&1 | sed 's/^/    /' || true
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

info "5. Untracking local-only and sensitive files from git"
UNTRACKED_ANY=0
for f in $(git ls-files .beads/ 2>/dev/null); do
  case "$f" in
    .beads/backup/*|.beads/backup.*/*|.beads/dolt/*|.beads/dolt.*/*|.beads/dolt-server*|.beads/dolt-config.log|.beads/dolt-monitor.pid*|.beads/*.lock|.beads/.beads-credential-key)
      git rm --cached "$f" >/dev/null 2>&1 && { echo "    untracked $f"; UNTRACKED_ANY=1; } ;;
  esac
done
[ "$UNTRACKED_ANY" -eq 0 ] && green "    No local runtime or credential files tracked in git."

info "6. Running bd doctor --fix, committing metadata changes, and refreshing hooks"
bd doctor --fix --yes 2>&1 | sed 's/^/    /' || true
bd vc commit -m "chore(bd): commit doctor metadata fixes" >/dev/null 2>&1 || true
if [ -f .git/hooks/pre-commit ] && [ ! -f .git/hooks/pre-commit.disabled ]; then
  bd hooks install --force >/dev/null 2>&1 || true
fi

info "7. Exporting clean JSONL"
EXPORT_RC=0
EXPORT_OUT=$(bd export -o .beads/issues.jsonl 2>&1) || EXPORT_RC=$?
[ -n "$EXPORT_OUT" ] && printf '%s\n' "$EXPORT_OUT" | sed 's/^/    /'
if [ "$EXPORT_RC" -ne 0 ]; then
  red "    bd export failed (exit $EXPORT_RC). Repair incomplete."
  echo "Raw snapshot saved at: $BACKUP_SNAPSHOT"
  exit "$EXPORT_RC"
fi

echo
green "Unified repair complete."
echo "Raw snapshot saved at: $BACKUP_SNAPSHOT"
