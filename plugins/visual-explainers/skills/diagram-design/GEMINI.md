# Diagram Design — Material Design 3 & Google Design System

Create visual diagrams as self-contained HTML files with inline SVG and CSS, using the Material Design 3 (M3) design system with subtle Google colors.

## When to Use

Use whenever creating architecture diagrams, sequence diagrams, flowcharts, IT current-state maps, state machines, data flow pipelines, ER models, swimlanes, quadrant matrices, or timelines.

## Core Design Principles

1. **Material Design 3 Surface & Shape:**
   - Surfaces: `#f8f9fa` (light surface), `#f1f3f4` (surface container low), `#1f1f1f` (dark surface), `#28292a` (dark container).
   - Corner Radii: `rx="12"` for standard node boxes & cards (signature M3 shape), `rx="8"` for sub-chips, `rx="16"` for container zones.
   - Text & Strokes: `#1f1f1f` on light, `#e3e3e3` on dark.
2. **Subtle Google Color Accents:**
   - Primary Accent: Google Blue (`#0b57d0` light / `#a8c7fa` dark) — 1–2 focal elements per diagram.
   - Google Green (`#1e8e3e` / `#81c995`) for data persistence / storage / pass states.
   - Google Amber (`#e37400` / `#fdd663`) for queues / bottlenecks / stage transitions.
   - Google Red (`#d93025` / `#f28b82`) for security boundaries / policy divergences / error paths.
3. **Google Typography:**
   - Google Sans / Google Sans Text for titles and node labels.
   - Roboto Mono for technical labels, ports, and protocols.
4. **Mandatory Routing Rules:**
   - Orthogonal connectors with rounded quarter-arcs (`r=8`). No diagonal lines.
   - Arrow labels masked with 6–10px clear gap above the connector line.
   - Attach points fanned ≥12px apart on shared edges.

## How to Create a Diagram

1. Copy `assets/template.html` (minimal light), `assets/template-dark.html` (dark mode), or `assets/template-full.html` (editorial cards).
2. Choose from the 27 visual types (e.g. `references/type-architecture.md`, `references/type-flowchart.md`, `references/type-sequence.md`, `references/type-data-flow.md`).
3. Replace SVG nodes with M3 `rx="12"` boxes, Google Sans labels, and Roboto Mono sublabels.
4. Validate with `python3 scripts/self_check.py <file.html>`.

See `SKILL.md` and `references/style-guide.md` for full documentation.
