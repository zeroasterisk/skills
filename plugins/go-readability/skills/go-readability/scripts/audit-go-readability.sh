#!/usr/bin/env bash
# audit-go-readability.sh — Runs the 13 mechanical Go Readability self-audit
# checks recursively across a Go repository or package directory.
#
# Usage:
#   ./scripts/audit-go-readability.sh [target_dir]

set -euo pipefail

TARGET_DIR="${1:-.}"
if [[ ! -d "$TARGET_DIR" ]]; then
  echo "Error: directory '$TARGET_DIR' does not exist." >&2
  exit 1
fi

cd "$TARGET_DIR"

echo "# Go Readability Self-Audit Report"
echo "- **Target**: \`$(pwd)\`"
echo ""

run_check() {
  local num="$1"
  local title="$2"
  local include_glob="$3"
  local pattern="$4"
  local exclude_pattern="${5:-}"

  local matches
  if [[ -n "$exclude_pattern" ]]; then
    matches="$(grep -rnE --include="$include_glob" --exclude-dir={.git,vendor,node_modules,dist,.serena,.beads,.dolt} "$pattern" . 2>/dev/null | grep -vE "$exclude_pattern" || true)"
  else
    matches="$(grep -rnE --include="$include_glob" --exclude-dir={.git,vendor,node_modules,dist,.serena,.beads,.dolt} "$pattern" . 2>/dev/null || true)"
  fi

  local count=0
  if [[ -n "$matches" ]]; then
    count="$(printf '%s\n' "$matches" | wc -l | tr -d ' ')"
  fi

  printf "## %s. %s (%s match(es))\n" "$num" "$title" "$count"
  if [[ "$count" -gt 0 ]]; then
    printf '```text\n%s\n```\n\n' "$matches"
  else
    printf "_Clean (0 matches)_\n\n"
  fi
}

run_check "1"  "Manually-quoted format verbs (prefer %q)" "*.go" "('%[svqd]'|\\\\\"%[svqd]\\\\\")"
run_check "2"  "Capitalized error strings (inspect proper nouns/identifiers)" "*.go" '(fmt\.Errorf|errors\.New)\("[A-Z]'
run_check "3"  "Error strings ending in punctuation" "*.go" 'fmt\.Errorf\(".*[.!?]"'
run_check "4"  "Test failures missing function-under-test name" "*_test.go" 't\.(Error|Fatal)f?\("(got|expected) '
run_check "5"  "Test failures with empty parens (missing inputs)" "*_test.go" 't\.(Error|Fatal)f?\("[A-Za-z_]+\(\)'
run_check "6"  "Get-prefixed functions or methods (decisions#getters)" "*.go" 'func (\([^)]+\) )?Get[A-Z]'
run_check "7"  "Receiver names longer than 2 letters" "*.go" 'func \([a-zA-Z]{3,} \*?[A-Z]'
run_check "8"  "Indented else blocks (decisions#indent-error-flow)" "*.go" '\} else \{$'
run_check "9"  "Legacy interface{} (prefer any)" "*.go" '\binterface\{\}'
run_check "10" "Detached context.Background() outside main/init/tests" "*.go" 'context\.Background\(\)' '(_test\.go|main\.go|init\.go)'
run_check "11" "Non-nil empty slice literal := []T{} (prefer var s []T)" "*.go" ':= \[\][a-zA-Z*]+\{\}'
run_check "12" "Overly permissive file modes (0666 or 0777)" "*.go" '\b0(666|777)\b'
