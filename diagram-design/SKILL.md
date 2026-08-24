---
name: diagram-design
description: Create branded architecture, IT current-state, flowchart, sequence, state machine, ER/data model, timeline, swimlane, quadrant, radar/spider, loop/flywheel, nested, tree, org chart, layer stack, Venn, pyramid/funnel, bar, line, Gantt and scatter charts, high-level, process, medallion, data flow, DP integration, or DP security matrix diagrams as standalone Material Design 3 HTML/SVG/PNG with subtle Google colors. Redraw .drawio/.drawio.png/.drawio.svg or Mermaid .mmd sources at a chosen size/detail; onboard brand tokens from a website; add semantic patterns, callouts, accessible motion, or sketchy/hand-drawn styling.
license: MIT
metadata:
  version: "3.0"
---

# Diagram Design — Material Design 3 & Google System

Create visual diagrams as self-contained HTML files with inline SVG and CSS, following Material Design 3 (M3) principles and a refined Google color system.

Twenty-seven visual types. Semantic patterns describe behavior independently; type references describe layout. Details load from `references/` only when selected.

---

## 0. First-time setup — style guide gate

**Before generating your first diagram in a new project, verify the style guide has been customized.**

Don't silently ship default-skinned diagrams into a branded project.

First check the project root for a `.diagram-design` marker and resolve it per [`references/profiles.md`](references/profiles.md). A valid marker whose profile exists selects that file directly and skips this gate; `profile: default` also skips it. A malformed or missing-profile marker follows the visible failure handling in that reference. Never copy a marker-selected profile over the installed working copy.

Open [`references/style-guide.md`](references/style-guide.md) and check the default tokens. If they're the shipped defaults (paper `#f8f9fa`, ink `#1f1f1f`, accent `#0b57d0` Google Blue), **pause and ask the user** if they wish to customize it or proceed with the Google Material Design 3 default.

**Once the style guide has been customized** (or the user explicitly opted for default), skip this gate on subsequent runs.

---

## 1. Philosophy

**The highest-quality move is usually deletion.**

Applied to schematics:

- Every node represents a distinct idea. Two nodes that always travel together are one node.
- Every connection carries information. If the relationship is obvious from layout, remove the line.
- Focal accent (Google Blue / Red) is **editorial, not a flag.** 1–2 focal nodes per diagram. Using it on 5 nodes erases the signal.
- The schematic isn't done when everything is added. It's done when nothing can be removed.
- **Material Design 3 Clarity:** Clean tonal surfaces (`surface-container-low`, `surface-container`), high contrast, soft 12px rounded geometry (`rx="12"`), and disciplined typography.

**Target density: 4/10.** Enough to be technically complete. Not so dense it needs a guide. Above 9 nodes, it's probably two diagrams.

---

## 2. When to Use

Use for any of the 27 visual types (§3) when a reader will learn more from a visual than from prose, a table, or a bulleted list.

**Don't use for:**

- Quick unicode diagrams → use **wiretext**.
- Lists of things → table or bullets.
- Simple before/after → table.
- One-shape "diagrams" → just write the sentence.

Before drawing, ask: *Would the reader learn more from this than from a well-written paragraph?* If no, don't draw.

---

## 3. Selection: semantic pattern, then visual type

When behavior, state, enforcement, or risk carries the meaning, first load [`references/semantic-patterns.md`](references/semantic-patterns.md) and choose one primary pattern. Then choose the nearest visual type for layout. If no pattern matches, choose the type directly.

| Behavioral trigger | Semantic pattern → nearest type |
|---|---|
| Fan-in, queue depth, finite capacity, bottleneck | **Fan-in queue / bottleneck** → Data flow |
| Repeated Question / Input / Governance / Output slots across stages | **Stage framework with semantic slots** → Process |
| Conversation or loose input becomes a structured durable artifact | **Unstructured input → structured artifact** → Data flow |
| Two rule traces need pass/fail/skipped/not-reached and first divergence | **Paired policy-evaluation traces** → Flowchart |
| Trust boundaries plus permitted/forbidden ingress or deploy paths | **Secure paved road** → Architecture |
| Controls grouped by where they are enforced | **Governance / control catalog** → Layer stack |
| Defenses compensate for prior gaps and residual risk propagates | **Compensating security layers** → Layer stack |

The pattern owns semantic primitives and its tighter budget; the type owns layout grammar. Use [`references/animation.md`](references/animation.md) only when motion is requested or materially clarifies ordered change; static remains the default.

### Visual-type guide (27)

| If you're showing… | Use | Reference |
|---|---|---|
| Components + connections in a system | **Architecture** | [type-architecture.md](references/type-architecture.md) |
| Legacy IT landscape grouped by phase/department; documents modernization | **IT current-state** | [type-it-state.md](references/type-it-state.md) |
| Decision logic with branches | **Flowchart** | [type-flowchart.md](references/type-flowchart.md) |
| Time-ordered messages between actors | **Sequence** | [type-sequence.md](references/type-sequence.md) |
| States + transitions + guards | **State machine** | [type-state.md](references/type-state.md) |
| Entities + fields + relationships | **ER / data model** | [type-er.md](references/type-er.md) |
| Events positioned in time | **Timeline** | [type-timeline.md](references/type-timeline.md) |
| Cross-functional process with handoffs | **Swimlane** | [type-swimlane.md](references/type-swimlane.md) |
| Two-axis positioning / prioritization | **Quadrant** | [type-quadrant.md](references/type-quadrant.md) |
| Multiple entities scored across 3–5 quantitative criteria | **Radar / Spider** | [type-radar.md](references/type-radar.md) |
| Reinforcing cycle / flywheel where the last step feeds the first | **Loop** | [type-loop.md](references/type-loop.md) |
| Hierarchy through containment / scope | **Nested** | [type-nested.md](references/type-nested.md) |
| Parent → children relationships | **Tree** | [type-tree.md](references/type-tree.md) |
| Human/agent/team ownership, reporting, routing, escalation | **Org chart** | [type-org-chart.md](references/type-org-chart.md) |
| Stacked abstraction levels | **Layer stack** | [type-layers.md](references/type-layers.md) |
| Overlap between sets | **Venn** | [type-venn.md](references/type-venn.md) |
| Ranked hierarchy or conversion drop-off | **Pyramid / funnel** | [type-pyramid.md](references/type-pyramid.md) |
| Quantitative comparison across categories | **Bar chart** | [type-bar.md](references/type-bar.md) |
| Continuous trends over time | **Line chart** | [type-line.md](references/type-line.md) |
| Tasks and phases on a timeline | **Gantt** | [type-gantt.md](references/type-gantt.md) |
| Distribution and correlation between two variables | **Scatter plot** | [type-scatter.md](references/type-scatter.md) |
| End-to-end data stack on a container cluster | **High-Level** | [type-high-level.md](references/type-high-level.md) |
| Multi-actor sequential process with data handoffs | **Process** | [type-process.md](references/type-process.md) |
| Multi-tier data storage with quality levels and access policies | **Medallion** | [type-medallion.md](references/type-medallion.md) |
| Role-scoped data flow: who does what at each pipeline step | **Data flow** | [type-data-flow.md](references/type-data-flow.md) |
| Integration topology of a data platform — sources → core → consumers | **DP integration** | [type-dp-integration.md](references/type-dp-integration.md) |
| Per-role / per-component access permissions matrix | **DP security matrix** | [type-dp-security-matrix.md](references/type-dp-security-matrix.md) |

**Always load the chosen `references/type-*.md` before drawing.**

---

## 4. Universal Anti-patterns

These mark low-quality schematics of any type:

| Anti-pattern | Why it fails |
|---|---|
| Dark mode + cyan/purple neon glow | Looks "technical" without design decisions |
| JetBrains Mono as blanket "dev" font | Mono is for *technical* content — ports, commands, URLs. Names go in Google Sans / Roboto. |
| Sharp boxy corners without radius | Unrefined; Material Design 3 uses rounded geometry (`rx="12"` for boxes, `rx="8"` for chips). |
| Identical boxes for every node | Erases hierarchy |
| Legend floating inside the diagram area | Collides with nodes |
| Arrow labels with no masking rect | Bleeds through the line |
| Vertical `writing-mode` text on arrows | Unreadable |
| 3 equal-width summary cards as default | Generic grid — vary widths |
| Heavy drop shadows on elements | Muddy and busy. Use M3 tonal surface elevation and clean stroke borders. |
| Accent color on every "important" node | Accent is 1–2 editorial accents, not a signaling system |
| Diagonal / slanted connectors between off-axis nodes | Rounded right-angle (orthogonal) elbows are mandatory — see §6 Mandatory connector rules |
| Arrow label sitting on or touching its connector | Label must have a 6–10px gap above the line so the connector stays visible |
| Arrow label mask overlapping a node box | Nodes paint after labels — the fill clips the text into a fragment on the border. |
| Two connectors overlapping or running on the same path | Each connection must be independently traceable — bridge crossings, offset parallels |
| Two connectors sharing a single attach point on a box | Fan attach points along the edge (≥12px apart) so every arrow is clearly distinct |

---

## 5. Material Design 3 Design System

**The design system is skinnable.** All colors, typography, and tokens live in a single source of truth — [`references/style-guide.md`](references/style-guide.md).

### Semantic roles (at a glance)

| Role | Purpose | Default Light | Default Dark |
|---|---|---|---|
| `paper`, `paper-2` | Page bg and container bg | `#f8f9fa` / `#f1f3f4` | `#1f1f1f` / `#28292a` |
| `ink` | Primary text / stroke | `#1f1f1f` | `#e3e3e3` |
| `muted`, `soft` | Secondary text, default arrows, sublabels | `#444746` / `#747775` | `#c4c7c5` / `#8e918f` |
| `rule`, `rule-solid` | Hairline borders, card outlines | `rgba(31,31,31,0.12)` / `#c4c7c5` | `rgba(227,227,227,0.12)` / `#444746` |
| `accent`, `accent-tint` | 1–2 focal elements (Google Blue) | `#0b57d0` / `rgba(11,87,208,0.08)` | `#a8c7fa` / `rgba(168,199,250,0.12)` |
| `link` | HTTP/API calls, external arrows | `#0b57d0` | `#a8c7fa` |

**Google Semantic Accents:**
- **Google Red** (`#d93025` / `#f28b82`): Security, policy divergence, errors, fail traces.
- **Google Amber** (`#e37400` / `#fdd663`): Queues, warning thresholds, stage bottlenecks.
- **Google Green** (`#1e8e3e` / `#81c995`): Storage, databases, pass traces, verified artifacts.

### Node type → treatment (M3 Style)

| Type | Fill | Stroke | Radius |
|---|---|---|---|
| **Focal** (1–2 max) | `accent-tint` (`rgba(11,87,208,0.08)`) | `accent` (`#0b57d0`) | `rx="12"` |
| **Backend / API / Service** | `#ffffff` (light) / `#28292a` (dark) | `rule-solid` (`#c4c7c5`) | `rx="12"` |
| **Store / Database / State** | `rgba(30,142,62,0.06)` (Google Green) | `#1e8e3e` or `muted` | `rx="12"` |
| **External / Cloud** | `rgba(11,87,208,0.04)` (Google Blue) | `rgba(11,87,208,0.35)` | `rx="12"` |
| **Input / User** | `rgba(68,71,70,0.06)` / `#f1f3f4` | `soft` (`#747775`) | `rx="12"` |
| **Optional / Async** | `rgba(31,31,31,0.02)` | `rgba(31,31,31,0.25)` dashed `4,3` | `rx="12"` |
| **Security / Boundary** | `rgba(217,48,37,0.05)` (Google Red) | `rgba(217,48,37,0.50)` dashed `4,4` | `rx="12"` |

### Typography (Material Design 3)

- **Title** — Google Sans / Roboto, 1.75rem (28px), 500/400 — H1 only
- **Node name** — Google Sans Text / Google Sans, 12px, 500/600 — human-readable labels
- **Sublabel** — Roboto Mono, 9px — ports, URLs, field types
- **Eyebrow / tag** — Google Sans Text, 7–8px, uppercase, tracked 0.12em — type tags, axis labels
- **Arrow label** — Roboto Mono, 8px, 500 — annotation on arrows
- **Editorial aside** — Google Sans Text, 13–14px, *italic* — callouts only

```html
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Google+Sans:wght@400;500;700&family=Google+Sans+Text:ital,wght@0,400;0,500;0,700;1,400&family=Roboto+Mono:wght@400;500;600&family=Roboto:ital,wght@0,400;0,500;0,700;1,400&display=swap" rel="stylesheet">
```

---

## 6. Core SVG Primitives

Universal building blocks:

- Editorial callouts → [primitive-annotation.md](references/primitive-annotation.md)
- Hand-drawn variant → [primitive-sketchy.md](references/primitive-sketchy.md)
- Icon set (Compute, Storage, Network, GCP, etc.) → [primitive-icons.md](references/primitive-icons.md)
- Terminal / CLI-window variant → [primitive-terminal.md](references/primitive-terminal.md)
- Explanatory motion → [animation.md](references/animation.md)

### Background

**Default: clean M3 surface.** Single `<rect>` filled with `paper` (`#f8f9fa`).

```svg
<rect width="100%" height="100%" fill="#f8f9fa"/>
```

### Arrow markers

```svg
<marker id="arrow" markerWidth="8" markerHeight="6" refX="7" refY="3" orient="auto">
  <polygon points="0 0, 8 3, 0 6" fill="#444746"/>
</marker>
<marker id="arrow-accent" markerWidth="8" markerHeight="6" refX="7" refY="3" orient="auto">
  <polygon points="0 0, 8 3, 0 6" fill="#0b57d0"/>
</marker>
<marker id="arrow-link" markerWidth="8" markerHeight="6" refX="7" refY="3" orient="auto">
  <polygon points="0 0, 8 3, 0 6" fill="#0b57d0"/>
</marker>
```

| Arrow | Stroke | When |
|---|---|---|
| Default | muted `#444746` | Internal, generic |
| Accent | Google Blue `#0b57d0` | Primary / highlighted / headline |
| Link-blue | `#0b57d0` | HTTP/API calls, external systems |
| Green | `#1e8e3e` | Data persistence, success flows |
| Red | `#d93025` | Rejections, critical alert paths |
| Dashed | `stroke-dasharray="5,4"` + any color | Optional, passive, return, async |

**Draw arrows before boxes** so z-order puts lines behind nodes.

### Mandatory connector rules

1. **Rounded right-angle (orthogonal) connectors are mandatory.** Every bend must be a quarter-arc with `r=8` (or `r=6` for tight layouts). Diagonal connectors are an automatic fail.
2. **Label-to-connector margin: 6–10px gap, always.** Place label centered above (or beside) the line with minimum 6px gap between mask rect and stroke.
3. **No overlapping connectors.** When crossing at a single point, apply the bridge/hop primitive. Offset parallel lines by ≥12px.
4. **Shared edge → fan the attach points.** Spread attach points evenly along the edge with ≥12px between adjacent points.
5. **No connector passing behind an intervening box without dashed transit.**
6. **No label mask overlapping a node drawn after it.**

### Node box — M3 pattern (`rx="12"`)

```svg
<!-- 1. Opaque paper mask -->
<rect x="X" y="Y" width="W" height="H" rx="12" fill="#f8f9fa"/>
<!-- 2. Styled box with M3 12px rounded corner -->
<rect x="X" y="Y" width="W" height="H" rx="12" fill="FILL" stroke="STROKE" stroke-width="1"/>
<!-- 3. M3 Type Tag / Chip (rx="4" or rx="6") -->
<rect x="X+10" y="Y+8" width="32" height="14" rx="4" fill="transparent" stroke="STROKE@0.40" stroke-width="0.8"/>
<text x="X+26" y="Y+18" fill="STROKE@0.8" font-size="7" font-family="'Google Sans Text', sans-serif"
      text-anchor="middle" letter-spacing="0.08em">API</text>
<!-- 4. Node name (Google Sans / Google Sans Text) -->
<text x="CX" y="CY+2" fill="#1f1f1f" font-size="12" font-weight="500"
      font-family="'Google Sans Text', 'Google Sans', sans-serif" text-anchor="middle">Node Name</text>
<!-- 5. Technical sublabel (Roboto Mono) -->
<text x="CX" y="CY+18" fill="#444746" font-size="9"
      font-family="'Roboto Mono', monospace" text-anchor="middle">service:port</text>
```

### Arrow labels

```svg
<!-- Mask sits 14px above the arrow. Stroke is at ARROW_Y. -->
<rect x="MID_X-18" y="ARROW_Y-20" width="36" height="12" rx="4" fill="#f8f9fa"/>
<text x="MID_X" y="ARROW_Y-11" fill="#747775" font-size="8" font-weight="500"
      font-family="'Roboto Mono', monospace" text-anchor="middle" letter-spacing="0.05em">WRITE</text>
```

### Legend — horizontal strip at the bottom

```svg
<line x1="30" y1="LEGEND_Y-8" x2="VIEWBOX_W-30" y2="LEGEND_Y-8"
      stroke="rgba(31,31,31,0.12)" stroke-width="0.8"/>
<text x="30" y="LEGEND_Y+8" fill="#444746" font-size="8" font-weight="500"
      font-family="'Roboto Mono', monospace" letter-spacing="0.14em">LEGEND</text>
```

---

## 7. Layout & Spacing

### 4px grid

**All values — font sizes, padding, node dimensions, gaps, x/y coords — divisible by 4.**

| Category | Allowed values |
|---|---|
| Font sizes | 8, 12, 16, 20, 24, 28, 32, 40 |
| Node width / height | 80, 96, 112, 120, 128, 140, 144, 160, 180, 200, 240, 320 |
| x / y coordinates | multiples of 4 |
| Gap between nodes | 20, 24, 32, 40, 48 |
| Padding inside boxes | 8, 12, 16 |
| Border radius (M3) | 4 (xs), 8 (sm), 12 (md), 16 (lg) |

### Complexity budget (per diagram)

Max nodes: 9 (split into overview + detail if larger). Max arrows: 12. Max focal elements: 2.

---

## 8. Material Design 3 Summary Cards

```html
<div class="card">
  <p class="eyebrow">COMPONENT OVERVIEW</p>
  <div class="card-header">
    <span class="card-dot blue"></span>
    <h3>Service Controller</h3>
  </div>
  <ul><li>Dispatches tasks to worker pool</li></ul>
</div>
```

Rules:
- `background: #ffffff`
- `border: 1px solid var(--color-rule)`
- `border-radius: 12px` (M3 card radius)
- `padding: 1.25rem`
- Card dots: 8px, `border-radius: 50%` (`blue`, `green`, `yellow`, `red`, `ink`, `muted`)

---

## 9. Pre-Output Checklist (Taste Gate)

Run before producing any diagram:

- [ ] Right visual type and semantic pattern?
- [ ] Nodes use Material Design 3 `rx="12"` rounded geometry?
- [ ] Google Sans / Roboto font stack used throughout?
- [ ] Google Blue `#0b57d0` / `#a8c7fa` used for primary focal accent?
- [ ] Connectors use rounded right-angle elbows (`r=8`)? No diagonal lines?
- [ ] Arrow labels masked with 6–10px gap above connector?
- [ ] No connector overlaps; attach points fanned ≥12px apart?
- [ ] Accessible SVG contract fulfilled (`role="img"`, `aria-labelledby`, `<title>`, `<desc>`)?
- [ ] 4px grid respected?
