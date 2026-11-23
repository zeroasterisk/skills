---
name: strata-graph
description: Compile, validate, and explore multi-layer structural and cross-cutting interactive graphs for stateful processes, OKF v0.2 LLM wikis, knowledge/entity graphs (KGs), and ATIF/OATR agent trajectories (with explicit blind alleys, backtrack return arcs, subagent drill-down, and cross-trajectory comparison). Use when visualizing complex systems, workflows, concept wikis, people/project/document networks, or multi-turn agent trajectories beyond ~15 nodes where flat static diagrams saturate and force-directed hairballs lose causal hierarchy. Don't use for small static architecture or flow diagrams (use diagram-design).
license: Apache-2.0
---

# Strata Graph (`strata-graph`)

Deterministic compiler, integrity validator, and zero-CDN interactive HTML explorer for **meso-scale structured graphs (`15–1,500+` nodes)** that combine a **hierarchical/causal spine** with a **dense cross-cutting web** and **temporal/counterfactual traces**.

> **Architectural Heritage**: Inspired by Adam Gospodarczyk's (`@overment`) [`overment/limen`](https://github.com/overment/limen) (`limen picture`, MIT License) — keeping its core principle (*agents curate facts; a deterministic zero-LLM compiler builds the HTML*), hierarchical edge lifting with `OUTSIDE` ghost blocks, cross-cutting bottom bands, and weighted Pool-Adjacent-Violators (`PAV`) multi-lane cable routing, while extending it to OKF v0.2 wikis, Knowledge Graphs, Stateful Processes, and ATIF/OATR trajectories with explicit blind alleys (`✕`) and backtrack return arcs (`↺`).

## When to Use vs. Neighboring Visualization Tools

| Scale & Topology | Best Tool | Why |
| :--- | :--- | :--- |
| **`<= 15` nodes** (single slide or hero diagram) | `diagram-design` | Curated single-frame SVG/PNG layout for docs and decks. |
| **`15 – 1,500` structured + cross-cutting nodes** | **`strata-graph`** | Hierarchical drill-down, lifted colored wire bundles, `OUTSIDE` ghost blocks, `Shift+Click` path tracing, cross-cutting slices, and ATIF blind-alley/backtrack scrubbing. |
| **`1,500 – 50,000+` flat vault nodes** | `vault-graph` | WebGL force-directed cluster overview when causal reading order is not needed. |

## Core Principle: Two-Stage Separation

1. **Fact Extraction / Adapter Stage**: Either run a deterministic adapter (`compile-okf`, `compile-kg`, `compile-atif`) directly over existing structured artifacts, OR author a `strata-graph/1` JSON spec (`compile-json`) for custom processes and architectures.
2. **Deterministic Build & Audit Stage**: `scripts/strata.py` validates every node ID, parent tree, edge endpoint, source bijection, and trace step **without calling an LLM**, then bundles CSS + JSON + JS into a single zero-network `file://`-safe HTML file.

## CLI Quick Reference

All commands use Python 3.10+ standard library (`scripts/strata.py` relative to this skill directory):

```bash
STRATA="<skill-dir>/scripts/strata.py"

# 1. Compile an OKF v0.2 Markdown wiki bundle (sections + prose links + co-citation slices)
python3 "$STRATA" compile-okf /path/to/wiki -o /tmp/wiki-map.html

# 2. Compile a Knowledge / Entity Graph (SQLite pipeline.db, YAML kg/ dir, or JSON)
python3 "$STRATA" compile-kg /path/to/agents-kg -o /tmp/kg-map.html

# 3. Compile a single ATIF v1.x, OATR v1, or Jetski transcript.jsonl trajectory
#    (detects blind alleys ✕, wires explicit ↺ backtrack arcs, nests subagents)
python3 "$STRATA" compile-atif /path/to/trajectory.json --mode decision -o /tmp/traj-map.html

# 4. Compare 2..N trajectories over a shared Tool / Subagent / Failure-State matrix
python3 "$STRATA" compile-atif run1.json run2.oatr.json run3.jsonl --mode compare -o /tmp/compare.html

# 5. Validate and compile a custom stateful Process / Architecture JSON spec
python3 "$STRATA" compile-json /path/to/process.strata.json -o /tmp/process.html

# 6. Bundle multiple compiled .json datasets into one multi-tab Explorer Hub
python3 "$STRATA" build-hub okf.json kg.json atif.json process.json -o /tmp/explorer-hub.html
```

## Authoring Custom Process & System Graphs (`strata-graph/1`)

When modeling a stateful process, workflow, or system architecture from prose/code, emit a JSON file conforming to [references/schema.md](references/schema.md) and compile with `compile-json`:

- **Hierarchy (`parent`)**: Group related components or stages inside drillable containers (`"parent": "stage:execution"`). Keep `4–9` sibling blocks per container so every focus level scans cleanly.
- **Explicit Loops & Backtracks (`"flowRole": "backtrack"`)**: Never omit retry loops, rejection rollbacks, or escalation spurs! Mark return edges `"flowRole": "backtrack"` so the viewer routes them along dedicated right-hand `↺` return channels instead of reversing causal order.
- **Blind Alleys & Gates (`status`)**: Use `"status": "gate"` for deterministic acceptance / human-approval gates, `"status": "blind-alley"` for dead-end hypotheses or error spurs, and `"status": "subagent"` for delegated workers.
- **Cross-Cutting Slices (`overlays[]`)**: Put cross-cutting policies, shared data stores, actors, or citations in `overlays[]` (`touches: [nodeId...]`) rather than creating hub-and-spoke spaghetti edges across the spine.

## Interactive Controls in the Rendered Explorer

- **Drill Down / Up**: Double-click any stacked container card (or click `N parts →`) to open its internal graph with `OUTSIDE` ghost callers/targets; press `Esc` or click breadcrumbs to go up.
- **Hierarchy vs. Expanded Mode**: Toggle `Mode: Hierarchy` / `Mode: Expanded` in the top bar to switch between aggregated container bundles and flattened leaf nodes with dashed group frames.
- **1-Hop / 2-Hop & Path Finder (`A ↔ B`)**: Click a card to highlight its 1-hop or 2-hop neighborhood; **`Shift+Click` any second card** to isolate all connecting paths (up to 4 hops) and shared cross-cutting slices.
- **ATIF & Process Scrubber**: Use `[` and `]` (or `▶ Play` / step pips) to step through trajectories, see numbered revisit chips (`#1`, `#4`) when an agent backtracks out of a blind alley, or click **`⇄ Compare All`** to overlay multiple runs (`R1..RN`).

## Verification Gate

Always run two checks before presenting a generated HTML map:
1. Run `python3 "$STRATA" validate <dataset.json>` and inspect any `error` or `warn` diagnostics.
2. Render the HTML in a headless browser (`1440x900`) and verify `0` console errors, legible card titles, non-overlapping count pills, and working tab/drill-down navigation.
