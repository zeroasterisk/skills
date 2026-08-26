#!/usr/bin/env bash
# Read-Only Conformance Debt Auditor for Agent Skills & Plugins
# Scans a repository and reports conformance debt without making modifications.
#
# Canonical Specifications:
#   - Agent Plugins Specification v1.0.0: https://github.com/agentplugins/agent-plugins-spec
#   - Agent Skills Specification: https://agentskills.io/specification.md
#   - Note: Reference validator (skills-ref) is marked for demonstration purposes and validates
#     skills only; this script provides custom automated debt analysis for plugin migrations.

set -euo pipefail

REPO_ROOT="${1:-.}"
cd "$REPO_ROOT"

RED='\033[1;31m'
GREEN='\033[1;32m'
YELLOW='\033[1;33m'
BLUE='\033[1;34m'
NC='\033[0m'

DEBT_ITEMS=0

info()  { echo -e "${BLUE}==>${NC} $1"; }
ok()    { echo -e "  ${GREEN}✓${NC} $1"; }
debt()  { echo -e "  ${RED}✖ [DEBT]${NC} $1"; DEBT_ITEMS=$((DEBT_ITEMS + 1)); }
warn()  { echo -e "  ${YELLOW}⚠ [WARN]${NC} $1"; }

info "1. Scanning for Untracked Machine-Local Tooling and Symlink Escapes"
for dir in .serena .antigravitycli .cache; do
  if [ -d "$dir" ]; then
    if ! git check-ignore -q "$dir" 2>/dev/null; then
      debt "Untracked directory '$dir' is not listed in .gitignore"
    fi
  fi
done

# Check for symlinks escaping repository root
for symlink in $(find . -type l -not -path '*/.git/*' 2>/dev/null); do
  target="$(readlink "$symlink")"
  if [[ "$target" == /* ]] || [[ "$target" == ../* ]]; then
    debt "Symlink '$symlink' points outside repository root ($target)"
  fi
done

info "2. Scanning Agent Skills for Frontmatter & Conformance Debt"
find_skills() {
  find . -type f -name "SKILL.md" -not -path '*/.git/*' | sort
}

for skill_md in $(find_skills); do
  skill_dir="$(dirname "$skill_md")"
  expected_name="$(basename "$skill_dir")"

  # Frontmatter check
  read_res="$(python3 -c "
import json, sys, os, re

filepath = '$skill_md'
content = open(filepath, 'r', encoding='utf-8').read()

if not content.startswith('---'):
    print(json.dumps({'error': 'Missing YAML frontmatter delimiter at start'}))
    sys.exit(0)

parts = content.split('---', 2)
if len(parts) < 3:
    print(json.dumps({'error': 'Malformed YAML frontmatter delimiters'}))
    sys.exit(0)

fm_text = parts[1]

def get_val(key, text):
    m = re.search(r'^' + key + r':\s*(.*)$', text, re.MULTILINE)
    if not m:
        return ''
    val = m.group(1).strip()
    if (val.startswith('\"') and val.endswith('\"')) or (val.startswith(\"'\") and val.endswith(\"'\")):
        val = val[1:-1]
    return val

name = get_val('name', fm_text)
desc = get_val('description', fm_text)
lic = get_val('license', fm_text)
top_ver = get_val('version', fm_text)

print(json.dumps({'name': name, 'desc': desc, 'desc_len': len(desc), 'license': lic, 'top_ver': top_ver}))
" 2>/dev/null || echo '{"error": "python parse error"}')"

  has_err="$(echo "$read_res" | python3 -c "import json,sys; print(json.load(sys.stdin).get('error',''))" 2>/dev/null || true)"
  if [ -n "$has_err" ]; then
    debt "Skill at '$skill_md': $has_err"
    continue
  fi

  name_in_fm="$(echo "$read_res" | python3 -c "import json,sys; print(json.load(sys.stdin).get('name',''))" 2>/dev/null || true)"
  desc_len="$(echo "$read_res" | python3 -c "import json,sys; print(json.load(sys.stdin).get('desc_len',0))" 2>/dev/null || echo 0)"
  lic_in_fm="$(echo "$read_res" | python3 -c "import json,sys; print(json.load(sys.stdin).get('license',''))" 2>/dev/null || true)"
  top_ver="$(echo "$read_res" | python3 -c "import json,sys; print(json.load(sys.stdin).get('top_ver',''))" 2>/dev/null || true)"

  if [ "$name_in_fm" != "$expected_name" ]; then
    debt "Skill '$skill_md' frontmatter name ('$name_in_fm') != directory '$expected_name'"
  fi

  if [ "$desc_len" -eq 0 ]; then
    debt "Skill '$expected_name' missing description in frontmatter"
  elif [ "$desc_len" -gt 1024 ]; then
    debt "Skill '$expected_name' description exceeds 1024 characters ($desc_len chars)"
  fi

  if [ -n "$top_ver" ]; then
    debt "Skill '$expected_name' has top-level version: field (should be under metadata.version)"
  fi

  if [ -z "$lic_in_fm" ]; then
    warn "Skill '$expected_name' missing license in frontmatter"
  fi

  # Check scripts executable bit
  if [ -d "$skill_dir/scripts" ]; then
    for script in "$skill_dir/scripts"/*; do
      [ -f "$script" ] || continue
      if [ ! -x "$script" ]; then
        debt "Script '$script' in '$expected_name' is not executable (+x)"
      fi
    done
  fi

  # Check for ../ cross-skill links
  parent_links="$(grep -o '\[.*\](\.\./[^)]*)' "$skill_md" || true)"
  if [ -n "$parent_links" ]; then
    warn "Skill '$expected_name' has parent-relative links (co-dependency candidate for plugin grouping):\n$parent_links"
  fi
done

info "3. Checking Root Files & Plugin Structure"
if [ ! -d "plugins" ]; then
  warn "Repository does not use 'plugins/' layout yet"
fi
if [ ! -f "LICENSE" ]; then
  debt "Missing root LICENSE file"
fi
if [ ! -f ".claude-plugin/marketplace.json" ]; then
  warn "Missing .claude-plugin/marketplace.json index"
fi

echo
if [ "$DEBT_ITEMS" -eq 0 ]; then
  echo -e "${GREEN}✓ No critical conformance debt found! Repository is in good shape.${NC}"
else
  echo -e "${YELLOW}Found $DEBT_ITEMS conformance debt item(s) to address before/during plugin migration.${NC}"
fi
