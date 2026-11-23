# `strata-graph/1` & `strata-hub/1` Specification

## 1. Single Dataset Schema (`strata-graph/1`)

```json
{
  "schema": "strata-graph/1",
  "id": "bounded-remediation-process",
  "title": "Bounded Autonomous Remediation Process",
  "subtitle": "Job-oriented workflow with proposal/execution split, deterministic gates, and human escalation.",
  "domain": "process",
  "generatedAt": "2026-11-07T05:30:00Z",
  "sourceLabel": "example-wiki/architectures",
  "rootId": "proc:root",
  "relations": {
    "transitions-to": {
      "label": "transitions to",
      "darkColor": "#60a5fa",
      "lightColor": "#2563eb",
      "dash": "none",
      "category": "flow"
    },
    "retries-loop": {
      "label": "↺ bounded retry",
      "darkColor": "#fb923c",
      "lightColor": "#c2410c",
      "dash": "7 4",
      "category": "backtrack"
    }
  },
  "nodes": [
    {
      "id": "proc:root",
      "title": "Bounded Autonomous Remediation",
      "kind": "process",
      "status": "ready",
      "parent": null,
      "summary": "Top-level container."
    },
    {
      "id": "stage:propose",
      "title": "Agent Proposal Generator",
      "kind": "stage",
      "status": "ready",
      "parent": "proc:root",
      "summary": "Generates candidate patch within declared scope and budget.",
      "url": "https://example.org/spec",
      "trust": { "tier": "verified" },
      "sources": [{ "id": "src-1", "title": "Spec PR #27", "url": "https://example.org/pr/27" }],
      "tags": ["proposal"],
      "metrics": { "budget": "max 3 attempts" }
    }
  ],
  "edges": [
    {
      "id": "e1",
      "from": "stage:gate",
      "to": "stage:propose",
      "relation": "retries-loop",
      "flowRole": "backtrack",
      "summary": "↺ Gate rejection returns structured diagnostics while budget remains",
      "contextSnippet": "Bounded Convergence Loop: retry only while scope and token/attempt budget remain."
    }
  ],
  "overlays": [
    {
      "id": "ov:audit",
      "title": "Immutable Audit Trail",
      "kind": "guardrail",
      "summary": "Cross-cutting telemetry & authorization ledger.",
      "touches": ["stage:propose", "stage:gate"]
    }
  ],
  "traces": [
    {
      "id": "trace:retry-then-pass",
      "title": "Scenario A: Gate Fail -> Retry -> Pass",
      "color": "#60a5fa",
      "steps": [
        { "stepIndex": 1, "nodeId": "stage:propose", "label": "Attempt 1: Draft remediation diff", "role": "normal" },
        { "stepIndex": 2, "nodeId": "stage:gate", "label": "✕ Gate rejects out-of-scope edit", "role": "blind-alley", "isError": true },
        { "stepIndex": 3, "nodeId": "stage:propose", "label": "↺ Retry Attempt 2 within fenced scope", "role": "backtrack" }
      ]
    }
  ],
  "diagnostics": []
}
```

Optional fields that change how the viewer draws a dataset:

| Field | Where | Effect |
| :--- | :--- | :--- |
| `levelLabel` | dataset | Unit word in overlay count badges, such as `"section"`. Default: `section` for `okf-wiki`, `phase` for `process`, `layer` otherwise. |
| `axisNotes` | dataset | List of `{ "nodeId": "...", "text": "..." }`. Draws a note in the left margin beside that node on the root view. |
| `quietBypass` | node | `true` dims forward edges that skip more than one row on the root view. |

The validator (`validate`, and every `compile-*` command) reports these errors: `MISSING_ROOT`, `DUPLICATE_ID`, `MISSING_PARENT`, `DANGLING_EDGE`, and `DANGLING_TRACE_STEP`.

## 2. Status & Flow Semantics

| `node.status` | Visual Encoding | Intended Domain Use |
| :--- | :--- | :--- |
| `"ready"` / `"verified"` | Solid card + green verified pill (when `trust.tier == "verified"`) | Canonical concepts, approved KG entities, winning trajectory turns |
| `"draft"` / `"partial"` | Subtle amber border + draft pill | Unverified OKF drafts, WIP modules |
| `"blind-alley"` / `"error"` | Dashed coral border + `-45deg` crimson hatch + `✕ BLIND ALLEY` pill | Failed tool calls, dead-end search branches, rejected proposals |
| `"gate"` | `3px` teal top accent bar + gate pill | Deterministic acceptance gates, human-approval checkpoints, planner routers |
| `"subagent"` | `3px` violet top accent bar + subagent pill | Delegated ATIF/OATR child agents (drillable when child steps exist) |
| `"deprecated"` | Dashed muted border | Retired specs or superseded concepts |

| `edge.flowRole` | Layout & Routing Behavior |
| :--- | :--- |
| `"forward"` (default) | Participates in Sugiyama topological layering + PAV channel alignment; residual cycles in cyclic KGs/wikis are automatically promoted to outer return arcs so downward arrows never lie. |
| `"backtrack"` / `"loop"` | Excluded from downward rank forcing; routed along a dedicated right-margin cubic Bezier return rail with an upward/left arrowhead and clickable `↺` pill badge. |

## 3. Multi-Dataset Hub Envelope (`strata-hub/1`)

```json
{
  "schema": "strata-hub/1",
  "title": "Strata Graph Multi-Domain Explorer",
  "generatedAt": "2026-11-07T05:30:00Z",
  "datasets": [ /* array of strata-graph/1 objects */ ]
}
```
