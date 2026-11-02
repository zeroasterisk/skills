#!/usr/bin/env bash
# hub-quota-manage.sh — Audit and configure Scion Hub quota limits and broker agent ceilings
set -euo pipefail

HUB_URL="${SCION_HUB_ENDPOINT:-}"
BROKER_ID=""
SET_CEILING=""
OUTPUT_JSON=false

usage() {
  cat <<EOF
Usage: $(basename "$0") --hub <https://hub.example.com/> [options]

Options:
  --hub <url>                   Hub endpoint URL (required or via SCION_HUB_ENDPOINT)
  --broker <broker-id>          Target runtime broker ID (defaults to first online broker)
  --set-broker-ceiling <count>  Create or update max_agents_per_broker entitlement for broker (0 = unlimited)
  --json                        Output results in JSON format
  -h, --help                    Show this help message

Examples:
  # Audit current quota definitions, entitlements, and active broker usage:
  $(basename "$0") --hub https://chinoy.projects.scion-ai.dev/

  # Raise max_agents_per_broker ceiling to 200 on the default broker:
  $(basename "$0") --hub https://chinoy.projects.scion-ai.dev/ --set-broker-ceiling 200
EOF
  exit 1
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --hub)
      HUB_URL="$2"
      shift 2
      ;;
    --broker)
      BROKER_ID="$2"
      shift 2
      ;;
    --set-broker-ceiling)
      SET_CEILING="$2"
      shift 2
      ;;
    --json)
      OUTPUT_JSON=true
      shift
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
  echo "Error: $CREDS_FILE not found. Authenticate first." >&2
  exit 1
fi

TOKEN=$(jq -r --arg h "$HUB_URL" --arg h2 "$API_BASE" '.hubs[$h].accessToken // .hubs[$h2].accessToken // empty' "$CREDS_FILE")
if [[ -z "$TOKEN" ]]; then
  echo "Error: No access token for $HUB_URL found in $CREDS_FILE." >&2
  exit 1
fi

LIMITS_RAW=$(curl -sS -H "Authorization: Bearer $TOKEN" "${API_BASE}/api/v1/admin/limits")
BROKERS_RAW=$(curl -sS -H "Authorization: Bearer $TOKEN" "${API_BASE}/api/v1/runtime-brokers")

BROKER_LIMIT_ID=$(echo "$LIMITS_RAW" | jq -r '.items[]? | select(.name == "max_agents_per_broker") | .id // empty')
if [[ -z "$BROKER_LIMIT_ID" ]]; then
  echo "Error: max_agents_per_broker limit definition not found on $API_BASE." >&2
  exit 1
fi

if [[ -z "$BROKER_ID" ]]; then
  BROKER_ID=$(echo "$BROKERS_RAW" | jq -r '(.brokers // .items // .)[0].id // empty')
fi

if [[ -n "$SET_CEILING" ]]; then
  if [[ -z "$BROKER_ID" ]]; then
    echo "Error: Could not resolve runtime broker ID; specify --broker <id>." >&2
    exit 1
  fi

  ENTS_RAW=$(curl -sS -H "Authorization: Bearer $TOKEN" "${API_BASE}/api/v1/admin/limits/${BROKER_LIMIT_ID}/entitlements")
  EXISTING_ENT_ID=$(echo "$ENTS_RAW" | jq -r --arg bid "$BROKER_ID" '.items[]? | select(.subjectId == $bid and .scopeId == $bid) | .id // empty' | head -n 1)

  PAYLOAD=$(jq -n --arg bid "$BROKER_ID" --argjson val "$SET_CEILING" '{
    subjectType: "user",
    subjectId: $bid,
    scopeType: "broker",
    scopeId: $bid,
    value: $val
  }')

  if [[ -n "$EXISTING_ENT_ID" ]]; then
    RESP=$(curl -sS -X PUT "${API_BASE}/api/v1/admin/entitlements/${EXISTING_ENT_ID}" \
      -H "Authorization: Bearer $TOKEN" \
      -H "Content-Type: application/json" \
      -d "$PAYLOAD")
  else
    RESP=$(curl -sS -X POST "${API_BASE}/api/v1/admin/limits/${BROKER_LIMIT_ID}/entitlements" \
      -H "Authorization: Bearer $TOKEN" \
      -H "Content-Type: application/json" \
      -d "$PAYLOAD")
  fi

  if [[ "$OUTPUT_JSON" == "true" ]]; then
    echo "$RESP" | jq .
  else
    echo "✓ Configured max_agents_per_broker entitlement on broker $BROKER_ID -> value=$SET_CEILING"
    echo "$RESP" | jq '{id, limitDefinitionId, subjectId, scopeType, scopeId, value}'
  fi
  exit 0
fi

ENTS_RAW=$(curl -sS -H "Authorization: Bearer $TOKEN" "${API_BASE}/api/v1/admin/limits/${BROKER_LIMIT_ID}/entitlements")
AGENTS_RAW=$(curl -sS -H "Authorization: Bearer $TOKEN" "${API_BASE}/api/v1/agents?limit=500")

REPORT=$(jq -n \
  --argjson limits "$LIMITS_RAW" \
  --argjson brokers "$BROKERS_RAW" \
  --argjson ents "$ENTS_RAW" \
  --argjson agents "$AGENTS_RAW" '
  ($limits.items // []) as $l_items |
  ($brokers.brokers // $brokers.items // []) as $b_items |
  ($ents.items // []) as $e_items |
  ($agents.agents // []) as $a_items |
  ($l_items[] | select(.name == "max_agents_per_broker") | .defaultValue) as $default_cap |
  {
    limits: $l_items,
    brokerQuotas: [
      $b_items[] |
      .id as $bid |
      ([ $e_items[] | select(.subjectId == $bid and (.scopeType == "broker" or .scopeType == "system")) | .value ]) as $bound_vals |
      (if ($bound_vals | length) == 0 then $default_cap
       elif ([ $bound_vals[] | select(. <= 0) ] | length) > 0 then 0
       else ($bound_vals | max) end) as $effective |
      ([ $a_items[] | select(.runtimeBrokerId == $bid and (.phase != "stopped" and .phase != "suspended" and .phase != "error")) ] | length) as $counted |
      {
        brokerId: $bid,
        brokerName: .name,
        status: .status,
        countedAgents: $counted,
        defaultCeiling: $default_cap,
        effectiveCeiling: $effective,
        entitlements: [ $e_items[] | select(.subjectId == $bid) ],
        throttled: ($effective > 0 and $counted >= $effective)
      }
    ]
  }
')

if [[ "$OUTPUT_JSON" == "true" ]]; then
  echo "$REPORT"
  exit 0
fi

echo "================================================================================"
echo "Scion Hub Quota & Broker Ceiling Report — $API_BASE"
echo "================================================================================"
echo "$REPORT" | jq -r '
  .brokerQuotas[] |
  "Broker: \(.brokerName) (\(.brokerId)) [status: \(.status)]\n" +
  "  Counted Live Agents : \(.countedAgents)\n" +
  "  Default Ceiling     : \(.defaultCeiling)\n" +
  "  Effective Ceiling   : \(if .effectiveCeiling == 0 then "unlimited (0)" else (.effectiveCeiling | tostring) end)\n" +
  "  Status              : \(if .throttled then "⚠️  AT/OVER CEILING (will reject create/start/wake with HTTP 429!)" else "✓ OK" end)\n"
'
