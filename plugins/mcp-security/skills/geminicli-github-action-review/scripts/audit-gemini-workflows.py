#!/usr/bin/env python3
"""Static review of GitHub Actions workflows that run Gemini CLI (run-gemini-cli).

Heuristic scanner: it reads workflow YAML only. A clean result is NOT proof of safety
(use the routing test and canaries too), and composite actions under .github/actions/
are not scanned.

Exit status: 0 = no HIGH/CRITICAL findings, 1 = at least one, 2 = usage/tooling error
or at least one workflow file could not be parsed (unless --allow-unparsed).
Requires PyYAML (python3 -m pip install pyyaml, or run in a venv).
"""
import argparse
import json
import os
import re
import sys

try:
    import yaml
except ImportError:
    print("PyYAML is required: python3 -m pip install pyyaml", file=sys.stderr)
    sys.exit(2)

ACTION = "google-github-actions/run-gemini-cli"
UNTRUSTED_EVENTS = {"issues", "issue_comment", "pull_request_target", "pull_request_review",
                    "pull_request_review_comment", "discussion", "discussion_comment",
                    "workflow_run"}
LEGACY_KEYS = ("coreTools", "excludeTools", "allowedTools")
SEV_ORDER = {"CRITICAL": 4, "HIGH": 3, "MEDIUM": 2, "LOW": 1, "INFO": 0}
# Mentions only: proves a condition exists, not that its polarity or logic is right.
GATE_RE = re.compile(r"author_association|\btrusted\b", re.I)
FIELDS = r"(body|title|message|head\.(ref|label)|name|email)"
INJECT_RE = re.compile(
    r"\$\{\{[^}]*github\.event\.(issue|comment|review|pull_request|discussion|head_commit|commits)[^}]*?\."
    + FIELDS + r"|\$\{\{[^}]*github\.head_ref")
READ_CMDS = {"cat", "grep", "head", "tail", "less", "more", "find", "ls", "sed", "awk", "tee"}


def load(path):
    with open(path, encoding="utf-8") as f:
        text = f.read()
    try:
        doc = yaml.safe_load(text)
    except yaml.YAMLError as e:
        return None, text, f"YAML parse error: {e}"
    if not isinstance(doc, dict):
        return None, text, "not a mapping"
    return doc, text, None


def triggers(doc):
    on = doc.get("on", doc.get(True))  # PyYAML parses bare `on` as True
    if isinstance(on, str):
        return {on}
    if isinstance(on, list):
        return set(on)
    if isinstance(on, dict):
        return set(on.keys())
    return set()


def gemini_steps(job):
    for step in job.get("steps", []) or []:
        if str(step.get("uses", "")).startswith(ACTION):
            yield step


def parse_settings(step):
    raw = (step.get("with") or {}).get("settings")
    if not raw:
        return None, "no settings block"
    txt = re.sub(r"\$\{\{.*?\}\}", "false", str(raw), flags=re.S)
    try:
        return json.loads(txt), None
    except json.JSONDecodeError as e:
        return None, f"settings JSON not parseable ({e}); G2/G4 and allowlist content checks were skipped"


def job_permissions(doc, job):
    """Return (privileged, known). `write-all` or absent permissions count as privileged."""
    perms = job.get("permissions", doc.get("permissions"))
    if perms is None:
        return True, False
    if isinstance(perms, str):
        return perms == "write-all", True
    if isinstance(perms, dict):
        priv = perms.get("id-token") == "write" or any(
            perms.get(k) == "write" for k in ("issues", "pull-requests", "contents"))
        return priv, True
    return True, False


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0],
                                 epilog="Exit: 0 ok, 1 HIGH/CRITICAL, 2 error/unparsed.")
    ap.add_argument("path", nargs="?", default=".", help="repo root or a workflows directory")
    ap.add_argument("--json", action="store_true", help="machine-readable output")
    ap.add_argument("--allow-unparsed", action="store_true",
                    help="do not exit 2 when a workflow file cannot be parsed")
    args = ap.parse_args()

    root = args.path
    wf_dir = root if root.rstrip("/").endswith("workflows") else os.path.join(root, ".github", "workflows")
    if not os.path.isdir(wf_dir):
        print(f"No workflows directory at {wf_dir}; pass a repo root or a workflows dir", file=sys.stderr)
        return 2

    docs, findings, unparsed = {}, [], 0
    seen = set()

    def add(sev, fid, f, msg):
        key = (sev, fid, f, msg)
        if key not in seen:
            seen.add(key)
            findings.append({"severity": sev, "id": fid, "file": f, "message": msg})

    for name in sorted(os.listdir(wf_dir)):
        if not name.endswith((".yml", ".yaml")):
            continue
        doc, text, err = load(os.path.join(wf_dir, name))
        if err:
            unparsed += 1
            add("HIGH", "PARSE", name, f"{err}; this file was NOT reviewed")
            continue
        docs[name] = (doc, text)

    callers = {n: set() for n in docs}
    for name, (doc, _) in docs.items():
        for job in (doc.get("jobs") or {}).values():
            m = re.match(r"\./\.github/workflows/(.+\.ya?ml)$", str(job.get("uses", "")))
            if m and m.group(1) in callers:
                callers[m.group(1)].add(name)

    def reach_events(name, seen_=None):
        seen_ = seen_ or set()
        if name in seen_:
            return set()
        seen_.add(name)
        ev = triggers(docs[name][0])
        for c in callers.get(name, ()):
            ev |= reach_events(c, seen_)
        return ev

    def chain_text(name, seen_=None):
        seen_ = seen_ or set()
        if name in seen_:
            return ""
        seen_.add(name)
        t = docs[name][1]
        for c in callers.get(name, ()):
            t += chain_text(c, seen_)
        return t

    def gate_text(name, jid):
        """`if:` of the job itself plus `if:` of any job in a caller that invokes this workflow."""
        t = str((docs[name][0].get("jobs") or {}).get(jid, {}).get("if", ""))
        for c in callers.get(name, ()):
            for cjob in (docs[c][0].get("jobs") or {}).values():
                if str(cjob.get("uses", "")).endswith(name):
                    t += " " + str(cjob.get("if", ""))
        return t

    found_any = False
    for name, (doc, text) in docs.items():
        ev = reach_events(name)
        untrusted_reach = sorted(ev & UNTRUSTED_EVENTS)
        for jid, job in (doc.get("jobs") or {}).items():
            # G8: untrusted text interpolated into run: scripts or github-script code (any job).
            for step in job.get("steps", []) or []:
                code = str(step.get("run", "")) + "\n" + str((step.get("with") or {}).get("script", ""))
                if INJECT_RE.search(code):
                    add("HIGH", "G8", f"{name}:{jid}",
                        "untrusted event text interpolated directly into a `run:`/github-script body; pass via `env:` instead")
            # G12: pull_request_target checkout of PR head/merge ref (any job).
            if "pull_request_target" in ev:
                for s2 in job.get("steps", []) or []:
                    ref = str((s2.get("with") or {}).get("ref", ""))
                    if str(s2.get("uses", "")).startswith("actions/checkout") and re.search(r"head|merge|pull/", ref):
                        add("HIGH", "G12", f"{name}:{jid}",
                            "pull_request_target job checks out PR head/merge code: untrusted code and `.gemini/` "
                            "config run with base-repo credentials")

            steps = list(gemini_steps(job))
            if not steps:
                continue
            found_any = True
            loc = f"{name}:{jid}"
            privileged, perms_known = job_permissions(doc, job)
            perms = job.get("permissions", doc.get("permissions"))
            id_token = isinstance(perms, dict) and perms.get("id-token") == "write"
            has_env = bool(job.get("environment"))
            has_assoc = "author_association" in chain_text(name)
            job_gated = bool(GATE_RE.search(gate_text(name, jid)))
            is_triage = bool(re.search(r"triage", jid, re.I))

            if not perms_known:
                add("MEDIUM", "G6", loc,
                    "no explicit `permissions:`; default GITHUB_TOKEN permissions are unknown (may be write). "
                    "Set them explicitly. Treated as privileged for G1")
            if untrusted_reach and privileged and not has_assoc:
                add("CRITICAL", "G1", loc,
                    f"reachable from {untrusted_reach} with write/OIDC permissions and no author_association check anywhere in the call chain")
            elif untrusted_reach and privileged and not job_gated and not is_triage:
                add("HIGH", "G1", loc,
                    f"reachable from {untrusted_reach}; the job `if:` (and its caller's) has no author_association/trusted "
                    "mention, so safety depends on upstream routing logic. Add a `trusted` condition and run the routing test "
                    "(heuristic: a mention is not proof the condition is correct)")
            elif untrusted_reach and not has_assoc:
                add("MEDIUM", "G1", loc,
                    f"reachable from {untrusted_reach} with no author_association check (verify the job is read-only and credential-free)")
            if untrusted_reach and privileged and not has_env:
                add("MEDIUM", "G9", loc,
                    "privileged job reachable from untrusted-capable events has no `environment:` "
                    "(no human approval gate; this scanner cannot verify required reviewers are configured)")
            if id_token:
                add("MEDIUM", "G6", loc,
                    "`id-token: write` on an agent job: cloud credentials (access token, OIDC request token, "
                    "gha-creds file) are exposed to anything the agent runs; scope the service account and prefer a gated environment")

            for step in steps:
                w = step.get("with") or {}
                settings, serr = parse_settings(step)
                if settings is None:
                    add("MEDIUM", "G3", loc, f"cannot verify tool allowlist: {serr}")
                else:
                    legacy = [k for k in LEGACY_KEYS if k in settings]
                    tools = settings.get("tools") if isinstance(settings.get("tools"), dict) else {}
                    if legacy:
                        add("HIGH", "G2", loc,
                            f"legacy flat settings key(s) {legacy}: may not be enforced by the pinned Gemini CLI; "
                            "use tools.core / tools.exclude (verify per version, see references/verifying-cli-settings.md)")
                    core = tools.get("core")
                    if core is None:
                        add("HIGH", "G3", loc, "no `tools.core` allowlist: built-in tools incl. shell may be available under --yolo")
                    elif not core:
                        add("HIGH", "G3", loc,
                            "`tools.core` is empty: with Gemini CLI 0.66.0 this made the model request fail with HTTP 400 "
                            "(`tools[0].tool_type ... must have one initialized field`). Use a minimal non-empty allowlist such as run_shell_command(echo)")
                    else:
                        for entry in map(str, core):
                            e = entry.strip()
                            if e == "*" or e == "run_shell_command":
                                add("HIGH", "G3", loc, f"allowlist entry `{e}` permits unrestricted shell")
                            m = re.match(r"run_shell_command\((.+)\)$", e)
                            if m and m.group(1).split()[0] in READ_CMDS:
                                add("MEDIUM", "G3", loc,
                                    f"allowlist permits `{m.group(1)}`: file-reading commands can read credential files in the workspace/runner")
                    exp = settings.get("experimental") if isinstance(settings.get("experimental"), dict) else {}
                    if exp.get("enableAgents") is not False:
                        add("MEDIUM", "G4", loc,
                            "subagents not disabled (`experimental.enableAgents` != false): subagents may have a tool surface the main allowlist was meant to deny")

                    # G13: MCP servers vs. the tools.core allowlist, plus image pinning.
                    servers = settings.get("mcpServers") if isinstance(settings.get("mcpServers"), dict) else {}
                    core_s = [str(c).strip() for c in (core or [])]
                    for sname, sconf in servers.items():
                        sconf = sconf if isinstance(sconf, dict) else {}
                        inc = sconf.get("includeTools")
                        if not inc:
                            add("MEDIUM", "G13", loc,
                                f"MCP server `{sname}` has no `includeTools`: every tool the server exposes (incl. write/delete tools) is available")
                        elif core_s:
                            wild = {f"mcp_{sname}_*", "mcp_*"}
                            if not wild & set(core_s):
                                missing = [t for t in inc if f"mcp_{sname}_{t}" not in core_s]
                                if missing:
                                    add("HIGH", "G13", loc,
                                        f"MCP tools {missing} are in `includeTools` but not in `tools.core` as `mcp_{sname}_<tool>`: with a non-empty "
                                        "`tools.core` the CLI adds a catch-all deny, so these calls are silently denied (the run still succeeds but "
                                        "cannot post). Verify with a canary")
                        cargs = [str(a) for a in (sconf.get("args") or [])]
                        if sconf.get("command") == "docker" and cargs:
                            image = cargs[-1]
                            last = image.rsplit("/", 1)[-1]
                            if "@sha256:" not in image and (":" not in last or last.endswith(":latest")):
                                add("MEDIUM", "G13", loc,
                                    f"MCP server `{sname}` image `{image}` is unpinned (floating tag): upstream tool renames/changes can break or widen "
                                    "the tool surface; includeTools names that no longer exist silently hide tools. Pin a version tag or digest")

                ver = str(w.get("gemini_cli_version", "")).strip()
                if not ver or ver.lower() in ("latest", "preview", "nightly"):
                    add("MEDIUM", "G5", loc, "gemini_cli_version unset or floating: CLI behaviour can change between runs")
                elif "${{" in ver and not re.search(r"\|\|\s*['\"]v?[0-9]", ver):
                    add("MEDIUM", "G5", loc, "gemini_cli_version comes from a variable with no pinned literal fallback (empty var = latest)")

                if w.get("gcp_workload_identity_provider") and not w.get("gcp_token_format"):
                    add("MEDIUM", "G7", loc,
                        "WIF login with default gcp_token_format (access token, cloud-platform scope): the agent holds a broad token; "
                        "confirm the service account is least-privilege and the provider has attribute conditions")

                env = {**(doc.get("env") or {}), **(job.get("env") or {}), **(step.get("env") or {})}
                trust = str(env.get("GEMINI_CLI_TRUST_WORKSPACE", "")).lower()
                has_checkout = any(str(s.get("uses", "")).startswith("actions/checkout") for s in job.get("steps", []) or [])
                if trust == "true" and has_checkout and untrusted_reach:
                    add("MEDIUM", "G10", loc,
                        "workspace trust enabled together with a checkout on an untrusted-reachable trigger: workspace .gemini settings/context files may be loaded")
                if trust == "false":
                    add("INFO", "G10", loc,
                        "GEMINI_CLI_TRUST_WORKSPACE=false: headless Gemini CLI may exit 1 ('not running in a trusted directory') when it has work; confirm this path is exercised")

            # G11: every `uses:` in a workflow that contains a Gemini job.
            for s2 in job.get("steps", []) or []:
                u = str(s2.get("uses", ""))
                if u and not u.startswith("./") and not re.search(r"@[0-9a-f]{40}\b", u):
                    add("LOW", "G11", loc, f"action not pinned to a full commit SHA: {u}")

    if not found_any:
        add("INFO", "NONE", wf_dir, "no run-gemini-cli usage found")

    findings.sort(key=lambda f: -SEV_ORDER[f["severity"]])
    if args.json:
        print(json.dumps(findings, indent=2))
    else:
        for f in findings:
            print(f"[{f['severity']:<8}] {f['id']:<5} {f['file']}: {f['message']}")
        worst = findings[0]["severity"] if findings else "INFO"
        print(f"\n{len(findings)} finding(s); worst = {worst}; unparsed files = {unparsed}")
    if unparsed and not args.allow_unparsed:
        return 2
    return 1 if any(SEV_ORDER[f["severity"]] >= 3 for f in findings) else 0


if __name__ == "__main__":
    sys.exit(main())
