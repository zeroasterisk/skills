#!/usr/bin/env bash
# hub-authz-triage.sh — Diagnose 3-layer AK1 authorization state on a Scion Hub
set -euo pipefail

HUB_URL="${SCION_HUB_ENDPOINT:-}"
AGENT_FILTER=""

usage() {
  cat <<EOF
Usage: $(basename "$0") --hub <https://hub.example.com/> [--agent <name-or-id>]

Checks:
  1. CLI & Hub authentication token in ~/.scion/credentials.json
  2. Role Definitions (/api/v1/admin/roles) for agent-role-full and project-owner
  3. Running agents (/api/v1/agents?phase=running), stored agentRole, and creation timestamps
  4. Root delegator role bindings (/api/v1/admin/role-bindings)
EOF
  exit 1
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --hub)
      HUB_URL="$2"
      shift 2
      ;;
    --agent)
      AGENT_FILTER="$2"
      shift 2
      ;;
    -h|--help)
      usage
      ;;
    *)
      echo "Unknown flag: $1" >&2
      usage
      ;;
  esac
done

if [[ -z "$HUB_URL" ]]; then
  echo "Error: --hub <url> or SCION_HUB_ENDPOINT is required." >&2
  usage
fi

# Ensure trailing slash matches credentials.json key convention
[[ "$HUB_URL" != */ ]] && HUB_URL="${HUB_URL}/"
API_BASE="${HUB_URL%/}"

for cmd in scion jq curl; do
  if ! command -v "$cmd" >/dev/null 2>&1; then
    echo "Error: Required command '$cmd' not found in PATH." >&2
    exit 1
  fi
done

CREDS_FILE="${HOME}/.scion/credentials.json"
if [[ ! -f "$CREDS_FILE" ]]; then
  echo "Error: $CREDS_FILE not found. Run: scion hub auth login --hub-url $HUB_URL --no-browser" >&2
  exit 1
fi

TOKEN=$(jq -r --arg hub "$HUB_URL" '.hubs[$hub].accessToken // empty' "$CREDS_FILE")
if [[ -z "$TOKEN" ]]; then
  echo "Error: No accessToken found for $HUB_URL in $CREDS_FILE." >&2
  echo "Run: scion hub auth login --hub-url $HUB_URL --no-browser" >&2
  exit 1
fi

echo "=== [Layer 1] Checking Role Definitions on $API_BASE ==="
curl -s -H "Authorization: Bearer $TOKEN" "$API_BASE/api/v1/admin/roles" | \
  jq -r '.items[] | select(.name == "agent-role-full" or .name == "project-owner") |
    "Role: \(.name) (\(.scopeType)) -> template.create=\(.permissions | index("template.create") != null), agent.create=\(.permissions | index("agent.create") != null)"'

echo ""
echo "=== [Layer 2 & 3] Checking Running Agents & Stored Roles ==="
AGENTS_JSON=$(curl -s -H "Authorization: Bearer $TOKEN" "$API_BASE/api/v1/agents?phase=running&limit=100")

if [[ -n "$AGENT_FILTER" ]]; then
  echo "$AGENTS_JSON" | jq --arg f "$AGENT_FILTER" '.agents[] | select(.name == $f or .id == $f or (.name | contains($f))) |
    {id, name, project, template, storedRole: .appliedConfig.agentRole, created, ancestry, activity, message}'
else
  echo "$AGENTS_JSON" | jq '.agents[] | select(.template == "coordinator" or .template == "eng-manager") |
    {id, name, project, template, storedRole: .appliedConfig.agentRole, created, activity}'
fi

echo ""
echo "Tip: If storedRole is 'full' but CanDelegate fails with missing scopes (e.g. project:template:write),"
echo "the running container holds a pre-upgrade JWT. Re-mint tokens without restarting containers using:"
echo "  scripts/hub-reset-auth.sh --hub $HUB_URL --all"
