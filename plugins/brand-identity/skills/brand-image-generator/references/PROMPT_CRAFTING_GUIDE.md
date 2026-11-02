# Brand-Conditioned Prompt Crafting Guide

This reference explains how to translate tokens from a `DESIGN.md` file (colors, typography, spacing, rounded, elevation) into generative image prompts for diffusion and multimodal AI models (Gemini Nano Banana / Imagen 3 / FLUX / Midjourney).

---

## 1. Core Principle: Token-to-Sensory Mapping

AI image generation models do not render raw CSS rules directly. Instead, design tokens must be mapped into **sensory, photographic, and structural directives**:

| Design Token | CSS Meaning | Prompt Directive Mapping |
|---|---|---|
| `colors.primary` | Primary interaction color | Dominant accent lighting, hero element coloration, focal point tint |
| `colors.background` | Canvas background | Environmental setting, studio backdrop tone, architectural wall color |
| `colors.surface` | Card/elevated container | Material surface (matte porcelain, brushed metal, frosted acrylic) |
| `rounded` | Border radius scale | Edge curvature, soft tactile beveling vs. razor-sharp geometric cuts |
| `elevation` | Box-shadow / z-index | Lighting angle, ambient occlusion, diffuse drop shadows, multi-layer depth |
| `typography` | Font family & weight | Graphic overlay styling, editorial hierarchy, layout structural discipline |
| `tone` | Brand mood keywords | Color grading, emotional atmosphere, camera choice, composition density |

---

## 2. Color Palette Anchoring

When specifying hex colors in image prompts:
1. **Name + Hex Pair**: Pair evocative color descriptors with exact hex codes:
   * *"Anchored by vibrant cobalt action blue (#1D54D8) against a ghost slate canvas (#F8FAFC)..."*
2. **Role Distribution**: Maintain a 60-30-10 rule:
   * **60%**: Background / canvas neutrality (`colors.background`)
   * **30%**: Secondary surfaces, container cards (`colors.surface`)
   * **10%**: High-contrast focal accents (`colors.primary`)
3. **Lighting Harmony**: Direct the lighting engine to reflect the palette:
   * *"Soft ambient lighting subtly tinted with #1D54D8 rim illumination..."*

---

## 3. Physicalizing Elevation and Shapes

### Elevation
Translate box-shadow tokens into light diffusion:
- **Subtle Elevation** (`0 4px 12px rgba(0,0,0,0.05)`): *"Gentle floating layers with soft, wide ambient occlusion and diffuse underside shadowing."*
- **High Elevation** (`0 20px 40px rgba(0,0,0,0.12)`): *"Pronounced vertical separation, deep dimensional casting, floating acrylic panels with dramatic depth of field."*

### Corner Radii
- **Sharp (`rounded: 0px` / Brutalist)**: *"Strict monolithic angularity, razor-sharp 90-degree corners, brutalist architectural planes."*
- **Moderate (`rounded: 8px - 16px` / Modern UI)**: *"Smooth rounded corners (16px curvature), approachable modern tactile surfaces."*
- **Full (`rounded: 9999px` / Pill-shaped)**: *"Pill-shaped organic geometries, continuous curvature, tactile pebble-smooth edges."*

---

## 4. Asset Archetypes

### 1. Editorial Hero Banner (`--type hero`)
- **Aspect Ratio**: 16:9 or 3:2
- **Focus**: Wide canvas, negative space for typography overlays, aspirational scene setting.
- **Lighting**: Soft diffuse studio or golden-hour volumetric beam.

### 2. Digital UI Interface Preview (`--type ui`)
- **Aspect Ratio**: 16:9 or 4:3
- **Focus**: Floating cards, crisp typography hierarchy, vector precision, elevated components.
- **Camera**: Slightly angled isometric or clean orthographic top-down.

### 3. Tactile Brand Icon / Motif (`--type icon`)
- **Aspect Ratio**: 1:1
- **Focus**: Single central symbol, tactile 3D material (ceramic, frosted glass, matte silicone).
- **Lighting**: Macro studio setup, rim light, soft specular reflections.

### 4. Editorial Lifestyle Photography (`--type lifestyle`)
- **Aspect Ratio**: 16:9 or 1:1
- **Focus**: Human or environmental context using the brand's products or design ethos.
- **Camera**: 50mm f/1.8, natural grain, authentic non-stock aesthetic.
