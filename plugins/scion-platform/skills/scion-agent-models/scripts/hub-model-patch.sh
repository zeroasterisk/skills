#!/usr/bin/env bash
# hub-model-patch.sh — Live-switch model configurations on Scion agents (with optional container recreate)
set -euo pipefail

HUB_URL="${SCION_HUB_ENDPOINT:-}"
AGENT_TARGET=""
PROJECT_FILTER=""
TEMPLATE_FILTER=""
NEW_MODEL=""
RESTART_CONTAINERS=false
DRY_RUN=false
OUTPUT_JSON=false

usage() {
  cat <<EOF
Usage: $(basename "$0") --hub <https://hub.example.com/> --model <model-identifier> [targets] [options]

Targeting (specify at least one):
  --agent <id|slug>        Target a specific agent by ID or slug
  --project <id|slug>      Filter targets to a specific project
  --template <name>        Filter targets by agent template (e.g. 'coordinator', 'developer')
  --all                    Target all matching active agents

Required:
  --model <model>          Model string to set (e.g. 'claude-opus-5-5@default', 'Gemini 3.8 Flash (Medium)')

Options:
  --hub <url>              Hub endpoint URL (required or via SCION_HUB_ENDPOINT)
  --restart-containers     Stop and start running agents first so recreated containers pick up updated Hub/project env vars (e.g. CLOUD_ML_REGION=global)
  --dry-run                Preview matching agents and proposed actions without applying
  --json                   Output results in JSON format
  -h, --help               Show this help message

Examples:
  # Switch a single running coordinator by ID:
  $(basename "$0") --hub \$HUB --agent 1e156f1c-7ace... --model claude-opus-5-5@default

  # Recreate containers (to pick up CLOUD_ML_REGION=global) and switch all coordinators to claude-opus-5-5@default:
  $(basename "$0") --hub \$HUB --all --template coordinator --restart-containers --model claude-opus-5-5@default
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
      AGENT_TARGET="$2"
      shift 2
      ;;
    --project)
      PROJECT_FILTER="$2"
      shift 2
      ;;
    --template)
      TEMPLATE_FILTER="$2"
      shift 2
      ;;
    --model)
      NEW_MODEL="$2"
      shift 2
      ;;
    --restart-containers)
      RESTART_CONTAINERS=true
      shift
      ;;
    --dry-run)
      DRY_RUN=true
      shift
      ;;
    --all)
      shift
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

if [[ -z "$NEW_MODEL" ]]; then
  echo "Error: --model <model-name> is required." >&2
  usage
fi

if [[ -z "$AGENT_TARGET" && -z "$PROJECT_FILTER" && -z "$TEMPLATE_FILTER" ]]; then
  echo "Error: You must specify a target: --agent, --project, or --template." >&2
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

TOKEN=$(jq -r --arg h "$HUB_URL" --arg h2 "$API_BASE" '.hubs[$h].accessToken // .hubs[$h2].accessToken // empty' "$CREDS_FILE")
if [[ -z "$TOKEN" ]]; then
  echo "Error: No access token for $HUB_URL found in $CREDS_FILE." >&2
  exit 1
fi

AGENTS_RAW=$(curl -s -H "Authorization: Bearer $TOKEN" "${API_BASE}/api/v1/agents?limit=250")

MATCHES=$(echo "$AGENTS_RAW" | jq \
  --arg a_target "$AGENT_TARGET" \
  --arg p_filter "$PROJECT_FILTER" \
  --arg t_filter "$TEMPLATE_FILTER" '
  (.agents // .) |
  [ .[] |
    select(
      ($a_target != "" and (.id == $a_target or .slug == $a_target or .name == $a_target)) or
      ($a_target == "" and
        ($p_filter == "" or .projectId == $p_filter or .groveId == $p_filter or .project == $p_filter) and
        ($t_filter == "" or .template == $t_filter)
      )
    ) |
    {
      id: .id,
      name: .name,
      slug: .slug,
      project: .project,
      projectId: (.projectId // .groveId),
      template: (.template // "none"),
      phase: .phase,
      currentModel: (.appliedConfig.model // "(unset)"),
      harness: (.appliedConfig.harnessConfig // .harness // "unknown")
    }
  ]
')

COUNT=$(echo "$MATCHES" | jq 'length')
if [[ "$COUNT" -eq 0 ]]; then
  echo "No agents found matching the specified criteria."
  exit 0
fi

if [[ "$DRY_RUN" == "true" ]]; then
  if [[ "$OUTPUT_JSON" == "true" ]]; then
    jq -n --arg new "$NEW_MODEL" --argjson restart "$RESTART_CONTAINERS" --argjson matches "$MATCHES" \
      '{dryRun: true, proposedModel: $new, restartContainers: $restart, targetCount: ($matches | length), targets: $matches}'
  else
    echo "=== DRY RUN: Found $COUNT matching agent(s) to switch to model '$NEW_MODEL' (restartContainers=$RESTART_CONTAINERS) ==="
    echo "$MATCHES" | jq -r --arg new "$NEW_MODEL" '
      .[] |
      "  * [\(.name)] (\(.id)) in project \(.project) [phase: \(.phase)]\n" +
      "      Template: \(.template) | Harness: \(.harness)\n" +
      "      Current Model: \(.currentModel)  -->  Target Model: \($new)\n"
    '
    echo "Dry run complete. No changes were applied."
  fi
  exit 0
fi

RESULTS="[]"
for row in $(echo "$MATCHES" | jq -r '.[] | @base64'); do
  _decode() {
    echo "$row" | base64 --decode | jq -r "$1"
  }
  AID=$(_decode '.id')
  ANAME=$(_decode '.name')
  APHASE=$(_decode '.phase')
  AHARNESS=$(_decode '.harness')
  ACURR=$(_decode '.currentModel')

  METHOD_USED=""
  HTTP_CODE=0

  if [[ "$APHASE" == "created" ]]; then
    METHOD_USED="patch_config"
    HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" -X PATCH "${API_BASE}/api/v1/agents/${AID}" \
      -H "Authorization: Bearer $TOKEN" \
      -H "Content-Type: application/json" \
      -d "{\"config\": {\"model\": \"${NEW_MODEL}\"}}")
  else
    if [[ "$RESTART_CONTAINERS" == "true" ]]; then
      curl -s -o /dev/null -X POST "${API_BASE}/api/v1/agents/${AID}/stop" \
        -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" -d '{}'
      sleep 1
      curl -s -o /dev/null -X POST "${API_BASE}/api/v1/agents/${AID}/start" \
        -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" -d '{}'
      sleep 4
    fi

    if [[ "$AHARNESS" == "claude" ]]; then
      METHOD_USED="live_slash_model"
      [[ "$RESTART_CONTAINERS" == "true" ]] && METHOD_USED="restart_and_live_slash_model"
      HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" -X POST "${API_BASE}/api/v1/agents/${AID}/message" \
        -H "Authorization: Bearer $TOKEN" \
        -H "Content-Type: application/json" \
        -d "{\"structured_message\": {\"msg\": \"/model ${NEW_MODEL}\", \"raw\": true}}")
      sleep 1
      curl -s -o /dev/null -X POST "${API_BASE}/api/v1/agents/${AID}/message" \
        -H "Authorization: Bearer $TOKEN" \
        -H "Content-Type: application/json" \
        -d '{"structured_message": {"msg": "Enter", "raw": true}}'
    else
      METHOD_USED="restart_only"
      HTTP_CODE=200
    fi
  fi

  SUCCESS=false
  if [[ "$HTTP_CODE" -ge 200 && "$HTTP_CODE" -lt 300 ]]; then
    SUCCESS=true
    if [[ "$OUTPUT_JSON" != "true" ]]; then
      echo "✓ Updated $ANAME ($AID) via $METHOD_USED: $ACURR -> $NEW_MODEL"
    fi
  else
    if [[ "$OUTPUT_JSON" != "true" ]]; then
      echo "✗ Failed to update $ANAME ($AID) via $METHOD_USED — HTTP $HTTP_CODE" >&2
    fi
  fi

  RESULTS=$(echo "$RESULTS" | jq \
    --arg id "$AID" \
    --arg name "$ANAME" \
    --arg prev "$ACURR" \
    --arg new "$NEW_MODEL" \
    --arg method "$METHOD_USED" \
    --argjson code "$HTTP_CODE" \
    --argjson ok "$SUCCESS" \
    '. + [{id: $id, name: $name, previousModel: $prev, newModel: $new, method: $method, statusCode: $code, success: $ok}]')
done

if [[ "$OUTPUT_JSON" == "true" ]]; then
  echo "$RESULTS" | jq .
fi
