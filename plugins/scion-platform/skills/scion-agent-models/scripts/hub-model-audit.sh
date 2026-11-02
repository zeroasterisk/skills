#!/usr/bin/env bash
# hub-model-audit.sh — Audit Hub env vars, harness configs, project defaults, and effective agent models across Scion Hub
set -euo pipefail

HUB_URL="${SCION_HUB_ENDPOINT:-}"
PROJECT_FILTER=""
TEMPLATE_FILTER=""
OUTPUT_JSON=false

usage() {
  cat <<EOF
Usage: $(basename "$0") --hub <https://hub.example.com/> [options]

Options:
  --hub <url>          Hub endpoint URL (required or via SCION_HUB_ENDPOINT)
  --project <id|slug>  Filter audit to a specific project
  --template <name>    Filter audit to agents using a specific template
  --json               Output audit results in JSON format
  -h, --help           Show this help message

Audits:
  1. Hub-scoped environment variables (ANTHROPIC_MODEL override warning, CLOUD_ML_REGION=global check)
  2. Global harness-config defaults (claude, antigravity, opencode)
  3. Project-level default harness, default model, and default template annotations
  4. Agent applied configuration (configured model, harness config, phase, GCP identity)
EOF
  exit 1
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --hub)
      HUB_URL="$2"
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
  echo "Error: $CREDS_FILE not found. Authenticate first with: scion hub auth login --hub-url $HUB_URL --no-browser" >&2
  exit 1
fi

TOKEN=$(jq -r --arg h "$HUB_URL" --arg h2 "$API_BASE" '.hubs[$h].accessToken // .hubs[$h2].accessToken // empty' "$CREDS_FILE")
if [[ -z "$TOKEN" ]]; then
  echo "Error: No access token for $HUB_URL found in $CREDS_FILE." >&2
  exit 1
fi

HUB_ENV_RAW=$(curl -s -H "Authorization: Bearer $TOKEN" "${API_BASE}/api/v1/env?scope=hub" || echo '{"envVars":[]}')
HARNESS_RAW=$(curl -s -H "Authorization: Bearer $TOKEN" "${API_BASE}/api/v1/harness-configs" || echo '{"harnessConfigs":[]}')
PROJECTS_RAW=$(curl -s -H "Authorization: Bearer $TOKEN" "${API_BASE}/api/v1/projects")
AGENTS_RAW=$(curl -s -H "Authorization: Bearer $TOKEN" "${API_BASE}/api/v1/agents?limit=250")

if ! echo "$PROJECTS_RAW" | jq -e . >/dev/null 2>&1; then
  echo "Error: Failed to fetch projects from $API_BASE. Response was not valid JSON." >&2
  exit 1
fi

AUDIT_JSON=$(jq -n \
  --arg p_filter "$PROJECT_FILTER" \
  --arg t_filter "$TEMPLATE_FILTER" \
  --argjson env_data "$HUB_ENV_RAW" \
  --argjson h_data "$HARNESS_RAW" \
  --argjson p_data "$PROJECTS_RAW" \
  --argjson a_data "$AGENTS_RAW" '
  ($env_data.envVars // []) as $hub_env |
  ($h_data.harnessConfigs // []) as $hcs |
  ($p_data.projects // $p_data) as $projects |
  ($a_data.agents // $a_data) as $agents |
  (reduce $hcs[] as $h ({}; . + {($h.name): ($h.config.model // null)})) as $hc_models |
  ([ $hub_env[] | select(.key == "ANTHROPIC_MODEL") | .value ][0] // null) as $hub_anthropic_model |
  ([ $hub_env[] | select(.key == "CLOUD_ML_REGION") | .value ][0] // null) as $hub_cloud_ml_region |
  {
    hubEnv: {
      anthropicModelOverride: $hub_anthropic_model,
      cloudMlRegion: $hub_cloud_ml_region,
      warnings: (
        (if $hub_anthropic_model != null then ["Hub-scoped ANTHROPIC_MODEL=\($hub_anthropic_model) overrides SCION_MODEL inside all claude containers!"] else [] end) +
        (if $hub_cloud_ml_region != "global" then ["Hub-scoped CLOUD_ML_REGION is \($hub_cloud_ml_region // "unset") (expected \"global\" to avoid regional 429 quota errors)"] else [] end)
      )
    },
    harnessDefaults: $hc_models,
    projects: [ $projects[] |
      select($p_filter == "" or .id == $p_filter or .slug == $p_filter or .name == $p_filter) |
      . as $proj |
      ($proj.id) as $pid |
      ($proj.annotations // {}) as $ann |
      [ $agents[] |
        select((.projectId == $pid or .groveId == $pid) and
               ($t_filter == "" or .template == $t_filter)) |
        .appliedConfig as $ac |
        ($ac.model // null) as $cfg_model |
        ($ac.harnessConfig // .harness // "unknown") as $harness |
        (
          if $hub_anthropic_model != null and $harness == "claude" then
            {effectiveModel: $hub_anthropic_model, source: "hub_env_override"}
          elif $cfg_model != null and $cfg_model != "" then
            {effectiveModel: $cfg_model, source: "explicit"}
          elif ($ann["scion.io/default-model"] // null) != null and $ann["scion.io/default-model"] != "" then
            {effectiveModel: $ann["scion.io/default-model"], source: "project_default"}
          elif ($hc_models[$harness] // null) != null and $hc_models[$harness] != "" then
            {effectiveModel: $hc_models[$harness], source: "harness_config"}
          elif $harness == "claude" then
            {effectiveModel: "opus", source: "harness_default"}
          elif $harness == "opencode" then
            {effectiveModel: "vertexai.gemini-2.5", source: "harness_default"}
          else
            {effectiveModel: "unknown", source: "unresolved"}
          end
        ) as $resolved |
        {
          id: .id,
          name: .name,
          slug: .slug,
          phase: .phase,
          template: (.template // "none"),
          harnessConfig: $harness,
          configuredModel: $cfg_model,
          effectiveModel: $resolved.effectiveModel,
          modelSource: $resolved.source,
          gcpIdentityMode: ($ac.gcpIdentity.metadataMode // "none"),
          gcpServiceAccount: ($ac.gcpIdentity.serviceAccountEmail // "none")
        }
      ] as $proj_agents |
      {
        projectId: $pid,
        name: $proj.name,
        slug: $proj.slug,
        defaultHarnessConfig: ($ann["scion.io/default-harness-config"] // null),
        defaultModel: ($ann["scion.io/default-model"] // null),
        defaultTemplate: ($ann["scion.io/default-template"] // null),
        agentCount: ($proj_agents | length),
        agents: $proj_agents
      }
    ]
  }
')

if [[ "$OUTPUT_JSON" == "true" ]]; then
  echo "$AUDIT_JSON"
  exit 0
fi

echo "================================================================================"
echo "Scion Fleet Model & Region Audit — $API_BASE"
echo "================================================================================"

echo "$AUDIT_JSON" | jq -r '
  "Hub Environment:\n" +
  "  CLOUD_ML_REGION          : \(.hubEnv.cloudMlRegion // "(unset)")\n" +
  "  ANTHROPIC_MODEL Override : \(.hubEnv.anthropicModelOverride // "(none — OK)")\n" +
  (if (.hubEnv.warnings | length) > 0 then
    (.hubEnv.warnings | map("  ⚠️  WARNING: " + .) | join("\n")) + "\n"
   else "" end)
'

TOTAL_PROJECTS=$(echo "$AUDIT_JSON" | jq '.projects | length')
TOTAL_AGENTS=$(echo "$AUDIT_JSON" | jq '[.projects[].agents[]] | length')
echo "Audited $TOTAL_PROJECTS projects ($TOTAL_AGENTS matching agents)"
echo ""

echo "$AUDIT_JSON" | jq -r '
  .projects[] |
  "--------------------------------------------------------------------------------\n" +
  "Project: \(.name) [slug: \(.slug)] (\(.projectId))\n" +
  "  Default Harness: \(.defaultHarnessConfig // "(unset)") | Default Model: \(.defaultModel // "(unset)") | Default Template: \(.defaultTemplate // "(unset)")\n" +
  "  Agents (\(.agentCount)):\n" +
  (
    if .agentCount == 0 then
      "    (no matching agents)\n"
    else
      (
        .agents[] |
        "    * \(.name) [\(.phase)] (template: \(.template), harness: \(.harnessConfig))\n" +
        "      - Effective Model: \(.effectiveModel) (source: \(.modelSource))\n" +
        "      - Configured Model: \(.configuredModel // "(unset)")\n" +
        "      - GCP SA: \(.gcpServiceAccount) [mode: \(.gcpIdentityMode)]\n"
      )
    end
  )
'
