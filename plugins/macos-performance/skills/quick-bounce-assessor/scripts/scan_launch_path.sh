#!/usr/bin/env bash
# quick-bounce-assessor: launch-path & steady-state heuristic scanner
#
# Read-only. Greps a macOS/SwiftUI Swift project for likely first-frame
# offenders and steady-state render hazards. Advisory only: ALWAYS exits 0.
# Confirm every lead by opening the reported file:line.
#
# Usage: scan_launch_path.sh [PROJECT_DIR]   (defaults to current directory)

set -uo pipefail

ROOT="${1:-.}"

if [ ! -d "$ROOT" ]; then
  echo "quick-bounce-assessor: '$ROOT' is not a directory" >&2
  exit 0
fi

# Prefer ripgrep if available; fall back to grep -rn.
if command -v rg >/dev/null 2>&1; then
  SEARCH() { rg -n --no-heading -g '*.swift' -e "$1" "$ROOT" 2>/dev/null; }
  SEARCHU() { rg -Un --no-heading -g '*.swift' -e "$1" "$ROOT" 2>/dev/null; }
else
  SEARCH()  { grep -rns --include='*.swift' -E "$1" "$ROOT" 2>/dev/null; }
  SEARCHU() { grep -rns --include='*.swift' -E "$1" "$ROOT" 2>/dev/null; }
fi

BLUE='\033[1;34m'; YELLOW='\033[1;33m'; GREEN='\033[1;32m'; NC='\033[0m'
section() { echo -e "${BLUE}==>${NC} $1"; }
finding() { echo -e "  ${YELLOW}!${NC} $1"; }
okmsg()   { echo -e "  ${GREEN}ok${NC} $1"; }

emit() { # $1=label  $2=pattern  (multiline)
  local out
  out="$(SEARCHU "$2")"
  if [ -n "$out" ]; then
    finding "$1"
    echo "$out" | sed 's/^/      /'
  fi
}

echo "quick-bounce-assessor scan: $ROOT"
echo

# --- 1. Launch path / main-actor I/O -----------------------------------------
section "1. Launch path / main-actor I/O"
# I/O primitives anywhere (leads; confirm they run during init/launch)
emit "Synchronous file reads (confirm not on launch path)" \
  '(Data\(contentsOf:|String\(contentsOf:|contentsOfDirectory|\.decode\()'
# init bodies that call load/scan/decode
emit "init() calling load/scan/decode (likely blocks first frame)" \
  '(?s)init\([^)]*\)\s*\{[^}]*?(load|scan|decode)[A-Za-z]*\('
# singleton shared with parsing init
emit "static shared singleton (check its init for I/O)" \
  'static\s+let\s+shared\s*='
# app delegate launch method
emit "applicationDidFinishLaunching (check for heavy work)" \
  'applicationDidFinishLaunching'

# --- 2. Body work / per-render allocations -----------------------------------
section "2. Blocking / allocating in body"
emit "Formatter/encoder constructed (hoist to static; check if in body)" \
  '(DateFormatter\(|JSONEncoder\(|JSONDecoder\(|NumberFormatter\()'

# --- 3. Strict concurrency posture -------------------------------------------
section "3. Strict concurrency posture"
if find "$ROOT" -name 'Package.swift' 2>/dev/null | head -1 | grep -q .; then
  if SEARCH 'StrictConcurrency' | grep -q .; then
    okmsg "StrictConcurrency referenced in build settings"
  else
    finding "No StrictConcurrency found in Package.swift (enable targeted -> complete)"
  fi
fi
emit "@unchecked Sendable (verify each promise under strict concurrency)" \
  '@unchecked\s+Sendable'

# --- 4. VM / business-logic separation ---------------------------------------
section "4. View-model / business-logic separation"
emit "actor declarations (use only for shared mutable state crossing threads)" \
  '\bactor\s+[A-Za-z_]'
emit "Combine sink/subjects (prefer AsyncStream for new coordination)" \
  '(\.sink\(|PassthroughSubject|CurrentValueSubject)'
# Large ObservableObject files (heuristic: report .swift over 400 lines w/ ObservableObject)
while IFS= read -r f; do
  [ -f "$f" ] || continue
  if grep -q 'ObservableObject' "$f" 2>/dev/null; then
    lines=$(wc -l < "$f" | tr -d ' ')
    if [ "${lines:-0}" -gt 400 ]; then
      finding "Large ObservableObject ($lines lines): $f  (candidate god-object VM)"
    fi
  fi
done < <(find "$ROOT" -name '*.swift' 2>/dev/null)

# --- 5. Steady-state render budget -------------------------------------------
section "5. Steady-state render budget"
emit "Timer (small interval driving @Published? -> TimelineView/Canvas)" \
  '(Timer\(timeInterval:|Timer\.scheduledTimer|DispatchSourceTimer)'
emit "inline print() (replace with a logger)" \
  '(?<![A-Za-z_])print\('

echo
echo "Scan complete (advisory). Confirm each lead by reading the file:line, then"
echo "verify real cost with Instruments (Time Profiler, os_signpost)."
exit 0
