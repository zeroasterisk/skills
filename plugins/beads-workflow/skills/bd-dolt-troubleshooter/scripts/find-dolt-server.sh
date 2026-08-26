#!/usr/bin/env sh
# bd / Dolt troubleshooter — list every running `dolt sql-server` with its PID
# AND its working directory, and mark the one that owns THIS repo's .beads/.
#
# Read-only: it inspects processes only, never kills or changes anything.
# Use it to isolate the single server to stop before `bd dolt start`, so you
# don't blanket-kill other projects' servers. See references/recovery-playbook.md
# "Case F" for the full lock-contention workflow.
#
# Usage: scripts/find-dolt-server.sh [path-to-repo-root]
# Defaults to the current directory.

set -eu

REPO="${1:-.}"
cd "$REPO"

red()   { printf '\033[1;31m%s\033[0m\n' "$1"; }
green() { printf '\033[1;32m%s\033[0m\n' "$1"; }
yellow(){ printf '\033[1;33m%s\033[0m\n' "$1"; }
info()  { printf '\033[1;34m==>\033[0m %s\n' "$1"; }

if ! command -v pgrep >/dev/null 2>&1; then
  red "pgrep not found; cannot enumerate dolt processes."
  exit 1
fi

# Absolute path to this repo's .beads/ so we can match a server's CWD against it.
BEADS_DIR=$(cd .beads 2>/dev/null && pwd || true)
if [ -z "$BEADS_DIR" ]; then
  yellow "No .beads/ here; will list all dolt servers but can't mark a match."
fi

# Resolve a PID's current working directory, portably.
#   macOS/BSD: lsof;  Linux: /proc.
pid_cwd() {
  _pid="$1"
  if [ -r "/proc/$_pid/cwd" ]; then
    readlink -f "/proc/$_pid/cwd" 2>/dev/null && return 0
  fi
  if command -v lsof >/dev/null 2>&1; then
    lsof -a -p "$_pid" -d cwd -Fn 2>/dev/null | sed -n 's/^n//p' && return 0
  fi
  echo "<cwd-unavailable>"
}

PIDS=$(pgrep -f "dolt sql-server" 2>/dev/null || true)
if [ -z "$PIDS" ]; then
  green "No 'dolt sql-server' processes are running."
  exit 0
fi

info "Running dolt sql-server processes:"
MATCH_PIDS=""
for pid in $PIDS; do
  cwd=$(pid_cwd "$pid")
  # A server for THIS repo has its CWD at or under our .beads/ directory.
  if [ -n "$BEADS_DIR" ] && case "$cwd" in "$BEADS_DIR"*) true ;; *) false ;; esac; then
    printf '  '; green "PID $pid  $cwd   <-- THIS repo"
    MATCH_PIDS="$MATCH_PIDS $pid"
  else
    printf '  PID %s\t%s\n' "$pid" "$cwd"
  fi
done

echo
MATCH_PIDS=$(echo "$MATCH_PIDS" | sed 's/^ *//')
if [ -z "$BEADS_DIR" ]; then
  yellow "No .beads/ in this directory — nothing marked. Pass the repo root as an argument."
elif [ -z "$MATCH_PIDS" ]; then
  green "No running server is bound to this repo's .beads/ (safe to 'bd dolt start')."
else
  yellow "Server(s) for this repo: $MATCH_PIDS"
  echo "To stop only this project's server, from the repo root run:"
  echo "    bd dolt stop"
  echo "If a listed PID survives (orphan), stop that specific one:"
  echo "    kill $MATCH_PIDS"
  echo "Then clear stale runtime files and start the single owner:"
  echo "    rm -f .beads/dolt-server.lock .beads/dolt-server.port .beads/dolt-server.info .beads/dolt-server.pid"
  echo "    bd dolt start && bd dolt status"
fi
