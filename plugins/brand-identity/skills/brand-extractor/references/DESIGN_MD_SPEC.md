# Google Labs DESIGN.md Alpha Specification Reference

This document outlines the normative structure, typed token groups, token aliasing syntax, and Markdown section hierarchy for `DESIGN.md` files adhering to the Google Labs Design Alpha specification.

---

## 1. Structure Overview

A conformant `DESIGN.md` file consists of two primary parts:
1. **Machine-Readable YAML Frontmatter** (delimited by `---`): Contains typed, structured design system tokens intended for direct programmatic ingestion by AI coding agents and design tools.
2. **Human-Readable Markdown Body**: Follows immediately after the closing `---` delimiter. Contains prose guidelines, aesthetic explanations, visual hierarchy rules, and implementation patterns organized into standardized `##` (Level 2) headings.

---

## 2. YAML Frontmatter Schema

```yaml
---
version: 1.0
colors:
  primary: '#1D54D8'
  background: '#F8FAFC'
  surface: '#FFFFFF'
  text: '#475569'
  success: '#10B981'
  warning: '#F59E0B'
  error: '#EF4444'
typography:
  headline:
    fontFamily: 'Inter, sans-serif'
    fontWeight: 700
    letterSpacing: '-0.02em'
  body:
    fontFamily: 'Inter, sans-serif'
    fontWeight: 400
    lineHeight: 1.5
spacing:
  xs: '4px'
  sm: '8px'
  md: '16px'
  lg: '24px'
  xl: '32px'
rounded:
  sm: '4px'
  md: '8px'
  lg: '16px'
  full: '9999px'
components:
  card:
    backgroundColor: '{colors.surface}'
    borderRadius: '{rounded.lg}'
    padding: '{spacing.lg}'
  button_primary:
    backgroundColor: '{colors.primary}'
    textColor: '#FFFFFF'
    borderRadius: '{rounded.full}'
---
```

### Token Groups

| Group | Type | Description |
|---|---|---|
| `version` | string / number | Specification version (e.g. `1.0`). |
| `colors` | key-value map | Hex codes (`#RRGGBB`). MUST include `primary`. Recommended: `background`, `surface`, `text`. |
| `typography` | mapping | Object per typographic role (`headline`, `body`, etc.) specifying font family, weights, and scale. |
| `spacing` | key-value map | Scale tokens (`px`, `rem`) for layout, padding, and gaps. |
| `rounded` | key-value map | Border radius values (`px`, `rem`, or full). |
| `components` | nested map | Composite component definitions using token aliasing. |

### Token Aliasing (Cross-Referencing)
Tokens may reference other tokens using the curly-brace path syntax:
```yaml
backgroundColor: "{colors.surface}"
borderRadius: "{rounded.md}"
```

---

## 3. Standard Markdown Body Sections

The Markdown body must use `##` (Level 2) headings for all primary sections. Document title (`# Title`) is optional and ignored by automated token parsers.

### Ordered Section Hierarchy

1. **`## Overview`**: High-level summary of the brand's visual identity, ethos, and design philosophy.
2. **`## Colors`**: Detailed prose explaining the color architecture, contrast ratios, and semantic usage rules.
3. **`## Typography`**: Hierarchy, font pairings, typographic scales, line heights, and Google Font fallbacks.
4. **`## Layout`**: Grid system, container max-widths, column layouts, and whitespace distribution.
5. **`## Elevation & Depth`**: Shadow formulas, elevation layers, glassmorphism, and border treatments.
6. **`## Shapes`**: Corner radius rules, geometry, tactile feel, and container curvature.
7. **`## Components`**: Core UI patterns (cards, buttons, input fields, navigation bars).
8. **`## Do's and Don'ts`**: Concrete, actionable guidance on what patterns to follow and what anti-patterns to avoid.

---

## 4. Font Fallback Rules

Commercial proprietary typefaces (e.g., *Helvetica Neue*, *Circular*, *Futura*) cannot be fetched directly from public Google Font CDNs. When specifying fonts, always provide open-source Google Font equivalents:
- **Circular / Proxima Nova** $ightarrow$ **Plus Jakarta Sans** or **Inter**
- **Helvetica / Arial** $ightarrow$ **Inter** or **Roboto**
- **Futura** $ightarrow$ **Outfit** or **Urbanist**
- **GT America / DIN** $ightarrow$ **Space Grotesk** or **DM Sans**
