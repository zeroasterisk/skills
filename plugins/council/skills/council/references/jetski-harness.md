# Jetski Harness Recipes for `council`

Concrete execution templates for running isolated 3-delegate council rounds inside Jetski / Antigravity (`agy`), including an optional multi-model roster in `~/.config/council/roster.json`.

---

## 1. Subagent Registration and Multi-Model Roster

### A. Default Single-Tier Subagent (`council-delegate`)

When the `council` plugin is enabled before a conversation starts and no `~/.config/council/roster.json` is configured, `council-delegate` (`plugins/council/agents/council-delegate.md`) is registered as a subagent (`subagent: true`, `mainAgent: false`) on the `pro` tier with a read-only `tools` list (`view_file`, `grep_search`) and shell execution off.

### B. Multi-Model Roster (`~/.config/council/roster.json`)

Request-time `model` values in `invoke_subagent` and `run_workflow` accept only tiers (`inherit`, `flash`, `pro`), and a documented custom agent's `model` frontmatter takes the same tiers. For three distinct models, define one custom agent per seat with whatever per-agent model pinning your harness supports, and list them in a machine-local roster. If the harness cannot pin a model per agent, use the default three `council-delegate` seats and say in the scorecard that all three ran on one tier.

Each seat agent is a documented custom agent (`~/.gemini/config/agents/<type_name>.md` or `<type_name>/agent.md`) with the same read-only `tools` list as `council-delegate` (`view_file`, `grep_search`).

Example machine-local `~/.config/council/roster.json` (kept outside public git repos):

```json
{
  "version": 1,
  "seats": [
    {"label": "<Model 1 Display Name>", "type_name": "council-seat-1"},
    {"label": "<Model 2 Display Name>", "type_name": "council-seat-2"},
    {"label": "<Model 3 Display Name>", "type_name": "council-seat-3"}
  ],
  "fallback": {"label": "<Fallback Model Display Name>", "type_name": "council-seat-fallback"}
}
```

Custom agents are discovered when a conversation starts. An agent added mid-conversation is visible only after a new conversation starts.

> **Why omitting write/command tools matters**: Omitting `replace_file_content` and `run_command` strips mutation capabilities at tool-schema construction time. Three delegates can inspect `Workspace: "inherit"` in parallel with zero risk of mutating working-tree files, git index locks, or build caches, while each delegate's own trajectory lives under `<appDataDir>/brain/<subConvID>/`.

---

## 2. Primary Execution Path: `run_workflow` Parallel Fan-Out (With Roster + Fallback)

When `run_workflow` is available in your tool declarations, prefer it over manual subagent calls:
* Every delegate runs as an isolated, single-use cold-start trajectory (`agent()`).
* The built-in `parallel(items, fn)` cancels the remaining items when one raises, so `run_seat` catches each seat's error and returns it. One failed delegate then cannot cancel the other two, and the fallback retry can run.
* If `~/.config/council/roster.json` is present, the script loads its 3 seats and retries any failed primary seat once on `fallback`.
* Ordering `findings` *before* `score` in the `finish` JSON Schema enforces findings-first adversarial grading.

### Preparing the Context Snapshot

Write any diff, RFC/design draft, or problem statement to your conversation's scratch directory (`<appDataDir>/brain/<conversation-id>/scratch/council-round-<N>-context.md`), **never** inside the repository working tree. Keep the snapshot strictly factual:
* User request / ticket goal
* Target files or full current draft / diff
* Exact test/lint/typecheck/anchor checks already run and their pass/fail output
* **Omit** author justifications, prior round scores, or prior delegate arguments (and do **not** state the user's target score bar such as `9/10` or `9.5/10`).

### `run_workflow` Script Template

Call `run_workflow` with `Description="Council review (Round <N>)"` and `Args={"context_path": "<abs-path-to-context-md>", "is_scored_review": true, "round": 1}`:

```python
import json
from pathlib import Path

ctx_path = args["context_path"]
is_review = bool(args.get("is_scored_review", True))
round_num = int(args.get("round", 1))

roster_path = Path.home() / ".config" / "council" / "roster.json"
fallback_seat = None
if args.get("seats"):
    seats = args["seats"]
elif roster_path.is_file():
    roster = json.loads(roster_path.read_text(encoding="utf-8"))
    seats = roster["seats"]
    fallback_seat = roster.get("fallback")
else:
    seats = [
        {"label": "Delegate 1 (pro)", "type_name": "council-delegate", "model": "pro"},
        {"label": "Delegate 2 (pro)", "type_name": "council-delegate", "model": "pro"},
        {"label": "Delegate 3 (pro)", "type_name": "council-delegate", "model": "pro"},
    ]

READ_ONLY_TOOLS = {"view_file", "grep_search"}
AGENTS_DIR = Path.home() / ".gemini" / "config" / "agents"


def seat_tools(seat):
    """The seat's declared tools, or None when no Markdown agent file is found."""
    for f in (AGENTS_DIR / f"{seat['type_name']}.md", AGENTS_DIR / seat["type_name"] / "agent.md"):
        if f.is_file():
            fm = f.read_text(encoding="utf-8").split("---", 2)[1]
            return [ln.strip()[2:].strip() for ln in fm.splitlines() if ln.strip().startswith("- ")]
    return None


def vet(seat, idx):
    if seat["type_name"] == "council-delegate":
        return seat
    tools = seat_tools(seat)
    if tools is None:
        log(f"{seat['type_name']}: no Markdown agent file found; tools unverified")
        return {**seat, "label": f"{seat['label']}, tools unverified"}
    if not tools or not set(tools) <= READ_ONLY_TOOLS:
        log(f"{seat['type_name']}: tools {tools} are not read-only; using council-delegate")
        return {"label": f"Delegate {idx + 1} (pro)", "type_name": "council-delegate", "model": "pro"}
    return seat


seats = [vet(s, i) for i, s in enumerate(seats)]
if fallback_seat and fallback_seat["type_name"] != "council-delegate":
    tools = seat_tools(fallback_seat)
    if tools is not None and (not tools or not set(tools) <= READ_ONLY_TOOLS):
        fallback_seat = None

scoring_block = (
    """Scoring rubric (findings-first):
1. First enumerate every concrete in-scope defect in `findings` with severity:
   - `blocker` (-2.0 points): broken correctness, security hole, contradiction, or missing core requirement.
   - `major` (-1.0 point): significant ambiguity, missing boundary/failure handling, or unclear architecture.
   - `minor` (-0.5 point): localized wording, edge-case clarity, or polish issue.
2. For each finding, set `encode` to the lint rule, type, or test that would catch this class of defect mechanically, or `none` if it needs judgment.
3. Compute `score` out of 10 (integer or half-point, e.g. '8.5/10') starting from 10.0 minus your findings deductions. Do not inflate scores or rubber-stamp 10/10 when real flaws exist.
4. Set `satisfied` to true ONLY if no blocker or major issues remain and the work is ready to ship."""
    if is_review
    else "Set `score` to 'no score' (this request is exploratory/non-scored)."
)

prompt = f"""Independent cold-start Council evaluation (Round {round_num}).

Read the request and target artifacts at: {ctx_path}
Inspect any referenced files directly with `view_file` to verify claims, boundaries, and edge cases.

{scoring_block}
Keep recommendations strictly within the requested scope; do not penalize for out-of-scope feature ideas."""

# NOTE: Gemini's genai.Schema requires scalar `type` strings (e.g. `"string"`).
# Never use JSON Schema union arrays like `["string", "null"]`.
# Keep `findings` BEFORE `score` so structured decoding enumerates defects before scoring.
schema = {
    "type": "object",
    "required": ["findings", "score", "satisfied", "summary", "recommendations"],
    "properties": {
        "findings": {
            "type": "array",
            "items": {
                "type": "object",
                "required": ["severity", "title", "detail", "encode"],
                "properties": {
                    "severity": {"type": "string", "enum": ["blocker", "major", "minor"]},
                    "location": {"type": "string"},
                    "title": {"type": "string"},
                    "detail": {"type": "string"},
                    "encode": {"type": "string", "description": "Lint rule, type, or test that would catch this defect class mechanically, or 'none'."}
                }
            }
        },
        "score": {
            "type": "string",
            "description": "Score formatted as '<N>/10' (e.g. '8.5/10'), or 'no score' when unscored."
        },
        "satisfied": {
            "type": "boolean",
            "description": "True if ready to ship without another review round."
        },
        "summary": {
            "type": "string",
            "description": "2-3 sentence overall assessment."
        },
        "recommendations": {
            "type": "array",
            "items": {"type": "string"}
        }
    }
}

def spawn_seat(seat, role_prefix="Council"):
    kwargs = {
        "prompt": prompt,
        "schema": schema,
        "role": f"{role_prefix} · {seat['label']} (R{round_num})",
        "type_name": seat["type_name"],
        "workspace": "inherit",
    }
    if seat.get("model"):
        kwargs["model"] = seat["model"]
    return agent(**kwargs)

async def run_seat(seat):
    # parallel() cancels the other items when one raises, so catch per seat.
    try:
        return await spawn_seat(seat)
    except Exception as err:
        return err

phase(f"Round {round_num}: Parallel Council")
results = await parallel(seats, run_seat)

output = []
for idx, (seat, res) in enumerate(zip(seats, results)):
    # A roster label is the intended model; the harness does not report which model ran.
    used_label = f'{seat["type_name"]} ({seat.get("model", "inherit")}; intended: {seat["label"]})'
    if isinstance(res, Exception) and fallback_seat and seat["type_name"] != fallback_seat["type_name"]:
        log(f"{used_label} failed ({res}); retrying on fallback {fallback_seat['label']}")
        try:
            res = await spawn_seat(fallback_seat, role_prefix=f"Council Fallback S{idx+1}")
            used_label = f"{fallback_seat['type_name']} (fallback for {seat['type_name']}; intended: {fallback_seat['label']})"
        except Exception as fb_err:
            res = fb_err

    if isinstance(res, Exception):
        log(f"{used_label}: ERROR ({res})")
        output.append({"delegate": used_label, "error": str(res), "score": "no score", "satisfied": False, "findings": []})
    else:
        score_str = res.get("score") or "no score"
        log(f"{used_label}: {score_str} (satisfied={res.get('satisfied')}, findings={len(res.get('findings', []))})")
        output.append({"delegate": used_label, **res, "score": score_str})

print(json.dumps(output, indent=2))
```

---

## 3. Fallback Execution Path: Parallel `invoke_subagent`

If `run_workflow` is unavailable:

1. Issue **three `invoke_subagent` calls in the same assistant turn** using the `type_name` values from `~/.config/council/roster.json` (with `Model: "inherit"`, which runs the parent conversation's model unless the harness pins one per agent), or `TypeName: "council-delegate"` with `Model: "pro"` if no `roster.json` exists.
2. **Stop calling tools** at the end of that turn. Jetski wakes your conversation reactively as each subagent sends its completion message; never sleep or poll in a loop.
3. For Round 2+, always launch three fresh subagents rather than calling `send_message` on Round 1's `conversationId`s, so Round 2 evaluates the updated work from a clean cold start.

---

## 4. Isolated Execution Sandboxes (`Workspace: "branch"`)

Only when the user explicitly asks the council to **run commands, execute benchmarks, or prototype three competing implementations**:

1. Define a separate custom agent (e.g., `council-sandbox-delegate.md`) whose `tools` list adds `replace_file_content` and `run_command` to the read tools but no subagent tools, with `commandExecutionPolicy: sandbox`.
2. Launch each delegate with **`Workspace: "branch"`** (or `workspace="branch"` in `run_workflow`).
3. Each delegate gets its own isolated Git worktree, so working-tree edits, lockfiles, and test artifacts do not collide across the three delegates.
