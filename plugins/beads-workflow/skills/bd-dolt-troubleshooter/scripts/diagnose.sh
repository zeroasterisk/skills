#!/usr/bin/env sh
# bd / Dolt troubleshooter — diagnostic.
#
# Primary signals (deterministic):
#   - Are local-only files (.beads/backup, dolt-server.*) tracked in git?
#   - Do Dolt and .beads/issues.jsonl agree?
#   - Does a write actually PERSIST? (definitive functional probe)
#
# Secondary signal (informational only): recent backup errors in the log.
#
# By default the functional probe is SKIPPED (read-only mode). Pass --probe to
# run it; it creates and then deletes a temporary throwaway issue.
#
# Usage:
#   scripts/diagnose.sh [--probe] [path-to-repo-root]

set -eu

PROBE=0
REPO="."
for arg in "$@"; do
  case "$arg" in
    --probe) PROBE=1 ;;
    *) REPO="$arg" ;;
  esac
done
cd "$REPO"

red()   { printf '\033[1;31m%s\033[0m\n' "$1"; }
green() { printf '\033[1;32m%s\033[0m\n' "$1"; }
yellow(){ printf '\033[1;33m%s\033[0m\n' "$1"; }
info()  { printf '\033[1;34m==>\033[0m %s\n' "$1"; }

if [ ! -d .beads ]; then
  red "No .beads/ directory here. Run from a bd-managed repo root, or pass the path."
  exit 1
fi
command -v bd >/dev/null 2>&1 || { red "bd not found in PATH."; exit 1; }

ISSUES=0

info "0. Engine mode and daemon-error (foundational check)"
MODE_LINE=$(bd dolt show 2>/dev/null | grep "Mode:" || true)
printf "    %s\n" "$MODE_LINE"
if echo "$MODE_LINE" | grep -q "embedded"; then
  if [ -d .beads/dolt ] && [ "$(ls -A .beads/dolt 2>/dev/null)" ]; then
    red "    PROBLEM: Engine is in embedded mode but .beads/dolt/ contains server-mode data."
    red "    Fix: bd init --server --reinit-local --database <name> --non-interactive"
    red "         (find <name> with: ls .beads/dolt/)"
    ISSUES=$((ISSUES+1))
  else
    yellow "    Engine is in embedded mode (no server-mode data found in .beads/dolt/)."
  fi
fi
if [ -f .beads/daemon-error ]; then
  red "    PROBLEM: .beads/daemon-error exists — bd failed to start:"
  sed 's/^/      /' .beads/daemon-error
  if grep -q "DATABASE MISMATCH" .beads/daemon-error; then
    red "    Fix: bd migrate --update-repo-id --yes"
    red "         then: rm .beads/daemon-error"
  fi
  ISSUES=$((ISSUES+1))
else
  DOLT_SHOW=$(bd dolt show 2>/dev/null || true)
  if echo "$DOLT_SHOW" | grep -qi "Server not reachable" && [ -f .beads/dolt-server.lock ]; then
    red "    PROBLEM: Dolt server is unreachable but .beads/dolt-server.lock exists (lock contention / orphaned process)."
    red "    Fix: Run scripts/find-dolt-server.sh to isolate and stop the orphan, then clear stale runtime files."
    ISSUES=$((ISSUES+1))
    SKIP_DB_CALLS=1
  else
    # Check bd doctor output directly even if daemon-error file is missing
    REPO_MISMATCH=$(bd doctor 2>&1 | grep -i "Database belongs to different repository" || true)
    if [ -n "$REPO_MISMATCH" ]; then
      red "    PROBLEM: Repo Fingerprint mismatch (Database belongs to different repository)."
      red "    Fix: bd migrate --update-repo-id --yes"
      ISSUES=$((ISSUES+1))
    else
      green "    No daemon-error or repo fingerprint mismatch. Good."
    fi
  fi
fi

info "0b. Schema version skew & pending migrations (client binary vs database)"
if [ "${SKIP_DB_CALLS:-0}" -eq 1 ]; then
  yellow "    Skipping schema checks (resolve lock contention / unreachable server first)."
else
  DOCTOR_OUT=$(bd doctor 2>&1 || true)
  SKEW=$(echo "$DOCTOR_OUT" | grep -i -E "schema version mismatch|schema skew|pending schema migration|refusing to auto-apply" | head -1 || true)
  if [ -z "$SKEW" ]; then
    # Also check bd list or bd migrate --inspect output for migration gates
    MIG_CHECK=$(bd migrate --inspect 2>&1 || true)
    if echo "$MIG_CHECK" | grep -qi -E "refusing to auto-apply|pending schema migration"; then
      SKEW=$(echo "$MIG_CHECK" | grep -i -E "refusing to auto-apply|pending schema migration" | head -1)
    fi
  fi
fi

if [ -n "$SKEW" ]; then
  red "    PROBLEM: schema version skew / pending migrations detected:"
  printf "      %s\n" "$SKEW"
  if echo "$SKEW" | grep -qi -E "binary knows up to|is ahead of binary"; then
    red "    Your bd binary is BEHIND the database (another agent/machine migrated it forward)."
    red "    Reads warn; writes FAIL (\"Field 'id' doesn't have a default value\" or unexpected schema errors)."
    red "    Fix: UPGRADE the client to match — scripts/restore-bd.sh (or go install github.com/steveyegge/beads/cmd/bd@main)"
    red "         (CGO/ICU + PATH-copy caveats: SKILL.md 'Client BEHIND the Database')."
    red "    Do NOT run 'bd migrate' on the old binary; it can't apply a schema it doesn't know."
  else
    red "    Database has pending migrations blocked by remote-sync gate."
    red "    Fix: bd migrate --force (or BD_ALLOW_REMOTE_MIGRATE=1 bd migrate) followed by bd dolt push."
  fi
  ISSUES=$((ISSUES+1))
else
  green "    No schema version skew or pending migrations."
fi

info "0c. Client binary & PATH shadowing check"
PATH_BINS=$(which -a bd 2>/dev/null | sort -u || true)
BIN_COUNT=$(echo "$PATH_BINS" | grep -c . || echo 0)
ACTIVE_BIN=$(which bd 2>/dev/null || true)
UNIQUE_REAL_BINS=""
for bin in $PATH_BINS; do
  rbin=$(realpath "$bin" 2>/dev/null || echo "$bin")
  case " $UNIQUE_REAL_BINS " in
    *" $rbin "*) ;;
    *) UNIQUE_REAL_BINS="$UNIQUE_REAL_BINS $rbin" ;;
  esac
done
REAL_COUNT=0
for r in $UNIQUE_REAL_BINS; do [ -n "$r" ] && REAL_COUNT=$((REAL_COUNT+1)); done

if [ "$REAL_COUNT" -gt 1 ]; then
  red "    PROBLEM: Multiple distinct 'bd' binaries found in PATH ($BIN_COUNT found, $REAL_COUNT distinct):"
  for bin in $PATH_BINS; do
    if [ "$bin" = "$ACTIVE_BIN" ]; then
      echo "      * $bin (ACTIVE)"
    else
      echo "        $bin (shadowed)"
    fi
  done
  red "    Upgrade hazard: Running 'go install' installs to ~/go/bin/bd, but an older active copy in ~/.local/bin/bd"
  red "    or /usr/local/bin/bd will shadow it, causing schema skew errors to persist after upgrading."
  red "    Fix: Sync or link duplicates — ln -sf ~/go/bin/bd \"$ACTIVE_BIN\" && hash -r"
  red "    Tip: Run scripts/inspect-binary.sh to inspect git commit revisions across all installed binaries."
  ISSUES=$((ISSUES+1))
elif [ "$BIN_COUNT" -gt 1 ]; then
  green "    Multiple PATH entries found for bd, but all resolve via symlink to the same binary ($ACTIVE_BIN). Good."
else
  green "    Single bd binary found in PATH ($ACTIVE_BIN). Good."
fi

info "1. Dolt server status"
bd dolt status 2>&1 | sed 's/^/    /' || yellow "    bd dolt status failed"

info "2. PRIMARY: local-only files tracked in git (deterministic)"
TRACKED_BAD=""
for f in $(git ls-files .beads/ 2>/dev/null); do
  case "$f" in
    .beads/backup/*|.beads/dolt-server.pid|.beads/dolt-server.port|.beads/dolt-server.lock)
      TRACKED_BAD="$TRACKED_BAD $f" ;;
  esac
done
if [ -n "$TRACKED_BAD" ]; then
  red "    These local files are committed to git (corruption will spread to clones):"
  for f in $TRACKED_BAD; do echo "      $f"; done
  ISSUES=$((ISSUES+1))
else
  green "    No backup/runtime files tracked. Good."
fi

info "3. PRIMARY: Dolt vs JSONL agreement (the real symptom)"
if command -v python3 >/dev/null 2>&1 && [ -f .beads/issues.jsonl ]; then
  SAMPLE=$(python3 -c "
import json
ids=[json.loads(l, strict=False)['id'] for l in open('.beads/issues.jsonl') if l.strip()]
print(' '.join(ids[:5]))
" 2>/dev/null || true)
  MISMATCH=0
  for id in $SAMPLE; do
    DOLT_RAW=$(bd show "$id" --json 2>&1 || true)
    DOLT=$(echo "$DOLT_RAW" | python3 -c "import json,sys;d=json.loads(sys.stdin.read(), strict=False);i=d[0] if isinstance(d,list) else d;print(i['status'])" 2>/dev/null || echo "?")
    JSONL=$(python3 -c "
import json
for l in open('.beads/issues.jsonl'):
    if l.strip():
        i=json.loads(l, strict=False)
        if i['id']=='$id': print(i['status'])
" 2>/dev/null || echo "?")
    if [ "$DOLT" = "$JSONL" ]; then
      green "    $id: dolt=$DOLT jsonl=$JSONL OK"
    elif [ "$DOLT" = "?" ]; then
      if echo "$DOLT_RAW" | grep -qi -E "refusing to auto-apply|Database belongs to different repository|schema version"; then
        red "    $id: dolt=? (bd query failed due to schema skew / repo-id mismatch; see checks 0 & 0b)"
      else
        red "    $id: dolt=? jsonl=$JSONL MISMATCH (query failed)"
        MISMATCH=1
      fi
    else
      red "    $id: dolt=$DOLT jsonl=$JSONL MISMATCH"
      MISMATCH=1
    fi
  done
  [ "$MISMATCH" -eq 1 ] && ISSUES=$((ISSUES+1))
else
  yellow "    Skipped (need python3 and .beads/issues.jsonl)."
fi

info "4. PRIMARY: write-persistence probe (definitive)"
if [ "$PROBE" -eq 1 ]; then
  LOG_BEFORE=$( [ -f .beads/dolt-server.log ] && wc -c < .beads/dolt-server.log || echo 0 )
  OUT=$(bd create "TEMP diagnose probe" --type task --priority 4 --json 2>/dev/null || true)
  PID=$(echo "$OUT" | python3 -c "import json,sys;d=json.loads(sys.stdin.read(), strict=False);print(d.get('id',''))" 2>/dev/null || true)
  if [ -z "$PID" ]; then
    PID=$(echo "$OUT" | grep -oE '[a-zA-Z0-9_.-]+-[a-zA-Z0-9]+' | tail -1 || true)
  fi
  sleep 1
  bd export -o .beads/issues.jsonl >/dev/null 2>&1 || true
  if [ -n "$PID" ] && grep -q "$PID" .beads/issues.jsonl 2>/dev/null; then
    green "    Write persisted to JSONL ($PID). Persistence is healthy."
  else
    red "    Write did NOT persist to JSONL. Active write-rollback corruption."
    ISSUES=$((ISSUES+1))
  fi
  LOG_AFTER=$( [ -f .beads/dolt-server.log ] && wc -c < .beads/dolt-server.log || echo 0 )
  NEWERR=$(tail -c +$((LOG_BEFORE+1)) .beads/dolt-server.log 2>/dev/null | grep -c "table file not found\|auto-backup failed" || true)
  if [ "${NEWERR:-0}" -gt 0 ] 2>/dev/null; then
    red "    $NEWERR new backup error(s) emitted during the write — backup target is broken."
    ISSUES=$((ISSUES+1))
  fi
  [ -n "$PID" ] && bd delete "$PID" --force >/dev/null 2>&1 || true
  bd export -o .beads/issues.jsonl >/dev/null 2>&1 || true
else
  yellow "    Skipped (read-only mode). Re-run with --probe for the definitive test."
fi

info "5. INFORMATIONAL: recent backup errors in log (heuristic)"
if [ -f .beads/dolt-server.log ]; then
  TOTAL=$(grep -c "table file not found\|auto-backup failed\|sync backup" .beads/dolt-server.log 2>/dev/null || true)
  if [ "${TOTAL:-0}" -gt 0 ] 2>/dev/null; then
    yellow "    $TOTAL historical backup-error line(s) in the log."
    yellow "    NOTE: historical lines persist after a fix; trust checks 2-4 above, not this count."
  else
    green "    No backup errors in log."
  fi
fi

echo
if [ "$ISSUES" -eq 0 ]; then
  green "No problems detected by primary checks."
  if [ "$PROBE" -eq 0 ]; then
    yellow "(Run with --probe for the definitive write-persistence test.)"
  fi
else
  red "Detected $ISSUES problem area(s). See SKILL.md for fixes:"
  red "  - Automated multi-issue repair: scripts/repair.sh"
  red "  - Engine mode / daemon-error issues: references/recovery-playbook.md Case E"
  red "  - Corrupt backup / write-revert issues: scripts/repair-corrupt-backup.sh"
fi
