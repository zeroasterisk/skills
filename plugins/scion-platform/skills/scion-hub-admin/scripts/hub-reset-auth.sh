#!/usr/bin/env bash
# hub-reset-auth.sh — Re-mint and hot-inject fresh JWT tokens into running Scion agents
set -euo pipefail

HUB_URL="${SCION_HUB_ENDPOINT:-}"
TARGET_MODE=""
AGENT_ID=""

usage() {
  cat <<EOF
Usage: $(basename "$0") --hub <https://hub.example.com/> (--all | --agent <agent-id>)

Options:
  --hub <url>       Scion Hub base URL
  --all             Re-mint and hot-inject tokens for all running agents (POST /api/v1/admin/agents/reset-auth-all)
  --agent <id>      Re-mint and hot-inject token for a specific agent UUID (POST /api/v1/agents/{id}/reset-auth)
EOF
  exit 1
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --hub)
      HUB_URL="$2"
      shift 2
      ;;
    --all)
      TARGET_MODE="all"
      shift
      ;;
    --agent)
      TARGET_MODE="single"
      AGENT_ID="$2"
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

if [[ -z "$HUB_URL" || -z "$TARGET_MODE" ]]; then
  usage
fi

[[ "$HUB_URL" != */ ]] && HUB_URL="${HUB_URL}/"
API_BASE="${HUB_URL%/}"

for cmd in scion jq curl; do
  if ! command -v "$cmd" >/dev/null 2>&1; then
    echo "Error: Required command '$cmd' not found in PATH." >&2
    exit 1
  fi
done

CREDS_FILE="${HOME}/.scion/credentials.json"
TOKEN=$(jq -r --arg hub "$HUB_URL" '.hubs[$hub].accessToken // empty' "$CREDS_FILE")
if [[ -z "$TOKEN" ]]; then
  echo "Error: No accessToken found for $HUB_URL in $CREDS_FILE." >&2
  exit 1
fi

if [[ "$TARGET_MODE" == "all" ]]; then
  echo "Dispatching bulk auth token reset on $API_BASE/api/v1/admin/agents/reset-auth-all ..."
  RESP=$(curl -s -X POST -H "Authorization: Bearer $TOKEN" "$API_BASE/api/v1/admin/agents/reset-auth-all")
  echo "$RESP" | jq '{total, succeededCount: (.succeeded | length), failed}'
else
  echo "Dispatching auth token reset for agent $AGENT_ID ..."
  curl -s -X POST -H "Authorization: Bearer $TOKEN" "$API_BASE/api/v1/agents/$AGENT_ID/reset-auth" | jq .
fi
