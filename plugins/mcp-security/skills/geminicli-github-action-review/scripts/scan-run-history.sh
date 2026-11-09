#!/usr/bin/env bash
# Read-only sweep of past workflow runs: which runs of a Gemini dispatch workflow
# were started by low-trust accounts and had a privileged job (invoke/review) succeed?
#
# Usage: scan-run-history.sh OWNER/REPO [WORKFLOW_FILE] [LIMIT] [JOB_REGEX]
#   WORKFLOW_FILE  default: gemini-dispatch.yml
#   LIMIT          default: 200 (most recent runs inspected; results cover only this window)
#   JOB_REGEX      default: 'invoke|review' (job names considered privileged)
#
# Requires: gh (authenticated; the collaborator-permission lookup needs push access to the
# repo, otherwise it fails and the script exits 2) and jq. Makes only GET requests, about
# 1-3 API calls per outsider-capable run, so keep LIMIT modest to avoid rate limits.
#
# Exit: 0 = nothing suspicious, 1 = privileged success for a low-trust/outside actor,
#       2 = usage/tooling error or some runs could not be inspected (result incomplete).
set -uo pipefail

REPO="${1:-}"
WF="${2:-gemini-dispatch.yml}"
LIMIT="${3:-200}"
JOBRE="${4:-invoke|review}"

if [[ -z "$REPO" || "$REPO" != */* ]]; then
  echo "usage: $0 OWNER/REPO [WORKFLOW_FILE] [LIMIT] [JOB_REGEX]" >&2
  exit 2
fi
for bin in gh jq; do
  command -v "$bin" >/dev/null 2>&1 || { echo "missing dependency: $bin" >&2; exit 2; }
done

tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT
cache="$tmp/perm"; : >"$cache"

if ! gh run list -R "$REPO" --workflow "$WF" --limit "$LIMIT" \
      --json databaseId,event,createdAt >"$tmp/runs.json" 2>"$tmp/err"; then
  echo "gh run list failed: $(cat "$tmp/err")" >&2
  echo "hint: check 'gh auth status' and that $WF exists in $REPO" >&2
  exit 2
fi

# bash 3.2 (macOS) has no associative arrays: permissions are cached in a temp file.
lookup_perm() { # login -> prints permission, "none", or returns 1 on API failure
  local login="$1" p
  p="$(awk -F'\t' -v a="$login" '$1==a {print $2; exit}' "$cache")"
  if [[ -z "$p" ]]; then
    if p="$(gh api "repos/$REPO/collaborators/$login/permission" --jq '.permission' 2>"$tmp/err")"; then
      :
    elif grep -q "404" "$tmp/err"; then
      p="none"   # not a collaborator
    else
      return 1
    fi
    printf '%s\t%s\n' "$login" "$p" >>"$cache"
  fi
  printf '%s' "$p"
}

suspicious=0; checked=0; errors=0

echo "# $REPO $WF: inspecting up to $LIMIT runs (events outsiders can trigger: issues, issue_comment, pull_request_target, pull_request_review*, discussion*)"
printf '%-12s %-24s %-19s %-16s %-16s %-10s %s\n' RUN EVENT CREATED ACTOR TRIGGERING PERMISSION PRIVILEGED_JOBS_SUCCEEDED

while IFS=$'\t' read -r id event created; do
  case "$event" in
    issues|issue_comment|pull_request_target|pull_request_review|pull_request_review_comment|discussion|discussion_comment) ;;
    *) continue ;;
  esac
  checked=$((checked + 1))

  if ! gh run view "$id" -R "$REPO" --json jobs >"$tmp/jobs.json" 2>"$tmp/err"; then
    echo "WARN run $id: could not read jobs: $(head -c 200 "$tmp/err")" >&2; errors=$((errors + 1)); continue
  fi
  jobs="$(jq -r --arg re "$JOBRE" '[.jobs[] | select(.conclusion=="success") | select(.name|test($re;"i")) | .name] | join(",")' "$tmp/jobs.json")"
  [[ -z "$jobs" ]] && continue

  if ! gh api "repos/$REPO/actions/runs/$id" --jq '[.actor.login, .triggering_actor.login] | @tsv' >"$tmp/actors" 2>"$tmp/err"; then
    echo "WARN run $id: could not read actors: $(head -c 200 "$tmp/err")" >&2; errors=$((errors + 1)); continue
  fi
  IFS=$'\t' read -r actor trig <"$tmp/actors"

  verdict=""; permtxt=""
  for who in "$actor" "$trig"; do
    [[ -z "$who" || "$permtxt" == *"$who="* ]] && continue
    if ! p="$(lookup_perm "$who")"; then
      echo "WARN run $id: permission lookup for $who failed: $(head -c 200 "$tmp/err")" >&2
      errors=$((errors + 1)); p="unknown"
    fi
    permtxt="$permtxt$who=$p "
    case "$p" in
      admin|maintain|write) ;;
      read|triage) [[ "$verdict" != "OUTSIDER" ]] && verdict="LOW-TRUST" ;;
      none) verdict="OUTSIDER" ;;
    esac
  done
  flag=""
  case "$verdict" in
    OUTSIDER)  flag="  <-- OUTSIDER"; suspicious=$((suspicious + 1)) ;;
    LOW-TRUST) flag="  <-- LOW-TRUST (read/triage; may still have author_association COLLABORATOR)"; suspicious=$((suspicious + 1)) ;;
  esac
  printf '%-12s %-24s %-19s %-16s %-16s %-10s %s%s\n' "$id" "$event" "${created:0:19}" "$actor" "${trig:-?}" "${permtxt% }" "$jobs" "$flag"
done < <(jq -r '.[] | [.databaseId, .event, .createdAt] | @tsv' "$tmp/runs.json")

echo
echo "# $checked outsider-capable run(s) inspected; $suspicious flagged; $errors lookup error(s)."
if (( errors > 0 )); then
  echo "RESULT INCOMPLETE: $errors run/actor lookup(s) failed; fix access/rate limits and re-run." >&2
  exit 2
fi
if (( suspicious > 0 )); then
  echo "hint: preserve run logs and issue/comment edit history now; audit the cloud identity used by those jobs; involve your security team." >&2
  exit 1
fi
exit 0
