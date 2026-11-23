# Strata graph (`strata-graph`)

A compiler, validator, and standalone HTML explorer for layered graphs. It uses only the Python standard library and a single self-contained HTML file with no network access.

It handles four kinds of input:

1. **Processes and stateful workflows.** Ordered stages, acceptance gates, human-approval waits, retry loops, and escalation branches.
2. **Concept graphs and OKF v0.2 wikis.** Hierarchical sections, internal Markdown links, trust badges derived from OKF frontmatter, and cross-cutting overlays for co-citation and tags.
3. **Knowledge and entity graphs.** People, organizations, projects, protocols, and documents, with typed edge bundles, `Shift+Click` path finding, and timeline playback.
4. **ATIF, OATR, and Jetski agent trajectories.** One run as a decision tree with marked dead ends (`✕`), return arcs for backtracks (`↺`), and nested subagents. Several runs can be compared over shared tools.

## Attribution

This plugin is an independent implementation inspired by Adam Gospodarczyk's (`@overment`) [`overment/limen`](https://github.com/overment/limen) (`limen picture`, MIT License). It borrows these ideas from limen:

- Agents curate facts in Markdown, and a deterministic compiler with no LLM builds the output.
- Edges between hierarchy levels are lifted, with `OUTSIDE` ghost blocks for endpoints outside the current view.
- Cross-cutting side bands.
- Weighted Pool-Adjacent-Violators (PAV) isotonic regression to align multi-lane wire bundles.

`strata-graph` adds these on top:

- OKF v0.2, knowledge graph (YAML and SQLite), and trajectory compilers (ATIF, OATR, Jetski JSONL).
- Backtrack and loop edges drawn as `↺` return arcs, instead of silently reversing edges to break cycles.
- Dead-end styling, step scrubbing, and multi-trajectory comparison.
- 1-hop and 2-hop highlighting, `Shift+Click` path finding, pan and zoom.
- Multi-dataset explorer hubs.

See [SKILL.md](skills/strata-graph/SKILL.md) for usage and [references/schema.md](skills/strata-graph/references/schema.md) for the data format.
