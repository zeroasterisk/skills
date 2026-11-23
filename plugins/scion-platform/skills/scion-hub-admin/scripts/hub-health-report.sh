#!/usr/bin/env bash
# hub-health-report.sh — Comprehensive Hub subsystem and per-project health & metrics reporting
set -euo pipefail

HUB_URL="${SCION_HUB_ENDPOINT:-}"
PROJECT_TARGET=""
ALL_PROJECTS=false
JSON_OUTPUT=false

usage() {
  cat <<EOF
Usage: $(basename "$0") --hub <https://hub.example.com/> [options]

Options:
  --hub <url>               Hub endpoint URL (required or via SCION_HUB_ENDPOINT)
  -p, --project <slug-or-id> Focus health & metrics report on a specific project
  --all-projects            Include detailed agent health for all projects
  --json                    Output raw structured JSON for scripts and agents
  -h, --help                Show this help message

Examples:
  # Overall Hub subsystem health scorecard
  $(basename "$0") --hub https://chinoy.projects.scion-ai.dev/

  # Health and agent metrics for a specific project
  $(basename "$0") --hub https://chinoy.projects.scion-ai.dev/ --project okf-app

  # Full fleet health report across all projects as JSON
  $(basename "$0") --hub https://chinoy.projects.scion-ai.dev/ --all-projects --json
EOF
  exit 1
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --hub)
      HUB_URL="$2"
      shift 2
      ;;
    -p|--project)
      PROJECT_TARGET="$2"
      shift 2
      ;;
    --all-projects)
      ALL_PROJECTS=true
      shift
      ;;
    --json)
      JSON_OUTPUT=true
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

# Authentication Token Resolution
TOKEN="${SCION_HUB_TOKEN:-${TOKEN:-}}"
if [[ -z "$TOKEN" ]]; then
  CREDS_FILE="${HOME}/.scion/credentials.json"
  if [[ -f "$CREDS_FILE" ]]; then
    TOKEN=$(jq -r --arg h "$HUB_URL" '.hubs[$h].accessToken // empty' "$CREDS_FILE")
    if [[ -z "$TOKEN" ]]; then
      TOKEN=$(jq -r '.hubs[]?.accessToken // empty' "$CREDS_FILE" | head -n 1)
    fi
  fi
fi

if [[ -z "$TOKEN" ]]; then
  echo "Error: No valid access token found in ~/.scion/credentials.json or TOKEN env." >&2
  echo "Authenticate first with: scion hub auth login --hub-url $HUB_URL --no-browser" >&2
  exit 1
fi

# Fetch Hub health summary
SUMMARY_JSON=$(curl -s -f -H "Authorization: Bearer $TOKEN" "${API_BASE}/api/v1/admin/health/summary" 2>/dev/null || true)
if [[ -z "$SUMMARY_JSON" ]]; then
  echo "Error: Failed to fetch health summary from ${API_BASE}/api/v1/admin/health/summary" >&2
  exit 1
fi

# Helper functions for color formatting
if [ -t 1 ] && [ "$JSON_OUTPUT" = false ]; then
  BOLD="\033[1m"
  GREEN="\033[32m"
  YELLOW="\033[33m"
  RED="\033[31m"
  CYAN="\033[36m"
  DIM="\033[2m"
  RESET="\033[0m"
else
  BOLD=""
  GREEN=""
  YELLOW=""
  RED=""
  CYAN=""
  DIM=""
  RESET=""
fi

format_status() {
  local status="$1"
  case "$status" in
    healthy|ok|ready|online|running|completed)
      echo -e "${GREEN}${status}${RESET}"
      ;;
    degraded|blocked|thinking|working)
      echo -e "${YELLOW}${status}${RESET}"
      ;;
    unhealthy|error|crashed|stalled)
      echo -e "${RED}${status}${RESET}"
      ;;
    *)
      echo -e "${DIM}${status}${RESET}"
      ;;
  esac
}

# Fetch project metadata if project-level reporting is requested
PROJECTS_JSON=""
if [[ -n "$PROJECT_TARGET" || "$ALL_PROJECTS" = true ]]; then
  PROJECTS_JSON=$(curl -s -f -H "Authorization: Bearer $TOKEN" "${API_BASE}/api/v1/projects" 2>/dev/null || echo '{"projects":[]}')
fi

# If JSON output is requested
if [ "$JSON_OUTPUT" = true ]; then
  if [[ -n "$PROJECT_TARGET" || "$ALL_PROJECTS" = true ]]; then
    # Collect project details
    TARGET_PROJECTS_JSON='[]'
    if [ "$ALL_PROJECTS" = true ]; then
      TARGET_PROJECTS_JSON=$(echo "$PROJECTS_JSON" | jq '.projects // []')
    else
      TARGET_PROJECTS_JSON=$(echo "$PROJECTS_JSON" | jq --arg t "$PROJECT_TARGET" '[.projects[]? | select(.id == $t or .slug == $t or .name == $t)]')
    fi

    # Enrich each target project with agents
    ENRICHED_PROJECTS='[]'
    while read -r p; do
      [ -z "$p" ] && continue
      pid=$(echo "$p" | jq -r '.id')
      agents_res=$(curl -s -f -H "Authorization: Bearer $TOKEN" "${API_BASE}/api/v1/agents?project=${pid}&limit=200" 2>/dev/null || echo '{"agents":[]}')
      agents_list=$(echo "$agents_res" | jq '.agents // []')
      p_with_agents=$(echo "$p" | jq --argjson a "$agents_list" '. + {agents: $a}')
      ENRICHED_PROJECTS=$(echo "$ENRICHED_PROJECTS" | jq --argjson p "$p_with_agents" '. + [$p]')
    done < <(echo "$TARGET_PROJECTS_JSON" | jq -c '.[]')

    echo "$SUMMARY_JSON" | jq --argjson p "$ENRICHED_PROJECTS" '. + {projects_detail: $p}'
  else
    echo "$SUMMARY_JSON"
  fi
  exit 0
fi

# Human-Readable Report
echo -e "${BOLD}══════════════════════════════════════════════════════════════════${RESET}"
echo -e "${BOLD}                     SCION HUB HEALTH & METRICS                   ${RESET}"
echo -e "${BOLD}══════════════════════════════════════════════════════════════════${RESET}"
echo -e "Endpoint: ${CYAN}${HUB_URL}${RESET}"

HUB_STATUS=$(echo "$SUMMARY_JSON" | jq -r '.status // "unknown"')
HUB_VER=$(echo "$SUMMARY_JSON" | jq -r '.hub.version // "unknown"')
HUB_UPTIME=$(echo "$SUMMARY_JSON" | jq -r '.hub.uptime // "unknown"')
CONNECTED_BROKERS=$(echo "$SUMMARY_JSON" | jq -r '.hub.connected_brokers // 0')
ACTIVE_AGENTS=$(echo "$SUMMARY_JSON" | jq -r '.hub.active_agents // 0')
PROJECT_COUNT=$(echo "$SUMMARY_JSON" | jq -r '.hub.projects // 0')

echo -e "Overall Status:      $(format_status "$HUB_STATUS")"
echo -e "Hub Server Version:  ${HUB_VER} ${DIM}(Uptime: ${HUB_UPTIME})${RESET}"
echo -e "Registered Projects: ${BOLD}${PROJECT_COUNT}${RESET}  |  Active Agents: ${BOLD}${ACTIVE_AGENTS}${RESET}  |  Brokers: ${BOLD}${CONNECTED_BROKERS}${RESET}"
echo

# Database Health & Pool Metrics
echo -e "${BOLD}─── Database Subsystem ───────────────────────────────────────────${RESET}"
DB_STATUS=$(echo "$SUMMARY_JSON" | jq -r '.database.status // "unknown"')
POOL_ACTIVE=$(echo "$SUMMARY_JSON" | jq -r '.database.pool_active // 0')
POOL_MAX=$(echo "$SUMMARY_JSON" | jq -r '.database.pool_max // 0')
POOL_IDLE=$(echo "$SUMMARY_JSON" | jq -r '.database.pool_idle // 0')
POOL_WAIT=$(echo "$SUMMARY_JSON" | jq -r '.database.pool_wait_count_total // 0')

echo -e "Status:     $(format_status "$DB_STATUS")"
echo -e "Pool Stats: Active=${BOLD}${POOL_ACTIVE}${RESET} / Max=${BOLD}${POOL_MAX}${RESET}  |  Idle=${POOL_IDLE}  |  Wait Count Total=${POOL_WAIT}"
echo

# Runtime Brokers Health
echo -e "${BOLD}─── Runtime Brokers ──────────────────────────────────────────────${RESET}"
BROKER_COUNT=$(echo "$SUMMARY_JSON" | jq '.brokers | length')
if [ "$BROKER_COUNT" -eq 0 ]; then
  echo -e "${DIM}No runtime brokers registered.${RESET}"
else
  printf "%-24s %-10s %-10s %-11s %-12s %-20s\n" "BROKER" "STATUS" "RUNTIME" "AVAILABLE" "AGENTS(OK/TOT)" "LAST HEARTBEAT"
  echo "────────────────────────────────────────────────────────────────────────────────────────"
  while read -r b; do
    [ -z "$b" ] && continue
    b_name=$(echo "$b" | jq -r '.name')
    b_status=$(echo "$b" | jq -r '.status')
    b_runtime=$(echo "$b" | jq -r '.runtime')
    b_avail=$(echo "$b" | jq -r '.runtime_available')
    b_healthy=$(echo "$b" | jq -r '.agent_healthy // 0')
    b_total=$(echo "$b" | jq -r '.agent_count // 0')
    b_hb=$(echo "$b" | jq -r '.last_heartbeat // "never"')
    
    if [ "$b_hb" != "0001-01-01T00:00:00Z" ] && [ "$b_hb" != "never" ]; then
      b_hb_fmt=$(echo "$b_hb" | cut -d'.' -f1 | tr 'T' ' ')
    else
      b_hb_fmt="never"
    fi

    avail_str="no"
    [ "$b_avail" = "true" ] && avail_str="yes"

    printf "%-24s %-10s %-10s %-11s %-12s %-20s\n" \
      "${b_name:0:23}" "$b_status" "$b_runtime" "$avail_str" "${b_healthy}/${b_total}" "$b_hb_fmt"
  done < <(echo "$SUMMARY_JSON" | jq -c '.brokers[]')
fi
echo

# Fleet Agent Health Summary
echo -e "${BOLD}─── Fleet Agent Health ───────────────────────────────────────────${RESET}"
TOTAL_AGENTS=$(echo "$SUMMARY_JSON" | jq -r '.agents.total // 0')
RUNNING_AGENTS=$(echo "$SUMMARY_JSON" | jq -r '.agents.by_phase.running // 0')
ERROR_AGENTS=$(echo "$SUMMARY_JSON" | jq -r '.agents.by_phase.error // 0')
STALLED_COUNT=$(echo "$SUMMARY_JSON" | jq '.agents.stalled | length')
CRASHED_COUNT=$(echo "$SUMMARY_JSON" | jq '.agents.crashed | length')
ERRORED_COUNT=$(echo "$SUMMARY_JSON" | jq '.agents.errored | length')

echo -e "Total Agents: ${BOLD}${TOTAL_AGENTS}${RESET}  (Running: ${GREEN}${RUNNING_AGENTS}${RESET}, Errors: ${RED}${ERROR_AGENTS}${RESET})"

if [ "$STALLED_COUNT" -gt 0 ]; then
  stalled_names=$(echo "$SUMMARY_JSON" | jq -r '.agents.stalled | join(", ")')
  echo -e "${YELLOW}⚠ Stalled Agents (${STALLED_COUNT}):${RESET} ${stalled_names}"
fi

if [ "$CRASHED_COUNT" -gt 0 ]; then
  crashed_names=$(echo "$SUMMARY_JSON" | jq -r '.agents.crashed | join(", ")')
  echo -e "${RED}✖ Crashed Agents (${CRASHED_COUNT}):${RESET} ${crashed_names}"
fi

if [ "$ERRORED_COUNT" -gt 0 ]; then
  errored_names=$(echo "$SUMMARY_JSON" | jq -r '.agents.errored | join(", ")')
  echo -e "${RED}✖ Errored Agents (${ERRORED_COUNT}):${RESET} ${errored_names}"
fi

DISPATCH_STUCK=$(echo "$SUMMARY_JSON" | jq -r '.dispatch.stuck_messages // 0')
DISPATCH_FAIL1H=$(echo "$SUMMARY_JSON" | jq -r '.dispatch.failed_1h // 0')
if [ "$DISPATCH_STUCK" != "0" ] || [ "$DISPATCH_FAIL1H" != "0" ]; then
  echo -e "${YELLOW}⚠ Dispatch Queue Issues:${RESET} Stuck Messages: ${DISPATCH_STUCK}, Failed (1h): ${DISPATCH_FAIL1H}"
fi
echo

# Per-Project Deep Dive (if requested)
if [[ -n "$PROJECT_TARGET" || "$ALL_PROJECTS" = true ]]; then
  echo -e "${BOLD}══════════════════════════════════════════════════════════════════${RESET}"
  echo -e "${BOLD}                     PROJECT HEALTH & AGENT METRICS               ${RESET}"
  echo -e "${BOLD}══════════════════════════════════════════════════════════════════${RESET}"

  TARGET_PROJECTS='[]'
  if [ "$ALL_PROJECTS" = true ]; then
    TARGET_PROJECTS=$(echo "$PROJECTS_JSON" | jq '.projects // []')
  else
    TARGET_PROJECTS=$(echo "$PROJECTS_JSON" | jq --arg t "$PROJECT_TARGET" '[.projects[]? | select(.id == $t or .slug == $t or .name == $t)]')
  fi

  T_COUNT=$(echo "$TARGET_PROJECTS" | jq 'length')
  if [ "$T_COUNT" -eq 0 ]; then
    echo -e "${RED}Error: Project '$PROJECT_TARGET' not found on Hub.${RESET}"
    exit 1
  fi

  while read -r p; do
    [ -z "$p" ] && continue
    p_name=$(echo "$p" | jq -r '.name')
    p_slug=$(echo "$p" | jq -r '.slug')
    p_id=$(echo "$p" | jq -r '.id')
    
    echo -e "Project: ${BOLD}${p_name}${RESET} ${DIM}(slug: ${p_slug}, id: ${p_id})${RESET}"

    agents_res=$(curl -s -f -H "Authorization: Bearer $TOKEN" "${API_BASE}/api/v1/agents?project=${p_id}&limit=200" 2>/dev/null || echo '{"agents":[]}')
    p_agents_count=$(echo "$agents_res" | jq '.agents | length')
    
    if [ "$p_agents_count" -eq 0 ]; then
      echo -e "  ${DIM}No agents found in this project.${RESET}"
      echo
      continue
    fi

    p_running=$(echo "$agents_res" | jq '[.agents[] | select(.phase == "running")] | length')
    p_error=$(echo "$agents_res" | jq '[.agents[] | select(.phase == "error")] | length')
    p_blocked=$(echo "$agents_res" | jq '[.agents[] | select(.activity == "blocked")] | length')
    p_working=$(echo "$agents_res" | jq '[.agents[] | select(.activity == "working" or .activity == "thinking")] | length')
    p_completed=$(echo "$agents_res" | jq '[.agents[] | select(.activity == "completed")] | length')

    echo -e "  Summary: Total=${BOLD}${p_agents_count}${RESET} | Running=${GREEN}${p_running}${RESET} | Error=${RED}${p_error}${RESET} | Working/Thinking=${YELLOW}${p_working}${RESET} | Blocked=${YELLOW}${p_blocked}${RESET} | Completed=${CYAN}${p_completed}${RESET}"
    echo
    printf "  %-26s %-14s %-10s %-10s %-12s\n" "AGENT" "TEMPLATE" "HARNESS" "PHASE" "ACTIVITY"
    echo "  ─────────────────────────────────────────────────────────────────────────────"
    
    while read -r a; do
      [ -z "$a" ] && continue
      a_name=$(echo "$a" | jq -r '.name // .slug')
      a_template=$(echo "$a" | jq -r '.template // "default"')
      a_harness=$(echo "$a" | jq -r '.harnessConfig // "claude"')
      a_phase=$(echo "$a" | jq -r '.phase // "unknown"')
      a_activity=$(echo "$a" | jq -r '.activity // "-"')

      printf "  %-26s %-14s %-10s %-10s %-12s\n" \
        "${a_name:0:25}" "${a_template:0:13}" "${a_harness:0:9}" "$a_phase" "$a_activity"
    done < <(echo "$agents_res" | jq -c '.agents[]')
    echo
  done < <(echo "$TARGET_PROJECTS" | jq -c '.[]')
fi
