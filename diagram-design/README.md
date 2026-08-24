# Diagram Design — Material Design 3 (Google Edition)

Publication-grade visual schematics and software architecture diagrams generated as self-contained HTML/SVG files. Built with **Material Design 3 (M3)** principles, subtle Google brand colors, and the official Google Sans / Roboto typography stack.

---

## Highlights

- **27 Diagram Types**: Architecture, Sequence, Flowchart, State Machine, ER / Data Model, Data Flow, IT Current-State, Medallion, High-Level, Timeline, Swimlane, Quadrant, Radar, Loop/Flywheel, Layer Stack, Gantt, and more.
- **Material Design 3**: Clean tonal surfaces (`surface-container-low`, `surface-container`), high contrast, signature 12px rounded rects (`rx="12"`), and tonal elevations.
- **Subtle Google Colors**: Google Blue primary focal accent (`#0b57d0` / `#a8c7fa`), Google Green storage (`#1e8e3e`), Google Amber queue (`#e37400`), Google Red security (`#d93025`).
- **Google Typography**: `Google Sans` for headlines, `Google Sans Text` for node labels, and `Roboto Mono` for technical ports, protocols, and field types.
- **Strict Layout Rules**: Orthogonal connectors with rounded quarter-arcs (`r=8`), mandatory 6–10px label-to-line gaps, fanned attach points (≥12px apart), and 4px grid alignment.
- **Zero Heavy Dependencies**: Outputs standalone, zero-JS or accessible-motion HTML/SVG files that render cleanly in any modern browser, docs site, slide deck, or social card.

---

## Supported Diagram Types (27)

| Visual Type | Typical Use Case | Reference |
|---|---|---|
| **Architecture** | Component topologies, microservices, cloud deployments | [`references/type-architecture.md`](references/type-architecture.md) |
| **Data Flow** | Pipeline stages, transformations, ingestion | [`references/type-data-flow.md`](references/type-data-flow.md) |
| **Sequence** | Time-ordered protocol handshakes, RPCs, OAuth flows | [`references/type-sequence.md`](references/type-sequence.md) |
| **Flowchart** | Decision trees, evaluation logic, business rules | [`references/type-flowchart.md`](references/type-flowchart.md) |
| **State Machine** | Lifecycle states, transitions, guard conditions | [`references/type-state.md`](references/type-state.md) |
| **ER / Data Model** | Database schemas, entities, keys, relationships | [`references/type-er.md`](references/type-er.md) |
| **IT Current-State** | Modernization proposals, legacy vs target architectures | [`references/type-it-state.md`](references/type-it-state.md) |
| **Medallion** | Multi-tier lakehouse storage (Bronze / Silver / Gold) | [`references/type-medallion.md`](references/type-medallion.md) |
| **DP Integration** | Data platform sources → processing → consumers | [`references/type-dp-integration.md`](references/type-dp-integration.md) |
| **DP Security Matrix**| Role-based access control, security permissions grid | [`references/type-dp-security-matrix.md`](references/type-dp-security-matrix.md) |
| **High-Level** | End-to-end multi-tier cluster topology | [`references/type-high-level.md`](references/type-high-level.md) |
| **Process** | Multi-actor sequential workflow with artifact handoffs | [`references/type-process.md`](references/type-process.md) |
| **Timeline** | Chronological milestones, roadmaps, release phases | [`references/type-timeline.md`](references/type-timeline.md) |
| **Swimlane** | Cross-functional team responsibilities & handoffs | [`references/type-swimlane.md`](references/type-swimlane.md) |
| **Quadrant** | 2×2 prioritization, BCG / scenario matrix | [`references/type-quadrant.md`](references/type-quadrant.md) |
| **Radar / Spider** | Quantitative multi-criteria entity scoring | [`references/type-radar.md`](references/type-radar.md) |
| **Loop / Flywheel** | Reinforcing feedback cycles, flywheel mechanics | [`references/type-loop.md`](references/type-loop.md) |
| **Layer Stack** | Abstraction levels, governance / control layers | [`references/type-layers.md`](references/type-layers.md) |
| **Nested / Tree** | Containment hierarchies, org structures, taxonomies | [`references/type-nested.md`](references/type-nested.md) |
| **Charts** | Bar, Line, Gantt, Scatter plot | [`references/type-bar.md`](references/type-bar.md) |

---

## Design System Tokens

### Semantic Colors

| Role | Light | Dark | Semantic Purpose |
|---|---|---|---|
| `paper` | `#f8f9fa` | `#1f1f1f` | Canvas surface (Google Grey 50 / Dark Surface) |
| `paper-2` | `#f1f3f4` | `#28292a` | Container background (Surface Container Low) |
| `paper-3` | `#e8eaed` | `#2d2f31` | Nested surface (Surface Container) |
| `ink` | `#1f1f1f` | `#e3e3e3` | Primary text and primary strokes |
| `muted` | `#444746` | `#c4c7c5` | Secondary text, default connectors |
| `soft` | `#747775` | `#8e918f` | Sublabels, tertiary annotations |
| `rule` | `rgba(31,31,31,0.12)` | `rgba(227,227,227,0.12)` | Divider hairlines, subtle borders |
| `rule-solid` | `#c4c7c5` | `#444746` | Outlined card and node borders |
| `accent` | `#0b57d0` | `#a8c7fa` | Focal element (Google Blue 700/200) |
| `accent-tint` | `rgba(11,87,208,0.08)` | `rgba(168,199,250,0.12)` | Focal node fill |
| `green` | `#1e8e3e` | `#81c995` | Storage, database, verified state |
| `yellow` | `#e37400` | `#fdd663` | Queue, warning, transition state |
| `red` | `#d93025` | `#f28b82` | Security boundary, failure, policy alert |

### Typography

```html
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Google+Sans:wght@400;500;700&family=Google+Sans+Text:ital,wght@0,400;0,500;0,700;1,400&family=Roboto+Mono:wght@400;500;600&family=Roboto:ital,wght@0,400;0,500;0,700;1,400&display=swap" rel="stylesheet">
```

- **Page H1 / Title**: `Google Sans` (1.75rem / 28px, weight 500)
- **Node Names**: `Google Sans Text` (12px, weight 500/600)
- **Technical Sublabels**: `Roboto Mono` (9px, weight 400)
- **Eyebrows & Tags**: `Google Sans Text` (7–8px, weight 500, uppercase, letter-spacing 0.12em)
- **Connector Labels**: `Roboto Mono` (8px, weight 500)

### Shape Geometry

- `radius-xs`: `4px` (small tags/chips)
- `radius-sm`: `8px` (inner chips)
- `radius-md`: `12px` (standard node boxes and cards — M3 signature rounded rect)
- `radius-lg`: `16px` (group container boundaries)
- `radius-pill`: `9999px` (status pills)

---

## Templates

- `assets/template.html`: Minimal clean light mode diagram.
- `assets/template-dark.html`: Dark mode high-contrast diagram.
- `assets/template-full.html`: Full editorial layout with M3 summary cards.
- `assets/template-motion.html`: Animated step-by-step explanatory diagram.
- `assets/template-terminal.html`: Developer CLI-chrome terminal window variant.

---

## Validation

Verify any generated diagram against the M3 accessible SVG contract and single-file safety rules:

```bash
python3 scripts/self_check.py path/to/my-diagram.html
```

---

## License

MIT
