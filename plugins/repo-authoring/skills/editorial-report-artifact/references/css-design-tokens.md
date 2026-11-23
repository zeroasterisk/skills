# Editorial Design Tokens & Component System

Use this design token palette to give standalone HTML research, benchmark, and architecture reports a warm, publication-grade editorial authority (`--ivory` / `--paper` / `--slate`) paired with strictly semantic accent colors (`--olive`, `--clay`, `--rust`, `--sky`).

## 1. Surface & Ink Palette

| CSS Variable | Hex / Value | Role |
| :--- | :--- | :--- |
| `--ivory` | `#FAF9F5` | Primary page background (warm editorial paper; eliminates stark white glare) |
| `--paper` | `#FFFFFF` | Elevated card, table, and diagram surface |
| `--sand` | `#F0EEE6` | Neutral pill background, progress track, and subtle code container |
| `--oat` | `#E3DACC` | Section number badge background (`.sec-head .num`) |
| `--slate` | `#141413` | High-contrast ink for headings, code blocks (`pre.code`), and primary values |
| `--g700` | `#3D3D3A` | Primary body prose and lead paragraph color |
| `--g500` | `#5E5D59` | Secondary labels, captions, and table column headers |
| `--g200` | `#D1CFC5` | Hairline border color (`--border: 1px solid var(--g200)`) |

## 2. Four Strictly Semantic Accent Families

Never assign arbitrary rainbow colors to charts or badges. Every accent maps to a specific epistemic or operational state:

1. **Olive (`--olive: #788C5D`, `--olive-soft: rgba(120, 140, 93, 0.14)`, `--olive-deep: #4B5C39`)**:
   - Verified pass (`100.0%`), Stage-1 early-exit (`H̃_m < τ`), target SLA met, or `100% MAPPED` patent claim coverage.
   - Classes: `.pill.live`, `.cell.olive`, `.callout.ok`, `.fill.olive`, `td.best`, `.sev.low`.
2. **Clay (`--clay: #D97757`, `--clay-soft: rgba(217, 119, 87, 0.12)`, `--clay-deep: #8A3B1E`)**:
   - Primary architectural mechanism, active decision gate (`H̃_m ≥ τ`), interactive node focus, or italic headline emphasis (`h1 em`).
   - Classes: `.pill.clay`, `.cell.accent`, `.callout.warn`, `.fill.clay`, `.gnode.active`, `.sev.med`.
3. **Rust (`--rust: #C44536`, `--rust-soft: rgba(196, 69, 54, 0.12)`)**:
   - Adversarial failure mode, unnormalized scale inversion, high epistemic disagreement (`ChaosNLI` high-entropy), or regression.
   - Classes: `.fill.rust`, `td.bad`, `.sev.high`, `.callout.danger`.
4. **Sky (`--sky: #6A9BCC`, `--sky-soft: rgba(106, 155, 204, 0.14)`)**:
   - Secondary telemetry overlay, baseline reference model, or cross-hardware diagnostic comparison.

## 3. Five-Layer Editorial Information Hierarchy

Structure every standalone HTML report in this five-layer vertical rhythm:

1. **Hero Header (`header.hero`)**:
   - `.eyebrow` (`11.5px` uppercase monospace: `Experiment Record · <Project> · <IDs> · <ISO-Date>`)
   - `h1` (`clamp(30px, 4vw, 44px)` serif with an `<em>` clay-deep italicized focal phrase)
   - `p.lead` (`16.5px` narrative synthesis of the baseline, mechanism, and headline delta)
   - `.status-line` containing 4–5 `.pill` badges summarizing key receipts
2. **Sticky / Pill Table of Contents (`nav.toc`)**:
   - Numbered pill links (`01`–`08`) jumping to `#s1`..`#s8`.
3. **Four-Cell KPI Strip (`.summary`)**:
   - 4 cards side-by-side (`.cell.olive`, `.cell.accent`, `.cell`, `.cell`) with `.k` (uppercase monospace metric name), `.v` (`28px` serif value), and `.s` (delta vs. baseline).
4. **Analytical Sections (`section#s1..#s7`)**:
   - `.sec-head` (`span.num` badge + `h2`) + `p.sec-intro`
   - Alternating between `.grid2` explanatory panels, full-width SVG schematics, `.bars` horizontal threshold comparisons, `.tscroll > table.t` ablation matrices, and `.risks` claim-to-code verification grids.
5. **Interactive Pipeline Explorer (`section#s8` / `.explorer`)**:
   - Left column: clickable SVG workflow graph (`.gnode[data-node="..."]`).
   - Right column: sticky `<aside class="inspector">` populated dynamically from a JavaScript `nodeData` dictionary containing `tag`, `title`, `body`, `kv` pairs (CLI flags, receipt JSON path, latency, accuracy), and `code` snippet.
