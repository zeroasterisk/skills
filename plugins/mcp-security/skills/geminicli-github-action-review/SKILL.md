---
name: geminicli-github-action-review
description: Reviews and hardens GitHub Actions workflows that run Gemini CLI via google-github-actions/run-gemini-cli (dispatch/invoke/review/triage patterns) against prompt injection from untrusted issue, comment and PR text, ungated triggers, ineffective tool allowlists, subagent bypass, and over-privileged GCP/GitHub credentials. Use when auditing or writing a gemini-cli workflow, reviewing a fleet of repos that copied the run-gemini-cli templates, responding to a report that an outsider can drive a repo's Gemini agent, or after bumping the Gemini CLI version.
license: Apache-2.0
metadata:
  version: "1.0.0"
---

# Gemini CLI GitHub Action Review

## Overview

`google-github-actions/run-gemini-cli` runs `gemini --yolo` (all tool calls auto-approved; as of the action and CLI versions reviewed) inside a GitHub Actions job. Whatever text reaches the prompt (issue titles/bodies, comments, PR descriptions, file contents) is attacker-controlled unless proven otherwise, and the job usually holds a GitHub write token and often a GCP access token. Reviewing these workflows is therefore a trust-boundary exercise: **who can reach the agent, what can the agent do once reached, and what credentials are lying around when it does.**

This skill packages a repeatable review, a static scanner, a run-history scanner, and a routing regression-test template, distilled from a real remediation (see the case study).

**Prerequisites:** python3 with PyYAML, `gh` (authenticated) and `jq`, and Node.js for the routing test.

## Bundled Resources

- `scripts/audit-gemini-workflows.py` — Static scanner. Point it at a repo (or a workflows directory); it reports findings G1–G13, indexed in the checklist. Exit 1 on HIGH/CRITICAL, 2 on unparsed files; `--json` for machines. It is a heuristic (a `trusted` mention in a job `if:` is not proof the condition is right) and never replaces the routing test.
- `scripts/scan-run-history.sh` — Read-only `gh` sweep of past runs: finds privileged Gemini jobs (invoke/review) that succeeded for event types outsiders can trigger, and shows the triggering account's repo permission. Use to answer "has this already been exploited?". It only covers the most recent `LIMIT` runs, makes a few API calls per run, and exits 2 if any lookup failed (incomplete result).
- `assets/dispatch-routing-test.py` — Template harness that extracts a dispatch workflow's command-routing script and asserts a matrix of events x author associations x bodies. Adapt the CONFIG block; always run it against the *old* workflow as a negative control.
- [Threat Model & Checklist](references/threat-model-and-checklist.md) (`references/threat-model-and-checklist.md`) — The full review checklist with rationale and fix snippets.
- [Verifying Gemini CLI Settings](references/verifying-cli-settings.md) (`references/verifying-cli-settings.md`) — How to prove which settings keys a given CLI version actually reads (the flat `coreTools` trap).
- [Case Study](references/case-study.md) (`references/case-study.md`) — Anonymized account of an exploited dispatch routing flaw and the layered fix.

## Workflow

### Step 1: Inventory

```bash
./scripts/audit-gemini-workflows.py /path/to/repo
```

List every workflow that uses `run-gemini-cli` and every workflow that calls it via `uses: ./.github/workflows/...`. The *triggers of the caller* decide who can reach the agent.

### Step 2: Walk the trust chain (the order matters)

1. **Reach** — Which events can start it? `issues` (opened/reopened), `issue_comment`, `pull_request_review*`, and `pull_request_target` are reachable by any GitHub user unless gated. A gate on the comment path does not cover a separate `issues` branch.
2. **Routing** — If a script parses `@gemini-cli ...` commands out of event text, the parse order and the author check must make it impossible for an untrusted author to select a privileged command. Classify new issues/PRs *before* honouring any command prefix, and make the command parser depend on the author check.
3. **Capability** — Check the `settings` JSON: nested `"tools": {"core": [...]}` allowlist, `"experimental": {"enableAgents": false}`, `"tools": {"exclude": [...]}`. The legacy flat `"coreTools"` key was not enforced in the 0.66.0 setup we observed; newer versions may migrate or read legacy keys, so verify behaviourally per version (see references).
4. **Credentials** — `permissions:` (`id-token: write`, issues/PR write), WIF provider + service-account roles, `gha-creds-*.json` written into the workspace, `GOOGLE_CLOUD_ACCESS_TOKEN` in the CLI environment. Untrusted-text jobs (triage) should get `GITHUB_TOKEN: ''` and the narrowest cloud identity.
5. **Human gate** — A prompt that says "wait for /approve" is not a control. Use a GitHub Environment with required reviewers on the job that holds credentials.
6. **Drift** — Pin `gemini_cli_version` and the action by SHA. An unpinned `latest` silently changes settings schema, trust prompts and defaults.

### Step 3: Check whether it was already exploited

```bash
./scripts/scan-run-history.sh OWNER/REPO gemini-dispatch.yml 200
```

Look for successful privileged jobs triggered by accounts with no repo permission. If found: preserve run logs and issue edit history (attackers edit bodies afterwards), assume the cloud identity and any job secrets were exposed, audit that identity's activity since the first run, and coordinate with your security team before public write-ups.

### Step 4: Fix in layers (do not rely on one)

1. Route untrusted issue authors to triage only; gate `invoke`/`review` on a computed `trusted` output (OWNER/MEMBER/COLLABORATOR or manual dispatch).
2. Enforce the allowlist with `tools.core`; disable subagents; exclude web tools; drop `cat`/`grep`/`head`/`tail` from agents that don't need file reads (they can read credential files).
3. Put the credentialed job in an Environment with required reviewers.
4. Reduce the cloud identity (dedicated service account, `roles/aiplatform.user`, WIF attribute conditions on repo and workflow ref).
5. Pin CLI version and action SHA; set `GEMINI_CLI_TRUST_WORKSPACE` deliberately (`true` only where the workspace is empty or trusted; `false` may make headless runs exit 1 in the versions reviewed).

### Step 5: Prove it

- Run the routing harness (needs Node and PyYAML) and expect 0 UNSAFE routes on the fix and a non-zero UNSAFE count on the old workflow (negative control):

```bash
./assets/dispatch-routing-test.py .github/workflows/gemini-dispatch.yml
```
- Re-run `./scripts/audit-gemini-workflows.py` and confirm findings dropped.
- Canary each workflow after merging (triage, review, invoke behind the approval gate): previously-unenforced allowlists become enforced and can break agents that quietly depended on a tool.
- Live negative test: on a test repo or fork (and after telling your security team), have a non-collaborator account open an issue starting with `@gemini-cli`; only triage should run and no privileged job or cloud login should appear.

## Pitfalls

- Fixing the comment gate but not the `issues` branch (or the reverse).
- A maintainer's `@gemini-cli` comment on an outsider's issue still feeds that outsider's text to the agent; capability and credential limits are what protect you there.
- Skipped steps hide breakage: a Gemini step guarded by "has work to do" can be broken for weeks and only fail on the first real input.
- Pushing or merging changes under `.github/workflows/` requires a token with the `workflow` scope; otherwise merge in the web UI.
