# Case Study: Ungated Issue Trigger Drove a Privileged Gemini Agent

Anonymized account of a real remediation. Identifiers, accounts, dates and infrastructure names are intentionally omitted.

## What happened

A repository copied the `run-gemini-cli` dispatch/invoke/review/triage workflows. Two local deviations from the upstream template combined:

1. The dispatch job's `if:` had an `issues: opened/reopened` branch with no author check (so outside issues could be triaged), while the comment path was correctly limited to OWNER/MEMBER/COLLABORATOR.
2. The command parser matched `@gemini-cli ...` prefixes **before** the "new issue -> triage" default. An outsider's issue body starting with `@gemini-cli` therefore selected the most privileged workflow (`invoke`): `gemini --yolo`, a Workload Identity Federation login with a `cloud-platform` access token, `id-token: write`, and issue/PR write.

An outside account opened issues with a generic task title, and the runs succeeded with the privileged job. The agent's own comments showed a subagent using network and scripting tools that were not on the allowlist. The issue bodies were edited afterwards, so preserve edit history early.

## What made it worse (found during remediation)

- The shell allowlist used the flat `coreTools` key, which appeared not to be enforced by the CLI version in use (observed behaviour plus inspection of that version; verify for yours, see the verification reference). The allowlists were likely ineffective in every Gemini workflow in the repo.
- Subagents were enabled, and the "wait for `/approve`" step existed only in the prompt.
- The CLI was unpinned (`latest`), so in the observed upgrade a newer release changed trust behaviour and broke a scheduled triage job that had been skipped on every run until the first issue needed triage.
- No API-key secrets existed; model access was only via WIF, so removing cloud credentials from the job needed a new secret.

## Fix, in layers

1. **Routing**: compute `trusted` from `author_association` (or manual dispatch); untrusted issue authors can only reach triage; `invoke` additionally gated on `trusted == 'true'`. Verified with a routing matrix: no unsafe routes on the fix, and a non-zero UNSAFE count on the old workflow (negative control).
2. **Capability**: nested `tools.core` allowlists, `enableAgents: false`, web tools excluded, invoke shell reduced to `echo`.
3. **Human gate**: `environment: <agent-env>` with required reviewers.
4. **Drift**: pinned CLI version everywhere; trust-workspace set deliberately.
5. **Cloud identity** (owner action): audit the service account's activity and roles since the first exploit run; reduce to least privilege; add WIF attribute conditions.
6. **Disclosure**: handled by the security team; a temporary `gh workflow disable` of the dispatch workflow bridged the gap until the fix merged.

## Lessons

- Review the whole chain: caller trigger -> routing script -> reusable workflow -> credentials. No single file looked dangerous.
- Test negative controls: run your regression test against the old workflow and confirm it fails.
- A skipped step is not a passing step. Canary every agent step on real input after changes: once the allowlists became enforced, a scheduled job with an empty allowlist failed with an API 400, but only when it had work, so it stayed green on every earlier run.
- Capability and credential limits, not prompt wording, are the defence once injection succeeds.
- Tightening the built-in tool allowlist also tightens MCP tools: after an enforced `tools.core`, two agent runs "succeeded" without posting anything because the MCP tools were not listed (`mcp_<server>_<tool>`), and the unpinned MCP image had renamed several tools. Canary on a visible side effect, and pin the MCP server image.
