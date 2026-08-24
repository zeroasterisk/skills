# Style Guide — Material Design 3 (Google Edition)

**The single source of truth for colors, typography, shapes, and tokens.** Every diagram draws from this — not from ad-hoc hex values inlined in other reference files. If you want to change the visual skin of Diagram Design, change this file.

Default skin is **Material Design 3 with Subtle Google Colors** — Google Grey surfaces (`#f8f9fa` surface, `#f1f3f4` surface container, `#1f1f1f` dark surface), Google Grey ink (`#1f1f1f` light, `#e3e3e3` dark), Google Blue accent (`#0b57d0` light / `#a8c7fa` dark), and semantic Google accents (Google Red, Google Yellow/Amber, Google Green). It features M3 shape geometry (distinctive 12px rounded rectangles for nodes and cards, 8px for chips/tags, 16px for containers) and the official Google Sans / Roboto font stack.

To generate your own from a website URL or custom brand, see [`onboarding.md`](onboarding.md).

---

## Tokens

### Semantic roles

Every token is referred to by **semantic role**, not by its hex value. Type references (`type-*.md`) and SKILL.md say `accent`, `paper`, `ink`, `muted`, etc.

| Role | Purpose | Default (light) | Default (dark) |
|---|---|---|---|
| `paper` | Page background, default canvas surface | `#f8f9fa` (Google Grey 50 / M3 Surface) | `#1f1f1f` (Google Dark Surface / M3 Dark Surface) |
| `paper-2` | Container background, secondary card fill | `#f1f3f4` (Google Grey 100 / Surface Container Low) | `#28292a` (Google Grey 800 / Surface Container Low) |
| `paper-3` | Tertiary fill, nested card containers | `#e8eaed` (Google Grey 200 / Surface Container) | `#2d2f31` (Google Grey 750 / Surface Container) |
| `ink` | Primary text, primary stroke | `#1f1f1f` (Google Grey 900 / On-Surface) | `#e3e3e3` (Google Grey 100 / On-Surface) |
| `muted` | Secondary text, default arrow stroke | `#444746` (Google Grey 700 / On-Surface Variant) | `#c4c7c5` (Google Grey 300 / On-Surface Variant) |
| `soft` | Sublabels, boundary labels, tertiary text | `#747775` (Google Grey 500 / Outline) | `#8e918f` (Google Grey 400 / Outline) |
| `rule` | Hairline borders, subtle dividers | `rgba(31,31,31,0.12)` (Outline Variant) | `rgba(227,227,227,0.12)` (Outline Variant) |
| `rule-solid` | Stronger borders, baselines, card outlines | `#c4c7c5` (Google Grey 300 / Outline Variant solid) | `#444746` (Google Grey 600 / Outline Variant solid) |
| `accent` | Focal / 1–2 max per diagram (Google Blue) | `#0b57d0` (Google Blue 700 / M3 Primary) | `#a8c7fa` (Google Blue 200 / M3 Dark Primary) |
| `accent-tint` | Fill for accent-bordered focal boxes | `rgba(11,87,208,0.08)` (M3 Primary Container tint) | `rgba(168,199,250,0.12)` (M3 Dark Primary Container tint) |
| `link` | HTTP/API calls, external arrows | `#0b57d0` (Google Blue) | `#a8c7fa` (Google Blue 200) |

> **Google Brand Palette Integration:**
> In addition to the primary Google Blue accent, 3 semantic Google brand colors are available for domain-specific meanings (1 focal color per diagram):
> - **Google Red** (`#d93025` light / `#f28b82` dark, tint `rgba(217,48,37,0.08)`): Security boundaries, failures, policy divergence, critical alerts.
> - **Google Amber / Yellow** (`#e37400` light / `#fdd663` dark, tint `rgba(227,116,0,0.08)`): Queues, bottlenecks, stages, warning thresholds.
> - **Google Green** (`#1e8e3e` light / `#81c995` dark, tint `rgba(30,142,62,0.08)`): Databases, canonical storage, passing states, verified outputs.

### Inversion rule (light → dark)

Any `rgba(31,31,31, X)` in light becomes `rgba(227,227,227, X)` in dark. Same opacities, RGB flipped. The primary Google Blue shifts from `#0b57d0` to `#a8c7fa` (M3 Dark Primary tone 80) to preserve high legibility and contrast against dark surfaces.

### Series palette (multi-series chart types only)

The 5-color Google brand palette tuned for Material Design 3 data visualization (radar, bar, line, scatter charts):

| Token | Light | Dark | Notes |
|---|---|---|---|
| `series-1` | `#1a73e8` (Google Blue) | `#8ab4f8` | Series 1 / Primary metric |
| `series-2` | `#1e8e3e` (Google Green) | `#81c995` | Series 2 / Secondary metric |
| `series-3` | `#e37400` (Google Amber) | `#fdd663` | Series 3 / Tertiary metric |
| `series-4` | `#d93025` (Google Red) | `#f28b82` | Series 4 / Quaternary metric |
| `series-5` | `#9334e6` (Google Purple) | `#c58af9` | Series 5 / Quinary metric |

Fills sit at `0.16` opacity in light, `0.20` in dark; strokes use the full solid color. **Don't backfill these tokens to non-chart types** — architecture, swimlane, etc. continue to use muted-ink variants.

### Terminal skin (opt-in alternate)

A self-contained palette for the terminal-window primitive (CLI-chrome register):

| Token | Hex | Purpose |
|---|---|---|
| `terminal-page` | `#121316` | Page background behind the window |
| `terminal-paper` | `#1e1f24` | Window body, node fill (Google Cloud Shell dark surface) |
| `terminal-bar` | `#282a30` | Titlebar strip |
| `terminal-border` | `#3c404b` | Window border, hairlines |
| `terminal-ink` | `#e3e3e3` | Primary text, primary stroke (Google Grey 100) |
| `terminal-muted` | `#9aa0a6` | Secondary text, sublabels, ring stroke |
| `terminal-soft` | `#5f6368` | Tertiary — inactive dots, spokes |
| `terminal-accent` | `#8ab4f8` | The one accent — prompt sign, focal station (Google Blue 300) |
| `terminal-accent-tint` | `rgba(138,180,248,0.12)` | Fill for accent-bordered boxes |

---

## Typography

Material Design 3 typography hierarchy with Google Sans & Roboto:

| Role | Family | Size | Weight | Usage |
|---|---|---|---|---|
| `title` | Google Sans, Roboto | 1.75rem | 500 | Page H1 / M3 Headline |
| `node-name` | Google Sans Text, Google Sans, Roboto | 12px | 500 | Human-readable node labels (M3 Title Small / Label Large) |
| `sublabel` | Roboto Mono, Google Sans Mono | 9px | 400 | Port, protocol, URL, field type (M3 Body Small mono) |
| `eyebrow` | Google Sans Text, Roboto Mono | 7–8px | 500 | Type tags, section overlines, axis labels (tracked 0.12em, uppercase) |
| `arrow-label` | Roboto Mono | 8px | 500 | Arrow annotations / protocol verbs (tracked 0.05em) |
| `callout` | Google Sans Text, Roboto | 13–14px | 400 | Editorial asides / marginalia only (*italic*) |

### Font stack

```html
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Google+Sans:wght@400;500;700&family=Google+Sans+Text:ital,wght@0,400;0,500;0,700;1,400&family=Roboto+Mono:wght@400;500;600&family=Roboto:ital,wght@0,400;0,500;0,700;1,400&display=swap" rel="stylesheet">
```

---

## Shape, Radius, and Stroke (Material Design 3)

| Token | Value | Use |
|---|---|---|
| `radius-xs` | `4` | Small badges, code chips (`rx="4"`) |
| `radius-sm` | `8` | Inner chips, compact tags (`rx="12"`) |
| `radius-md` | `12` | Standard node boxes, card items (`rx="12"` — signature M3 shape) |
| `radius-lg` | `16` | Group containers, zone boundaries (`rx="16"`) |
| `radius-pill` | `9999` | Status pills, filter chips (`rx="10"` on h=20) |
| `stroke-thin` | `0.8` | Tag-box outlines, leaf nodes |
| `stroke-default` | `1` | Standard node and connector strokes |
| `stroke-strong` | `1.5` | Emphasis strokes, active paths |
| `grid` | `4` | Every coord, size, and gap is divisible by 4 (hard rule) |

---

## Node type → treatment

Semantic role combinations — reference these by name in type specs.

| Type | Fill | Stroke | Radius |
|---|---|---|---|
| `focal` (1–2 max) | `accent-tint` (`rgba(11,87,208,0.08)`) | `accent` (`#0b57d0`) | `rx="12"` |
| `backend` / `service` | `#ffffff` (light) / `#28292a` (dark) | `rule-solid` (`#c4c7c5`) | `rx="12"` |
| `store` / `database` | `rgba(30,142,62,0.06)` (Google Green tint) | `#1e8e3e` (Google Green) or `muted` | `rx="12"` |
| `external` / `cloud` | `rgba(11,87,208,0.04)` (Google Blue tint) | `rgba(11,87,208,0.35)` | `rx="12"` |
| `input` / `user` | `rgba(68,71,70,0.06)` / `#f1f3f4` | `soft` (`#747775`) | `rx="12"` |
| `optional` / `async` | `rgba(31,31,31,0.02)` | `rgba(31,31,31,0.25)` dashed `4,3` | `rx="12"` |
| `security` / `boundary` | `rgba(217,48,37,0.05)` (Google Red tint) | `rgba(217,48,37,0.50)` dashed `4,4` | `rx="12"` |

---

## Customizing the skin

Four options:

1. **Run onboarding** — see [`onboarding.md`](onboarding.md). Drop a URL; the skill extracts the palette + fonts and rewrites this file.
2. **Edit by hand** — change the hex values in the tables above.
3. **Brand handoff** — paste your existing design-token JSON into a new section here and map its tokens to the semantic roles above.
4. **Client profiles** — save and switch named skins, or bind one to a project, using [`profiles.md`](profiles.md).

### Constraints (don't break these)

- **Contrast**: `ink` must hit WCAG AA on `paper`. `muted` must hit AA on `paper` for 11px+ text.
- **One primary accent**: pick one color for `accent` (default: Google Blue `#0b57d0`). Two primary accents erase the focal signal.
- **Material Design 3 Corner Radii**: Use `rx="12"` for standard node boxes and cards, `rx="12"` for sub-elements/chips, `rx="16"` for containers.
- **Google Sans + Roboto Typography**: Google Sans for titles/names, Roboto for body/sublabels, Roboto Mono for technical labels.
