---
name: brand-extractor
description: Crawls target websites, captures high-fidelity viewport and full-page screenshots, extracts computed CSS tokens from the DOM, and synthesizes structured Brand DNA and a DESIGN.md specification adhering strictly to the Design Alpha spec. Use when analyzing an existing website's visual brand identity, extracting color palettes, typography, spacing, and shape tokens, or generating a DESIGN.md design system.
license: Apache-2.0
compatibility: Requires python3 and google-chrome or chromium for automated browser crawl.
metadata:
  author: ghchinoy
  version: "1.0.0"
---

# Brand Extractor

Extracts core visual brand identity, design tokens, and structured design systems from live websites and web sources, translating real-world interfaces into a formal Google Labs `DESIGN.md` Alpha specification and `brand_dna.json`.

---

## When to Use This Skill

- Extracting the design system and brand identity of an existing website or web app.
- Capturing high-fidelity full-page and viewport screenshots for multimodal visual analysis.
- Extracting computed CSS styles and `:root` CSS custom properties (`--color-*`, `--spacing-*`, `--radius-*`, typography) as ground truth tokens.
- Synthesizing a machine-readable `DESIGN.md` specification adhering strictly to the Google Labs Design Alpha spec.
- Preparing brand context and design tokens for downstream image generation (via `brand-image-generator`).

---

## Progressive Disclosure & Reference Architecture

- **`DESIGN.md` Alpha Specification**: Read [`references/DESIGN_MD_SPEC.md`](references/DESIGN_MD_SPEC.md) for normative token schemas, typed token groups, aliasing syntax, and required `##` Markdown sections.
- **Brand DNA Schema**: Read [`references/BRAND_DNA_SCHEMA.md`](references/BRAND_DNA_SCHEMA.md) for the structured JSON schema of `brand_dna.json`.
- **Extraction Script**: Run `scripts/extract_brand_dna.py` to capture screenshots and extract computed CSS variables.
- **Validation Script**: Run `scripts/validate_design_md.py` to enforce strict conformance of generated `DESIGN.md` files.
- **Templates**:
  - [`assets/design_md.template`](assets/design_md.template) — Conformance template for `DESIGN.md`.
  - [`assets/brand_dna.template.json`](assets/brand_dna.template.json) — Schema template for `brand_dna.json`.

---

## Procedural Workflow

### Step 1: Execute Automated Web Extraction

Run `scripts/extract_brand_dna.py` against the target URL:

```bash
scripts/extract_brand_dna.py --url https://example.com --output ./brand-output
```

The script performs the following operations:
1. Launches headless Chrome (`1920x1080` viewport), prepares the page by dismissing cookie banners/modals, and scrolls to trigger lazy loading.
2. Captures `source_screenshot_1_viewport.png` and `source_screenshot_1_full.png`.
3. Injects DOM extraction JavaScript to record computed styles (`fontFamily`, `fontSize`, `fontWeight`, `lineHeight`, `color`, `backgroundColor` on `h1`, `h2`, `p`, `body`) and `:root` CSS custom properties into `extracted_css_tokens.json`.
4. Discovers candidate internal links (About, Pricing, Product) and captures secondary page screenshots (`source_screenshot_2_*.png`).

*Fallback*: If headless Chrome is unavailable, the script falls back to HTTP fetching and CSS extraction via `BeautifulSoup`.

### Step 2: Synthesize Brand DNA (`brand_dna.json`)

Analyze the captured visual screenshots alongside `extracted_css_tokens.json`:
- **Colors**: Map extracted hex values and dominant visual cues to primary, background, surface, text, and accent roles.
- **Fonts**: Identify headline and body typefaces and classify typography family (e.g. Neo-Grotesque Sans-serif, Humanist Sans, Serif).
- **Tone**: Select 3-5 evocative tone keywords (e.g., `["minimalist", "kinetic", "austere"]`).
- **Summary**: Draft a concise, authoritative paragraph defining the brand's aesthetic positioning.

Save to `./brand-output/brand_dna.json` conforming to [`references/BRAND_DNA_SCHEMA.md`](references/BRAND_DNA_SCHEMA.md).

### Step 3: Synthesize `DESIGN.md` (Alpha Spec)

Generate `DESIGN.md` adhering strictly to the Google Labs Design Alpha specification:

1. **YAML Frontmatter (Delimited by `---`)**:
   - `version: 1.0`
   - `colors`: Semantic hex map containing at minimum `primary`, `background`, `surface`, and `text`.
   - `typography`: Font family, weights, and scale for headlines and body.
   - `spacing`: Scale tokens (e.g., `sm: 4px`, `md: 8px`, `lg: 16px`).
   - `rounded`: Corner radius tokens (e.g., `sm: 4px`, `md: 8px`, `full: 9999px`).
   - `components`: Core component token definitions.

2. **Standardized Markdown Sections (Strict `##` headings)**:
   - `## Overview`: Visual identity summary.
   - `## Colors`: Palette roles and usage rules.
   - `## Typography`: Type scale, hierarchy, and font fallbacks.
   - `## Layout`: Grid, container widths, and whitespace strategy.
   - `## Elevation & Depth`: Shadow diffusion, surface layers, and borders.
   - `## Shapes`: Border radii and geometric treatment.
   - `## Components`: Key UI component patterns.
   - `## Do's and Don'ts`: Explicit design dos and don'ts.

### Step 4: Validate `DESIGN.md`

Always validate the generated `DESIGN.md` file using the bundled validator:

```bash
scripts/validate_design_md.py ./brand-output/DESIGN.md
```

Ensure 0 errors before proceeding.

### Step 5: Downstream Image Generation Hand-off

Once `DESIGN.md` and `brand_dna.json` are validated, transition to the `brand-image-generator` skill (`plugins/brand-identity/skills/brand-image-generator`) to produce brand-aligned visual assets, marketing graphics, or UI mockups.
