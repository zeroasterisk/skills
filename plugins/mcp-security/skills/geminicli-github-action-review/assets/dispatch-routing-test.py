#!/usr/bin/env python3
"""Routing regression test for a Gemini CLI dispatch workflow (template).

Extracts the github-script step that parses `@gemini-cli ...` commands out of event
text, runs it under Node with a matrix of events x author associations x bodies, and
checks that an untrusted author can never select a privileged command.

Usage:
  dispatch-routing-test.py [path/to/gemini-dispatch.yml]

Verdict (exit status):
  0  no UNSAFE routes and no unexpected routes
  1  at least one UNSAFE route (untrusted author -> privileged command) or mismatch
  2  tooling/config error (node missing, step not found, script crashed)

Adapt the CONFIG block to your workflow. Run it on the FIXED workflow (expect 0) and on
the OLD workflow: the UNSAFE count there is the negative control that proves the test can
detect the flaw. The `trusted` output is only compared when the script emits one.
Requires Node.js and PyYAML.
"""
import json
import os
import subprocess
import sys
import tempfile

try:
    import yaml
except ImportError:
    print("PyYAML is required: python3 -m pip install pyyaml", file=sys.stderr)
    sys.exit(2)

# ---- CONFIG: adapt to your workflow -------------------------------------------
WORKFLOW = sys.argv[1] if len(sys.argv) > 1 else ".github/workflows/gemini-dispatch.yml"
JOB = "dispatch"                 # job holding the command-parsing step
STEP_ID = "extract_command"      # id of the actions/github-script step
PREFIX = "@gemini-cli"           # command prefix users type
PRIVILEGED = {"invoke", "review"}  # commands an untrusted author must never get from TEXT
TRUSTED_ASSOCS = {"COLLABORATOR", "MEMBER", "OWNER"}
UNTRUSTED_ASSOCS = ["NONE", "FIRST_TIME_CONTRIBUTOR", "FIRST_TIMER", "CONTRIBUTOR", "MANNEQUIN"]
# Env vars the script reads (as in the upstream run-gemini-cli dispatch example):
#   REQUEST (event text), EVENT_TYPE ("<event>.<action>"), AUTHOR_ASSOCIATION,
#   INPUT_COMMAND / INPUT_CONTEXT (workflow_dispatch inputs).
# Outputs checked: `command` (invoke|review|triage|fallthrough) and, if emitted, `trusted`.
ISSUE_EVENTS = ["issues.opened", "issues.reopened"]
COMMENT_EVENTS = ["issue_comment.created", "pull_request_review.submitted"]
# Is an automatic review of ANY newly opened PR intended? In the upstream template
# pull_request.opened routes straight to `review` regardless of author, so a privileged
# job reads an untrusted diff. Set False if your dispatch job does not restrict PRs
# (e.g. to non-fork PRs) and you want this flagged.
PR_OPENED_REVIEW_FOR_ANYONE_INTENDED = True
BODIES = [
    f"{PREFIX} do bad", f"{PREFIX} /review", f"{PREFIX} /triage", "plain text",
    f" {PREFIX} leading space", f"\n{PREFIX} leading newline", PREFIX.upper() + " upper",
    f"{PREFIX}/review", f"hello {PREFIX} in the middle",
]
# ---------------------------------------------------------------------------------

NODE_RUNNER = r"""
const script = JSON.parse(process.argv[2]);
const cases = JSON.parse(process.argv[3]);
const noop = new Proxy({}, { get: () => () => {} });
(async () => {
  const results = [];
  for (const env of cases) {
    const out = {};
    const core = new Proxy({ setOutput: (k, v) => { out[k] = v; } },
      { get: (t, p) => (p in t ? t[p] : () => {}) });
    const context = { eventName: (env.EVENT_TYPE || '').split('.')[0], payload: {} };
    Object.assign(process.env,
      { INPUT_COMMAND: '', INPUT_CONTEXT: '', AUTHOR_ASSOCIATION: '', REQUEST: '', EVENT_TYPE: '' }, env);
    try {
      await (new Function('core', 'process', 'require', 'context', 'github',
        'return (async()=>{' + script + '})()'))(core, process, require, context, noop);
    } catch (e) { out.error = String(e); }
    results.push(out);
  }
  console.log(JSON.stringify(results));
})();
"""


def expected(ev, assoc, body):
    """Return the command the routing script must produce (None = don't care)."""
    if assoc not in TRUSTED_ASSOCS:
        return "triage" if ev in ISSUE_EVENTS else "fallthrough"
    if body.startswith(f"{PREFIX} /review"):
        return "review"
    if body.startswith(f"{PREFIX} /triage"):
        return "triage"
    if body.startswith(PREFIX):
        return "invoke"
    return "triage" if ev in ISSUE_EVENTS else "fallthrough"


def main():
    try:
        with open(WORKFLOW, encoding="utf-8") as f:
            wf = yaml.safe_load(f)
        steps = wf["jobs"][JOB]["steps"]
        script = next(s for s in steps if s.get("id") == STEP_ID)["with"]["script"]
    except (OSError, KeyError, StopIteration, TypeError) as e:
        print(f"cannot find step '{STEP_ID}' in job '{JOB}' of {WORKFLOW}: {e!r}; edit the CONFIG block", file=sys.stderr)
        return 2

    cases = []
    for ev in ISSUE_EVENTS + COMMENT_EVENTS:
        for assoc in UNTRUSTED_ASSOCS + sorted(TRUSTED_ASSOCS):
            for body in BODIES:
                cases.append({"EVENT_TYPE": ev, "AUTHOR_ASSOCIATION": assoc, "REQUEST": body})
    # PR-opened: expectation is config-driven (see PR_OPENED_REVIEW_FOR_ANYONE_INTENDED).
    for ev in ("pull_request.opened", "pull_request_target.opened"):
        for assoc in UNTRUSTED_ASSOCS:
            cases.append({"EVENT_TYPE": ev, "AUTHOR_ASSOCIATION": assoc, "REQUEST": ""})
    cases.append({"EVENT_TYPE": "workflow_dispatch.", "INPUT_COMMAND": "invoke"})

    with tempfile.NamedTemporaryFile("w", suffix=".js", delete=False) as t:
        t.write(NODE_RUNNER)
        runner = t.name
    try:
        out = subprocess.check_output(["node", runner, json.dumps(script), json.dumps(cases)])
    except FileNotFoundError:
        print("node is required to run this test (https://nodejs.org)", file=sys.stderr)
        return 2
    except subprocess.CalledProcessError as e:
        print(f"node runner failed: {e}", file=sys.stderr)
        return 2
    finally:
        os.unlink(runner)
    results = json.loads(out)

    unsafe = mismatches = errors = 0
    for case, got in zip(cases, results):
        ev, assoc, body = case["EVENT_TYPE"], case.get("AUTHOR_ASSOCIATION", ""), case.get("REQUEST", "")
        cmd = got.get("command")
        if "error" in got:
            errors += 1
            print("ERROR", case, got["error"])
            continue
        if ev == "workflow_dispatch.":
            if cmd != "invoke":
                mismatches += 1
                print("MISMATCH", case, "got", got)
            continue
        if ev.startswith("pull_request") and ev.endswith(".opened"):
            if cmd in PRIVILEGED and not PR_OPENED_REVIEW_FOR_ANYONE_INTENDED:
                unsafe += 1
                print("UNSAFE", case, "->", cmd)
            continue
        if assoc not in TRUSTED_ASSOCS and cmd in PRIVILEGED:
            unsafe += 1
            print("UNSAFE", case, "->", cmd)
            continue
        want = expected(ev, assoc, body)
        trusted_ok = "trusted" not in got or got["trusted"] == str(assoc in TRUSTED_ASSOCS).lower()
        if cmd != want or not trusted_ok:
            # A trusted author's malformed prefix (leading space etc.) falling through is safe.
            mismatches += 1
            print("MISMATCH", case, "expected", want, "got", got)

    print(f"{len(cases)} cases: {unsafe} UNSAFE routes, {mismatches} other mismatches, {errors} script errors")
    if errors:
        return 2
    return 1 if (unsafe or mismatches) else 0


if __name__ == "__main__":
    sys.exit(main())
