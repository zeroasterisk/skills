# Verifying Which Gemini CLI Settings Keys a Version Reads

Gemini CLI has moved from flat settings keys (`coreTools`, `excludeTools`, `allowedTools`) toward a nested schema (for example `tools.core`, `tools.exclude`, `experimental.enableAgents`). A workflow written for one schema can *look* restrictive while enforcing nothing under another version. The exact key names, defaults and migration behaviour are version-specific and were not independently verified for every release: prove behaviour for the version you pin.

## 1. Behavioural test (primary, authoritative)

In a scratch repo or fork, run the workflow's Gemini step with the allowlist you intend to ship, restricted to `echo` only, and a prompt that asks the agent to run something not on the list (for example `ls` or `date`).

- Expected: the log shows the tool call denied or unavailable. If the command runs, the allowlist is **not** being enforced.
- Repeat the test with the workspace-trust setting you ship (`GEMINI_CLI_TRUST_WORKSPACE`). An untrusted workspace can cause the CLI to skip workspace settings entirely, which makes even correctly nested keys ineffective. "Key not read" and "settings skipped for trust reasons" are different failure modes with the same symptom.
- Test subagents separately if you leave them enabled.
- Re-run whenever `gemini_cli_version` changes.

## 2. Read the docs for the target version

Check the configuration reference of the `google-gemini/gemini-cli` repository at the tag matching your pinned version (look for a configuration reference under its `docs/` directory). If a key you use is not documented there, treat it as unknown. Also compare with the settings shape in the `google-github-actions/run-gemini-cli` example workflows at the tag you pin.

## 3. Inspect the published bundle (secondary, supporting evidence only)

```bash
mkdir -p /tmp/gemini-cli-check && cd /tmp/gemini-cli-check
npm pack @google/gemini-cli@<version> --silent
tar xzf google-gemini-cli-*.tgz
```

The bundle is minified into large `package/bundle/*.js` chunks; use a short Python script (not `grep -o` with wide context, which is very slow on these files):

```python
import re, glob
for f in glob.glob("package/bundle/*.js"):
    s = open(f, errors="ignore").read()
    for pat in [r"settings\??\.tools\??\.core", r'["\']coreTools["\']', r"enableAgents"]:
        for m in list(re.finditer(pat, s))[:1]:
            print(f, pat, "::", s[max(0, m.start()-150):m.end()+250].replace("\n", " "))
```

Interpretation is fragile; treat it as a lead to confirm with the behavioural test:

- Code reading `settings.tools?.core` and then denying everything not listed suggests the nested allowlist is enforced.
- A missing quoted `"coreTools"` does **not** prove the flat key is ignored: a migration step may rename it before use, and minifiers rename variables.
- A default of `true` for `enableAgents` suggests subagents are on unless you disable them.

## 4. Confirm live

After merging, canary each workflow once (triage on an issue, review on a PR, invoke behind its approval gate) and read the job log for tool-denied or settings warnings. Never ship an empty allowlist (`"core": []`): with CLI 0.66.0 an enforced empty list made the API request fail with HTTP 400 (`tools[0].tool_type ... must have one initialized field`). It was invisible while the legacy key was ignored. Use a minimal non-empty list such as `run_shell_command(echo)`.

**MCP tools are gated by the same allowlist.** In CLI 0.66.0 each `tools.core` entry becomes an allow rule and a catch-all deny sits just below it, outranking the MCP allow rules. An MCP tool therefore needs its own entry named `mcp_<server>_<tool>`. Without it, the agent job succeeds and silently cannot post comments or reviews. Tool-name drift in the MCP server is a second silent failure: check `includeTools` against the pinned image's tool list (for the GitHub MCP server, `get_issue` became `issue_read`, `get_pull_request*` became `pull_request_read`, and the pending-review tools became `pull_request_review_write`). The only reliable detection is a canary that must produce a visible side effect (a comment, a review).
