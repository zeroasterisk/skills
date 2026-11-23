---
name: strata-graph
description: Compile, validate, and explore multi-layer structural and cross-cutting interactive graphs for stateful processes, OKF v0.2 LLM wikis, knowledge/entity graphs (KGs), and ATIF agent trajectories (with explicit blind alleys, backtrack return arcs, subagent drill-down, and cross-trajectory comparison). Use when visualizing complex systems, workflows, concept wikis, people/project/document networks, or multi-turn agent trajectories beyond ~15 nodes where flat static diagrams saturate and force-directed hairballs lose causal hierarchy. Don't use for small static architecture or flow diagrams (use diagram-design).
license: Apache-2.0
---

# Strata graph (`strata-graph`)

A compiler, validator, and interactive HTML explorer for structured graphs of about 15 to 1,500 nodes. These graphs have a hierarchical or causal spine, a dense set of cross-cutting links, and optional traces over time. The output is one HTML file that works from `file://` with no network access.

Independent implementation inspired by Adam Gospodarczyk's (`@overment`) [`overment/limen`](https://github.com/overment/limen) (`limen picture`, MIT License). It keeps limen's main idea: agents curate facts, and a deterministic compiler with no LLM builds the HTML. It also uses hierarchical edge lifting with `OUTSIDE` ghost blocks, cross-cutting bands, and weighted Pool-Adjacent-Violators (PAV) multi-lane routing. It adds OKF v0.2 wikis, knowledge graphs, stateful processes, and ATIF and Jetski trajectories with dead-end marks (`✕`) and backtrack return arcs (`↺`).

## When to use it

| Scale and shape | Tool | Why |
| :--- | :--- | :--- |
| Up to about 15 nodes | `diagram-design` | A hand-laid single-frame SVG or PNG for a doc or slide. |
| About 15 to 1,500 nodes with a spine and cross-cutting links | `strata-graph` | Drill-down, lifted edge bundles, `OUTSIDE` ghost blocks, path tracing, cross-cutting slices, and trajectory scrubbing. |
| More than about 1,500 flat nodes | A force-directed graph viewer | `strata-graph` is not built for this scale, and a flat overview does not need a causal reading order. |

## How it works

1. **Extract facts.** Run an adapter (`compile-okf`, `compile-kg`, `compile-atif`) over existing artifacts, or write a `strata-graph/1` JSON spec and run `compile-json`.
2. **Validate and build.** `scripts/strata.py` checks the root id, node ids, parent references and cycles, edge endpoints, and trace step node ids. It does not call an LLM. It then bundles CSS, JSON, and JS into one HTML file.

## CLI quick reference

All commands use the Python 3.10+ standard library. PyYAML is used when installed.

```bash
STRATA="<skill-dir>/scripts/strata.py"

# 1. Compile an OKF v0.2 Markdown wiki bundle (sections, prose links, co-citation slices)
python3 "$STRATA" compile-okf /path/to/wiki -o /tmp/wiki-map.html

# 2. Compile a knowledge graph (SQLite pipeline.db, or a directory with YAML files)
python3 "$STRATA" compile-kg /path/to/kg-dir -o /tmp/kg-map.html

# 3. Compile one ATIF v1.x or Jetski transcript.jsonl trajectory
#    (marks dead ends with ✕, wires ↺ backtrack arcs, nests subagents)
python3 "$STRATA" compile-atif /path/to/trajectory.json --mode decision -o /tmp/traj-map.html

# 4. Compare two or more trajectories over shared tools, subagents, and failure states
python3 "$STRATA" compile-atif run1.json run2.json run3.jsonl --mode compare -o /tmp/compare.html

# 5. Validate and compile a custom process or architecture JSON spec
python3 "$STRATA" compile-json /path/to/process.strata.json -o /tmp/process.html

# 6. Check a compiled dataset
python3 "$STRATA" validate /tmp/process.json

# 7. Bundle several compiled .json datasets into one multi-tab hub
python3 "$STRATA" build-hub okf.json kg.json atif.json process.json -o /tmp/explorer-hub.html
```

An output path that ends in `.json` writes the dataset instead of HTML. That is how you produce the inputs for `build-hub`.

Set `SOURCE_DATE_EPOCH` to a Unix timestamp to fix `generatedAt`, so the same input gives byte-identical output.

## Writing a process or system graph (`strata-graph/1`)

To model a process, workflow, or architecture from prose or code, write a JSON file that follows [references/schema.md](references/schema.md). Then compile it with `compile-json`.

- **Hierarchy (`parent`).** Group related components or stages in drillable containers (`"parent": "stage:execution"`). Keep 4 to 9 siblings per container so each level is easy to scan.
- **Loops and backtracks (`"flowRole": "backtrack"`).** Include retry loops, rejection rollbacks, and escalation branches. Mark return edges `"flowRole": "backtrack"` so the viewer draws them on a right-hand `↺` return channel and keeps the forward order intact.
- **Status.** Use `"status": "gate"` for acceptance gates and human-approval gates. Use `"status": "blind-alley"` for dead-end hypotheses and error branches. Use `"status": "subagent"` for delegated workers.
- **Cross-cutting slices (`overlays[]`).** Put shared policies, data stores, actors, and citations in `overlays[]` with `touches: [nodeId...]`. This avoids a hub-and-spoke tangle of edges across the spine.

## Controls in the explorer

- **Drill down and up.** Double-click a container card (or click `N parts →`) to open its inner graph with `OUTSIDE` ghost callers and targets. Press `Esc` or click a breadcrumb to go up.
- **Hierarchy and expanded modes.** The `Mode` button in the top bar switches between aggregated container bundles and flattened leaf nodes with dashed group frames.
- **1-hop, 2-hop, and path finder.** Click a card to highlight its 1-hop or 2-hop neighborhood. `Shift+Click` a second card to show the connecting paths (up to 4 hops) and the shared cross-cutting slices.
- **Trace scrubber.** Use `[` and `]`, `Play`, or the step pips to step through a trajectory. Numbered revisit chips (`#1`, `#4`) show when an agent backtracks out of a dead end. `Compare All` overlays several runs (`R1` to `RN`).

## Verification

Before you present a generated HTML map:

1. Run `python3 "$STRATA" validate <dataset.json>` and read every `error` and `warn` diagnostic.
2. Open the HTML in a headless browser (1440x900). Check for no console errors, readable card titles, count pills that do not overlap, and working tab and drill-down navigation.
