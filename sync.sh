#!/usr/bin/env bash
# sync.sh — Skills registry sync
#
# Reads registry.yaml and:
#   1. Resolves which skills exist on this machine (skips missing paths silently)
#   2. Updates cloudcode.json skills.paths for cloudcode-agent skills
#   3. Creates/cleans symlinks in ~/.gemini/config/skills/ for gemini-agent skills
#   4. Emits ai-catalog.json per source bundle + root aggregate
#
# Catalog layout:
#   <bundle-dir>/ai-catalog.json   one per source bundle (e.g. zeroasterisk/skills/)
#   ai-catalog.json                aggregate across all resolved bundles on this machine
#
# Usage:
#   ./sync.sh               # normal sync
#   ./sync.sh --dry-run     # print what would happen, change nothing
#   ./sync.sh --verbose     # print all actions including skips

set -euo pipefail

REGISTRY_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REGISTRY_FILE="$REGISTRY_DIR/registry.yaml"
CATALOG_FILE="$REGISTRY_DIR/ai-catalog.json"
CLOUDCODE_CONFIG="$HOME/dotfiles/config/cloudcode/cloudcode.json"
GEMINI_SKILLS_DIR="$HOME/.gemini/config/skills"
AGENTS_SKILLS_DIR="$HOME/.agents/skills"

DRY_RUN=false
VERBOSE=false
for arg in "$@"; do
  case "$arg" in
    --dry-run) DRY_RUN=true ;;
    --verbose) VERBOSE=true ;;
  esac
done

log()     { echo "[sync] $*"; }
verbose() { $VERBOSE && echo "[sync] $*" || true; }
dry()     { $DRY_RUN && echo "[dry-run] $*" || true; }

# ---------------------------------------------------------------------------
# 1. Parse registry.yaml with Python (stdlib only, no pyyaml needed)
#    Outputs one JSON object per skill to stdout
# ---------------------------------------------------------------------------

SKILLS_JSON=$(python3 - <<'PYEOF'
import sys, re, json

with open("registry.yaml") as f:
    content = f.read()

# Split on "- name:" blocks (handles comments and blank lines)
blocks = re.split(r'\n(?=- name:)', content)
skills = []

for block in blocks:
    block = block.strip()
    if not block or block.startswith('#'):
        continue
    # Strip leading "- "
    block = re.sub(r'^-\s*', '', block, count=1)

    skill = {}
    for line in block.splitlines():
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        if ':' not in line:
            continue
        key, _, val = line.partition(':')
        key = key.strip()
        val = val.strip()

        # Parse list values like [cloudcode, gemini]
        if val.startswith('[') and val.endswith(']'):
            val = [v.strip() for v in val[1:-1].split(',') if v.strip()]
        # Parse booleans
        elif val.lower() == 'true':
            val = True
        elif val.lower() == 'false':
            val = False

        skill[key] = val

    if 'name' in skill:
        skills.append(skill)

print(json.dumps(skills))
PYEOF
)

# ---------------------------------------------------------------------------
# 2. Resolve which skills are available on this machine
# ---------------------------------------------------------------------------

RESOLVED=()        # names of active+present skills
declare -A SKILL_PATHS    # name -> absolute path
declare -A SKILL_META     # name -> full JSON blob

while IFS= read -r skill_json; do
    name=$(echo "$skill_json" | jq -r '.name')
    active=$(echo "$skill_json" | jq -r '.active // true')
    rel_path=$(echo "$skill_json" | jq -r '.path')
    abs_path="$REGISTRY_DIR/$rel_path"

    if [[ "$active" != "true" ]]; then
        verbose "skip (inactive): $name"
        continue
    fi

    if [[ ! -d "$abs_path" ]]; then
        verbose "skip (path missing on this machine): $name @ $abs_path"
        continue
    fi

    # Pull name/description from SKILL.md frontmatter if present
    skill_md="$abs_path/SKILL.md"
    fm_name=""
    fm_desc=""
    if [[ -f "$skill_md" ]]; then
        fm_name=$(awk '/^---/{f++} f==1 && /^name:/{sub(/^name:\s*/,""); print; exit}' "$skill_md")
        fm_desc=$(awk '/^---/{f++} f==1 && /^description:/{sub(/^description:\s*/,""); print; exit}' "$skill_md")
    fi
    [[ -z "$fm_name" ]] && fm_name="$name"
    [[ -z "$fm_desc" ]] && fm_desc=$(echo "$skill_json" | jq -r '.description // ""')

    # Merge resolved metadata back into JSON
    skill_json=$(echo "$skill_json" | jq \
        --arg p "$abs_path" \
        --arg fn "$fm_name" \
        --arg fd "$fm_desc" \
        '. + {resolved_path: $p, resolved_name: $fn, resolved_description: $fd}')

    RESOLVED+=("$name")
    SKILL_PATHS["$name"]="$abs_path"
    SKILL_META["$name"]="$skill_json"

    log "resolved: $name"
done < <(echo "$SKILLS_JSON" | jq -c '.[]')

log "${#RESOLVED[@]} skill(s) resolved on this machine"

# ---------------------------------------------------------------------------
# 3. CloudCode — update skills.paths in cloudcode.json
# ---------------------------------------------------------------------------

cc_paths=()
for name in "${RESOLVED[@]}"; do
    agents=$(echo "${SKILL_META[$name]}" | jq -r '.agents // [] | join(",")')
    if [[ "$agents" == *"cloudcode"* ]]; then
        cc_paths+=("${SKILL_PATHS[$name]}")
    fi
done

if [[ -f "$CLOUDCODE_CONFIG" ]]; then
    # Build jq-safe JSON array of paths
    cc_paths_json=$(printf '%s\n' "${cc_paths[@]}" | jq -R . | jq -s .)
    new_config=$(jq --argjson paths "$cc_paths_json" \
        '.skills.paths = $paths' "$CLOUDCODE_CONFIG")

    if $DRY_RUN; then
        dry "would write cloudcode.json skills.paths: $(echo $cc_paths_json)"
    else
        echo "$new_config" > "$CLOUDCODE_CONFIG"
        log "cloudcode: updated skills.paths (${#cc_paths[@]} path(s))"
    fi
else
    log "cloudcode: config not found at $CLOUDCODE_CONFIG, skipping"
fi

# ---------------------------------------------------------------------------
# 4. Gemini — symlink into ~/.gemini/config/skills/
# ---------------------------------------------------------------------------

if $DRY_RUN; then
    dry "would ensure dir: $GEMINI_SKILLS_DIR"
else
    mkdir -p "$GEMINI_SKILLS_DIR"
fi

# Remove stale symlinks (point to missing targets or no longer in resolved set)
while IFS= read -r link; do
    target=$(readlink "$link" 2>/dev/null || true)
    link_name=$(basename "$link")

    # Only manage symlinks we created (target is inside REGISTRY_DIR)
    if [[ "$target" != "$REGISTRY_DIR"* ]]; then
        verbose "gemini: skip unmanaged entry: $link_name"
        continue
    fi

    if [[ ! -d "$target" ]]; then
        if $DRY_RUN; then
            dry "would remove stale symlink: $link_name"
        else
            rm "$link"
            log "gemini: removed stale symlink: $link_name"
        fi
    fi
done < <(find "$GEMINI_SKILLS_DIR" -maxdepth 1 -type l 2>/dev/null || true)

# Create/update symlinks for gemini-agent skills
for name in "${RESOLVED[@]}"; do
    agents=$(echo "${SKILL_META[$name]}" | jq -r '.agents // [] | join(",")')
    if [[ "$agents" != *"gemini"* ]]; then
        continue
    fi

    abs_path="${SKILL_PATHS[$name]}"
    link="$GEMINI_SKILLS_DIR/$name"

    # Only symlink if GEMINI.md exists
    if [[ ! -f "$abs_path/GEMINI.md" ]]; then
        verbose "gemini: skip $name (no GEMINI.md)"
        continue
    fi

    if $DRY_RUN; then
        dry "would symlink: $link -> $abs_path"
    else
        ln -sfn "$abs_path" "$link"
        log "gemini: linked $name"
    fi
done

# ---------------------------------------------------------------------------
# 5. Emit ai-catalog.json — per bundle, then aggregate
# ---------------------------------------------------------------------------

# Helper: build a catalog JSON blob from a JSON array of skill entries
make_catalog() {
    local entries="$1"
    local bundle="$2"   # empty string for aggregate
    local cc_view gemini_view

    cc_view=$(echo "$entries"     | jq '[.[] | select(.agents | contains(["cloudcode"]))]')
    gemini_view=$(echo "$entries" | jq '[.[] | select(.agents | contains(["gemini"]))]')

    jq -n \
        --arg ts "$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
        --arg bundle "$bundle" \
        --argjson all "$entries" \
        --argjson cloudcode "$cc_view" \
        --argjson gemini "$gemini_view" \
        '{
            generated_at: $ts,
            bundle: $bundle,
            total: ($all | length),
            skills: $all,
            by_agent: {
                cloudcode: $cloudcode,
                gemini: $gemini
            }
        }'
}

# Collect all entries and group by source bundle
declare -A BUNDLE_ENTRIES   # source -> JSON array string
all_entries="[]"

for name in "${RESOLVED[@]}"; do
    meta="${SKILL_META[$name]}"
    source=$(echo "$meta" | jq -r '.source // "unknown"')

    entry=$(echo "$meta" | jq '{
        name: .resolved_name,
        description: .resolved_description,
        audience: (.audience // "personal"),
        source: (.source // ""),
        tags: (.tags // []),
        agents: (.agents // []),
        registry_name: .name
    }')

    all_entries=$(echo "$all_entries" | jq --argjson e "$entry" '. + [$e]')

    # Accumulate per bundle
    existing="${BUNDLE_ENTRIES[$source]:-[]}"
    BUNDLE_ENTRIES["$source"]=$(echo "$existing" | jq --argjson e "$entry" '. + [$e]')
done

# Write per-bundle catalogs into their bundle directory
for source in "${!BUNDLE_ENTRIES[@]}"; do
    entries="${BUNDLE_ENTRIES[$source]}"

    # Derive bundle dir: first path segment of the source entries
    # e.g. source "zeroasterisk/skills" -> skill paths start with $REGISTRY_DIR/...
    # Use the resolved_path of the first entry to find the bundle root
    first_path=$(echo "$entries" | jq -r '.[0].path // ""')
    if [[ -z "$first_path" ]]; then
        continue
    fi

    # Find the catalog path for this bundle.
    # Strategy: look at the resolved skill paths. If all skills in this bundle
    # share a common subdirectory under REGISTRY_DIR, write the catalog there.
    # If they live directly in REGISTRY_DIR (flat personal layout), write
    # alongside registry.yaml as ai-catalog.<safe-source-slug>.json

    # Find common prefix of all skill paths in this bundle
    bundle_root=""
    while IFS= read -r skill_path; do
        parent=$(dirname "$skill_path")
        if [[ -z "$bundle_root" ]]; then
            bundle_root="$parent"
        elif [[ "$parent" != "$bundle_root" ]]; then
            bundle_root="$REGISTRY_DIR"  # mixed parents, fall back to root
            break
        fi
    done < <(echo "$entries" | jq -r '.[].path')

    if [[ "$bundle_root" == "$REGISTRY_DIR" ]]; then
        # Skills live flat in registry root (personal bundle)
        safe_source=$(echo "$source" | tr '/' '-' | sed 's/[^a-zA-Z0-9_-]/-/g')
        bundle_catalog="$REGISTRY_DIR/ai-catalog.${safe_source}.json"
    else
        # Skills live in a subdirectory — catalog goes there
        bundle_catalog="$bundle_root/ai-catalog.json"
    fi

    catalog=$(make_catalog "$entries" "$source")

    if $DRY_RUN; then
        dry "would write bundle catalog: $bundle_catalog ($(echo "$entries" | jq length) skills, source: $source)"
    else
        echo "$catalog" > "$bundle_catalog"
        log "catalog: wrote $bundle_catalog ($(echo "$entries" | jq length) skill(s), source: $source)"
    fi
done

# Write root aggregate catalog
agg_catalog=$(make_catalog "$all_entries" "")

if $DRY_RUN; then
    dry "would write aggregate catalog: $CATALOG_FILE ($(echo "$all_entries" | jq length) skills total)"
    echo "$agg_catalog" | jq .
else
    echo "$agg_catalog" > "$CATALOG_FILE"
    log "catalog: wrote aggregate $CATALOG_FILE ($(echo "$all_entries" | jq length) total)"
fi

log "done"
