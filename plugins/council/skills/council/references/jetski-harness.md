# Jetski Harness Recipes for `council`

Concrete execution templates for running isolated 3-delegate council rounds inside Jetski / Antigravity (`agy`), including cross-model subagent pinning via `~/.config/council/roster.json`.

---

## 1. Subagent Registration, Multi-Model Pinning & Zero-Restart Staging

### A. Default Single-Tier Subagent (`council-delegate`)

When the `council` plugin is enabled before a conversation starts and no `~/.config/council/roster.json` is configured, `council-delegate` (`plugins/council/agents/council-delegate.md`) is pre-registered as a hidden, read-only subagent on the `pro` tier.

### B. Multi-Model Roster Pinning (`~/.config/council/roster.json` + `~/.gemini/config/agents/`)

Native `invoke_subagent` and `run_workflow` request-time `model` strings only accept tier names (`inherit`, `flash_lite`, `flash`, `pro`). However, Jetski declarative JSON agents (`~/.gemini/config/agents/<type_name>/agent.json`) can pin **any** model available in the harness's model list by setting `"disableModelSelection": true` and `"cascadeConfig": {"plannerConfig": {"planModel": "<MODEL_ENUM>"}}` (with `modelTier` unset). When an agent sets `disableModelSelection: true` and no `modelTier`, the harness keeps the agent's pinned `planModel` for both `run_workflow` and `invoke_subagent`, as long as the call does not pass a tier name.

Example `~/.gemini/config/agents/<type_name>/agent.json`:

```json
{
  "name": "council-seat-1",
  "description": "Independent, cold-start council delegate pinned to a dedicated model with read-only tools.",
  "mainAgent": false,
  "subagent": true,
  "hidden": true,
  "disableModelSelection": true,
  "config": {
    "agentConfig": {
      "mixinConfig": {
        "promptSections": [
          {
            "custom": {
              "title": "Council Delegate",
              "content": "You are an independent council delegate evaluating a request from a clean cold start...\n"
            }
          },
          {"builtinName": "user_information"},
          {"builtinName": "skills"},
          {"builtinName": "user_rules"},
          {"builtinName": "messaging"},
          {"builtinName": "artifacts"},
          {"builtinName": "guidelines"},
          {"builtinName": "communication_style"}
        ],
        "tools": [
          {"name": "view_file", "builtin": true},
          {"name": "search_web", "builtin": true},
          {"name": "send_message", "builtin": true}
        ],
        "postInvocationHooks": [
          {"name": "message_continue_check", "builtin": true},
          {"name": "terminal_step_check", "builtin": true},
          {"name": "max_generator_invocations_check", "builtin": true},
          {"name": "empty_output_continuation_check", "builtin": true},
          {"name": "force_invocation", "builtin": true},
          {"name": "no_tool_call_check", "builtin": true}
        ]
      },
      "customizationDiscovery": {
        "skills": {"inheritUser": true},
        "plugins": {"inheritUser": true},
        "rules": {"inheritUser": true},
        "agents": {"inheritUser": true},
        "hooks": {"inheritUser": true},
        "mcp": {"inheritUser": false}
      },
      "cascadeConfig": {
        "plannerConfig": {
          "planModel": "<MODEL_ENUM>"
        }
      }
    }
  }
}
```

Example machine-local `~/.config/council/roster.json` (kept outside public git repos):

```json
{
  "version": 1,
  "seats": [
    {
      "label": "<Model 1 Display Name>",
      "type_name": "council-seat-1",
      "agent_json": "<home>/.gemini/config/agents/council-seat-1/agent.json"
    },
    {
      "label": "<Model 2 Display Name>",
      "type_name": "council-seat-2",
      "agent_json": "<home>/.gemini/config/agents/council-seat-2/agent.json"
    },
    {
      "label": "<Model 3 Display Name>",
      "type_name": "council-seat-3",
      "agent_json": "<home>/.gemini/config/agents/council-seat-3/agent.json"
    }
  ],
  "fallback": {
    "label": "<Fallback Model Display Name>",
    "type_name": "council-seat-fallback",
    "agent_json": "<home>/.gemini/config/agents/council-seat-fallback/agent.json"
  }
}
```

### C. Mid-Session Zero-Restart Staging

If `council` or any `~/.gemini/config/agents/<type_name>/agent.json` was created *during* an already-running conversation (after the conversation started, so the harness cannot see it yet), stage the agent files under the conversation's `.agents/agents/` directory so they resolve immediately without restarting:

```bash
ART_DIR="<appDataDir>/brain/<conversation-id>"
mkdir -p "${ART_DIR}/.agents/agents"
ln -sfn .agents "${ART_DIR}/_agents"
cp -r ~/.gemini/config/agents/council-* "${ART_DIR}/.agents/agents/" 2>/dev/null || \
  cp "<plugin-root>/agents/council-delegate.md" "${ART_DIR}/.agents/agents/"
```

> **Why omitting write/command tools matters**: Omitting `write_file`, `edit_file`, `replace_file_content`, and `run_command` strips mutation capabilities at tool-schema construction time. Three delegates can inspect `Workspace: "inherit"` in parallel with zero risk of mutating working-tree files, git index locks, or build caches, while each delegate's own trajectory lives under `<appDataDir>/brain/<subConvID>/`.

---

## 2. Primary Execution Path: `run_workflow` Parallel Fan-Out (With Roster + Fallback)

When `run_workflow` is available in your tool declarations, prefer it over manual subagent calls:
* Every delegate runs as an isolated, single-use cold-start trajectory (`agent()`).
* `from advanced import parallel` with `return_exceptions=True` prevents a single delegate error or timeout from canceling the other two delegates.
* If `~/.config/council/roster.json` is present, the script automatically loads the 3 model-pinned seats and retries any failed primary seat once on `fallback`.
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
from advanced import parallel

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

phase(f"Round {round_num}: Parallel Council")
results = await parallel(seats, spawn_seat, return_exceptions=True)

output = []
for idx, (seat, res) in enumerate(zip(seats, results)):
    used_label = seat["label"]
    if isinstance(res, Exception) and fallback_seat and seat["type_name"] != fallback_seat["type_name"]:
        log(f"{used_label} failed ({res}); retrying on fallback {fallback_seat['label']}")
        try:
            res = await spawn_seat(fallback_seat, role_prefix=f"Council Fallback S{idx+1}")
            used_label = f"{fallback_seat['label']} (fallback for {seat['label']})"
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

1. Issue **three `invoke_subagent` calls in the same assistant turn** using the `type_name` values from `~/.config/council/roster.json` (with `Model: "inherit"`, since `disableModelSelection: true` preserves each agent's baked-in `planModel`), or `TypeName: "council-delegate"` with `Model: "pro"` if no `roster.json` exists.
2. **Stop calling tools** at the end of that turn. Jetski wakes your conversation reactively as each subagent sends its completion message; never sleep or poll in a loop.
3. For Round 2+, always launch three fresh subagents rather than calling `send_message` on Round 1's `conversationId`s, so Round 2 evaluates the updated work from a clean cold start.

---

## 4. Isolated Execution Sandboxes (`Workspace: "branch"`)

Only when the user explicitly asks the council to **run commands, execute benchmarks, or prototype three competing implementations**:

1. Define a separate subagent (e.g., `council-sandbox-delegate`) with `EnableWriteTools: true`, `EnableSubagentTools: false`.
2. Launch each delegate with **`Workspace: "branch"`** (or `workspace="branch"` in `run_workflow`).
3. Jetski clones an isolated workspace copy and assigns a distinct `environmentID` per delegate, preventing working-tree edits, lockfiles, ports, or test artifacts from colliding across the three delegates.
