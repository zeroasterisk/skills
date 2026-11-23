#!/usr/bin/env bash
# hub-rebuild-server.sh — Trigger and monitor Scion Hub server rebuild via Admin Maintenance API
set -euo pipefail

HUB_URL="${SCION_HUB_ENDPOINT:-}"
BRANCH=""
TIMEOUT_SECONDS=300

usage() {
  cat <<EOF
Usage: $(basename "$0") --hub <https://hub.example.com/> [options]

Options:
  --hub <url>          Hub endpoint URL (required or via SCION_HUB_ENDPOINT)
  --branch <branch>    Override git branch to checkout on server (defaults to server config)
  --timeout <seconds>  Max time to wait for rebuild (default: 300s)
  -h, --help           Show this help message

Workflows:
  1. Checks current server Scion version vs local binary version
  2. Dispatches 'rebuild-server' via POST /api/v1/admin/maintenance/operations/rebuild-server/run
  3. Streams build output and tracks execution status
  4. Waits for systemd service restart and verifies updated version
EOF
  exit 1
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --hub)
      HUB_URL="$2"
      shift 2
      ;;
    --branch)
      BRANCH="$2"
      shift 2
      ;;
    --timeout)
      TIMEOUT_SECONDS="$2"
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

[[ "$HUB_URL" != */ ]] && HUB_URL="${HUB_URL}/"
API_BASE="${HUB_URL%/}"

for cmd in jq curl; do
  if ! command -v "$cmd" >/dev/null 2>&1; then
    echo "Error: Required command '$cmd' not found in PATH." >&2
    exit 1
  fi
done

CREDS_FILE="${HOME}/.scion/credentials.json"
if [[ ! -f "$CREDS_FILE" ]]; then
  echo "Error: $CREDS_FILE not found. Authenticate first with: scion hub auth login --hub-url $HUB_URL --no-browser" >&2
  exit 1
fi

TOKEN=$(jq -r --arg h "$HUB_URL" '.hubs[$h].accessToken // empty' "$CREDS_FILE")
if [[ -z "$TOKEN" ]]; then
  echo "Error: No access token for $HUB_URL found in $CREDS_FILE." >&2
  exit 1
fi

echo "================================================================================"
echo "Scion Hub Server Rebuild & Upgrade — $API_BASE"
echo "================================================================================"

# Step 1: Pre-flight check
HEALTH_RESP=$(curl -s -H "Authorization: Bearer $TOKEN" "${API_BASE}/api/v1/health")
SERVER_VERSION=$(echo "$HEALTH_RESP" | jq -r '.version // "unknown"')
echo "Current Server Version: $SERVER_VERSION"

# Step 2: Trigger rebuild-server
PAYLOAD="{}"
if [[ -n "$BRANCH" ]]; then
  PAYLOAD=$(jq -n --arg b "$BRANCH" '{"branch": $b}')
fi

echo "Dispatching 'rebuild-server' maintenance operation..."
TRIGGER_RESP=$(curl -s -X POST "${API_BASE}/api/v1/admin/maintenance/operations/rebuild-server/run" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "$PAYLOAD")

RUN_ID=$(echo "$TRIGGER_RESP" | jq -r '.runId // empty')
if [[ -z "$RUN_ID" ]]; then
  echo "Error: Failed to initiate rebuild: $TRIGGER_RESP" >&2
  exit 1
fi

echo "Rebuild operation started (Run ID: $RUN_ID). Monitoring execution..."
echo ""

# Step 3: Monitor until completion or timeout
START_TIME=$(date +%s)
PREV_LOG_LEN=0

while true; do
  CURRENT_TIME=$(date +%s)
  ELAPSED=$((CURRENT_TIME - START_TIME))
  if [[ "$ELAPSED" -gt "$TIMEOUT_SECONDS" ]]; then
    echo "Error: Timed out waiting for rebuild to complete after ${TIMEOUT_SECONDS}s." >&2
    exit 1
  fi

  RUN_RESP=$(curl -s -H "Authorization: Bearer $TOKEN" "${API_BASE}/api/v1/admin/maintenance/operations/rebuild-server/runs/${RUN_ID}" 2>/dev/null || true)
  
  if [[ -n "$RUN_RESP" ]] && echo "$RUN_RESP" | jq -e . >/dev/null 2>&1; then
    STATUS=$(echo "$RUN_RESP" | jq -r '.status // "unknown"')
    LOG=$(echo "$RUN_RESP" | jq -r '.log // empty')
    
    if [[ "$STATUS" == "completed" ]]; then
      echo ""
      echo "✓ Rebuild operation completed successfully on server."
      break
    elif [[ "$STATUS" == "failed" ]]; then
      echo ""
      echo "✗ Rebuild operation failed:"
      echo "$RUN_RESP" | jq -r '.result // empty'
      echo "--- Full Log ---"
      echo "$LOG"
      exit 1
    fi
  else
    # Server might be restarting
    echo -n "."
  fi

  sleep 5
done

# Step 4: Wait for server restart and verify health
echo "Waiting for Hub service to restart..."
NEW_VERSION="unknown"
for i in {1..20}; do
  sleep 3
  CHECK_RESP=$(curl -s "${API_BASE}/api/v1/health" 2>/dev/null || true)
  if [[ -n "$CHECK_RESP" ]] && echo "$CHECK_RESP" | jq -e . >/dev/null 2>&1; then
    NEW_VERSION=$(echo "$CHECK_RESP" | jq -r '.version // "unknown"')
    if [[ "$NEW_VERSION" != "unknown" ]]; then
      break
    fi
  fi
  echo -n "."
done

echo ""
echo "================================================================================"
echo "Hub Server Rebuild Complete"
echo "================================================================================"
echo "Previous Version: $SERVER_VERSION"
echo "New Version:      $NEW_VERSION"
echo "Hub Endpoint:     $API_BASE"
