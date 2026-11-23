# Threat Model & Checklist: Gemini CLI in GitHub Actions

## Assets and actors

| Asset | Why it matters |
|---|---|
| `GITHUB_TOKEN` / GitHub App token in the agent job | Comment, label, close, open PRs as the project bot (phishing / social engineering) |
| GCP access token / OIDC request token (`id-token: write`) | Cloud API access for the job's lifetime; OIDC request token mints new tokens until the job ends |
| `gha-creds-*.json` in the workspace | Readable by any file-reading tool (even an allowlisted `cat`) |
| Repository secrets passed to the job | Reachable by code running on that runner |

| Actor | Capability |
|---|---|
| Any GitHub user | Open/reopen issues, comment (comments gated separately), open fork PRs |
| First-time contributor | Same, plus PR workflows that require approval |
| OWNER/MEMBER/COLLABORATOR | Trusted commands, but may relay untrusted text (their comment on an outsider's issue) |

## Checklist (scanner IDs in brackets)

### A. Reach and routing
- [G1] Every path from an untrusted-reachable event (`issues`, `issue_comment`, `pull_request_target`, review events) to a privileged job has an `author_association` check on the *same branch* of the condition.
- Command parser: new-issue / new-PR classification comes first; `@gemini-cli` prefixes only count for trusted authors. Test the matrix, not the happy path.
- Reusable workflows (`workflow_call`) inherit the caller's trigger; review callers, not just callees.
- Prefer `pull_request` over `pull_request_target`; never check out and run PR code under `pull_request_target`.

### B. Capability inside the agent
- [G2] Allowlist uses `"tools": {"core": [...]}`. The flat `"coreTools"`, `"excludeTools"`, `"allowedTools"` keys are legacy and may not be enforced; confirm per CLI version.
- [G3] An allowlist exists at all (otherwise shell tools are available under `--yolo`).
- [G13] MCP servers: with a non-empty `tools.core`, MCP tools are denied unless listed as `mcp_<server>_<tool>` (e.g. `mcp_github_add_issue_comment`); the run still "succeeds" but cannot act. Keep `includeTools` and the `mcp_<server>_*` core entries identical, list only the tools the job needs (no delete/push/fork for an agent that only plans), and pin the server image to a version tag or digest, since upstream renames tools between releases and an `includeTools` name that no longer exists silently hides that tool.
- [G4] `"experimental": {"enableAgents": false}`; subagents (e.g. a generalist) have their own tool surface and the main agent's shell allowlist is not a guarantee about them.
- Exclude `web_fetch` and `google_web_search` unless needed; keep shell to `echo` (or `printenv` for env-var-based prompts).
- Triage that reads issue text from environment variables needs `printenv`/`echo` only, `GITHUB_TOKEN: ''`, `issues: read`, and label validation against an allowlist downstream.
- MCP GitHub server `includeTools`: remove write tools the workflow doesn't use (`delete_file`, `fork_repository`, `push_files`).

### C. Credentials
- [G6] `id-token: write` only on jobs that need cloud access; separate service accounts per workflow where possible; WIF attribute conditions on repository and `job_workflow_ref`. Do not block `issues` events globally if triage legitimately runs on them.
- Audit service account roles, keys and Cloud Audit Logs after any suspected exposure; remember the access token (default lifetime about 1 hour) can outlive the job.
- Understand the auth mode: if no `GEMINI_API_KEY` secret exists, model access is via Vertex + WIF and removing WIF means adding a new secret.

### D. Human gate
- [G9] Credentialed job runs in a GitHub Environment with **required reviewers**; consider restricting deployment branches. Prompt-level "wait for /approve" is advisory only.
- Decide `prevent_self_review` and `can_admins_bypass` deliberately.

### E. Input handling
- [G8] Never interpolate `${{ github.event.*.body|title }}` into `run:` scripts; pass via `env:` and read as shell variables.
- Treat issue text as data in the prompt, and still assume injection succeeds; capability and credential limits are the real defence.

### F. Drift and hygiene
- [G5] `gemini_cli_version` pinned (`vars.X || 'x.y.z'`, never bare `vars.X` which falls back to `latest`).
- [G11] Actions pinned to full commit SHAs.
- [G7] WIF login using the default token format yields a cloud-platform-scoped access token; keep the service account least-privilege and add provider attribute conditions.
- [G12] Never check out the PR head or merge ref under `pull_request_target` (it runs attacker code and `.gemini/` config with base-repo credentials).
- [G6] Also set explicit `permissions:` on every workflow; omitted permissions may default to write.
- [G10] `GEMINI_CLI_TRUST_WORKSPACE`: `true` makes the CLI load `.gemini` settings and context files from the workspace; do not combine with a checkout of untrusted code. `false` in headless mode may make the CLI exit 1 (as of the versions reviewed; test yours).

## Fix snippets

Dispatch routing (pseudo-code sketch, trusted-only commands):

```js
const trusted = Boolean(inputCommand) ||
  ['OWNER', 'MEMBER', 'COLLABORATOR'].includes(association);
core.setOutput('trusted', String(trusted));
if (eventType === 'pull_request.opened') { /* review: only safe if the caller restricts to non-fork PRs; otherwise a privileged job reads an untrusted diff */ }
else if (!trusted) { /* issues.opened/reopened -> triage; else fallthrough */ }
else if (request.startsWith('@gemini-cli /review')) { /* review */ }
// ... trusted-only command handling ...
```

```yaml
invoke:
  needs: dispatch
  if: ${{ needs.dispatch.outputs.command == 'invoke' && needs.dispatch.outputs.trusted == 'true' }}
```

Settings:

```json
{
  "experimental": { "enableAgents": false },
  "tools": {
    "core": ["run_shell_command(echo)"],
    "exclude": ["web_fetch", "google_web_search"]
  }
}
```

Credentialed job:

```yaml
jobs:
  invoke:
    environment: gemini-invoke   # add required reviewers in repo settings
```
