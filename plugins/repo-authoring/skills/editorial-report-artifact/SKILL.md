---
name: editorial-report-artifact
description: Author standalone, zero-dependency HTML technical experiment records, benchmark ablations, and architecture briefings using a warm editorial design system, offline semantic HTML mathematical typography, inline SVG schematics, interactive pipeline explorers, and claim-to-code verification matrices. Use when asked to create a rich HTML report, experiment ledger artifact, or interactive technical briefing.
license: Apache-2.0
compatibility: Requires python3 and git.
metadata:
  author: ghchinoy
  version: "1.0.0"
---

# Editorial Report Artifact (`editorial-report-artifact`)

Generate publication-grade, single-file HTML technical experiment records and architecture reports (`*.html`) with zero external JavaScript or CDN dependencies, warm editorial typography, offline mathematical rendering, inline SVG schematics, and interactive node-inspector pipelines.

## Reference, Asset & Script Files (Progressive Disclosure)

- [`assets/artifact-skeleton.html`](assets/artifact-skeleton.html) — Self-contained HTML5 starter skeleton with `--ivory` / `--paper` / `--slate` / `--clay` / `--olive` CSS tokens, `.math` rules, 4-cell KPI strip, responsive tables, horizontal bar charts, and interactive SVG pipeline explorer wiring.
- [`references/css-design-tokens.md`](references/css-design-tokens.md) — Complete specification of the warm editorial surface palette, the 4 strictly semantic accent families (`--olive`, `--clay`, `--rust`, `--sky`), and the 5-layer information hierarchy.
- [`references/html-math-cheatsheet.md`](references/html-math-cheatsheet.md) — LaTeX-to-Offline-HTML mathematical typography lookup table (`<span class="math">`, combining diacriticals `&#771;`, subscripts, and entity mappings) that eliminates unrendered `$...$` formulas.
- [`references/svg-schematic-patterns.md`](references/svg-schematic-patterns.md) — Reusable horizontal system schematic SVGs (`viewBox="0 0 940 205"`), arrowhead `<marker>` definitions, XML entity escaping rules, and vanilla JS `.explorer` + `<aside class="inspector">` wiring.
- [`scripts/lint-html-artifact.py`](scripts/lint-html-artifact.py) — Post-generation verification linter that fails on unrendered LaTeX macros (`\tilde`, `\ln`, `\mathcal`), raw `$...$` inline math delimiters, stray Markdown backticks, unescaped SVG `<text>` entities, or un-ignored git paths (`--check-gitignored`).

---

## Workflow

### Step 1: Determine Placement & Git Hygiene

1. Check whether the user requested a committed project page or an unversioned/scratch briefing (e.g., *"place in a directory that won't be committed"*).
2. For unversioned artifacts, inspect `.gitignore` first and place the output inside a gitignored directory such as `scratch/<artifact_name>.html`.

### Step 2: Scaffold from `assets/artifact-skeleton.html`

Start from [`assets/artifact-skeleton.html`](assets/artifact-skeleton.html) and structure the document along the **Five-Layer Editorial Information Hierarchy** detailed in [`references/css-design-tokens.md`](references/css-design-tokens.md):

1. **Hero Header (`header.hero`)**:
   - `.eyebrow`: `Experiment Record · <Project> · <Experiment IDs> · <YYYY-MM-DD>`
   - `h1`: High-contrast serif headline with an italicized `<em>` focal phrase (`color: var(--clay-deep)`).
   - `p.lead`: Narrative synthesis naming the model/system, the core mathematical or architectural mechanism, and the headline improvement.
   - `.status-line`: 4–5 `.pill` badges (`live` olive for verified lifts, `clay` for active mechanisms, neutral for hardware/latency specs).
2. **Numbered Pill Table of Contents (`nav.toc`)**:
   - Sticky top bar (`position: sticky; top: 0; backdrop-filter: blur(8px)`) with anchor pills (`01` through `07`+) linking to `#s1`..`#s8`.
   - **Mandatory WebView Smooth-Scroll Handler**: Embedded IDE/WebView HTML previewers block bare `<a href="#s1">` anchor navigation. Always include the vanilla JS `scrollIntoView({ behavior: 'smooth', block: 'start' })` + `IntersectionObserver` active-pill script from [`assets/artifact-skeleton.html`](assets/artifact-skeleton.html), and ensure every `<section id="s1..s8">` sets `scroll-margin-top: 76px`.
3. **Four-Cell KPI Summary Strip (`.summary`)**:
   - Big `28px` serif metric (`.v`), uppercase monospace label (`.k`), and baseline delta caption (`.s`).
4. **Core Analytical Sections (`section#s1..#s7`)**:
   - **Formulation & System Schematic**: Side-by-side `.grid2` panels followed by an inline horizontal SVG schematic (`viewBox="0 0 940 205"`, see [`references/svg-schematic-patterns.md`](references/svg-schematic-patterns.md)).
   - **Master Experiment Ledger (`EXP-01`..`EXP-NN`)**: Scrollable `<div class="tscroll"><table class="t">` linking experiment IDs, policy templates, CLI commands, key findings, and JSON receipt paths.
   - **Case-Level Failure & Mechanism Deep-Dive**: Concrete input/output examples plus proportionally scaled `.bars` horizontal bar charts showing threshold separation (e.g., how a normalized gate separates false-escalated items from true adversarial traps).
   - **Multi-Way Ablation Table**: Right-aligned monospace numeric columns (`td.num`), highlighting the winning configuration with `tr.highlight` and `td.best`.
   - **Claim-to-Code Verification Matrix (`.risks`)**: Maps each theoretical or patent claim element to `100% MAPPED` status badges, exact source file line ranges (`cmd/file.go:start–end`), and JSON telemetry receipts.
5. **Interactive Pipeline Explorer (`section#s8` / `.explorer`)**:
   - Clickable `.gnode[data-node="..."]` SVG stages paired with a sticky `<aside class="inspector">` driven by a `nodeData` object.

### Step 3: Enforce Zero-CDN Offline HTML Math (`<span class="math">`)

Never leave raw `$...$` LaTeX strings or `\tilde{...}` / `\mathcal{...}` macros inside HTML paragraphs or table cells. Consult [`references/html-math-cheatsheet.md`](references/html-math-cheatsheet.md) and convert every inline equation into `<span class="math">`:

- **Normalized Entropy (`\tilde{H}_m = H_m / \ln|\mathcal{V}_m|`)**:
  ```html
  <span class="math"><i>H&#771;</i><sub><i>m</i></sub> = <i>H</i><sub><i>m</i></sub> / ln|<i>V</i><sub><i>m</i></sub>|</span>
  ```
- **Complexity & Inequalities (`O(1)`, `\tilde{H}_m \ge 0.160`, `\tau = 0.16`)**:
  ```html
  <span class="math"><i>O</i>(1)</span>
  <span class="math"><i>H&#771;</i><sub><i>m</i></sub> &ge; 0.160</span>
  <span class="math">&tau; = 0.16</span>
  ```
- **Inline Code Spans**: Always use `<code>...</code>` instead of Markdown backticks (`` `...` ``).

### Step 4: Run Automated Post-Generation Verification

Before presenting the generated HTML file to the user, always run [`scripts/lint-html-artifact.py`](scripts/lint-html-artifact.py):

```bash
./scripts/lint-html-artifact.py path/to/report.html --check-gitignored
```

Fix any reported `[LATEX_MACRO]`, `[INLINE_MATH_$]`, `[MARKDOWN_BACKTICK]`, `[SVG_XML_ENTITY]`, `[BROKEN_ANCHOR_TARGET]`, `[TOC_MISSING_SCROLL_JS]`, or `[GIT_NOT_IGNORED]` findings until the script outputs `[PASS]`.
