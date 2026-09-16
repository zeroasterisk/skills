---
name: youtube-thumbnail-designer
description: Create high-impact 1920x1080 (16:9) YouTube thumbnails and technical social hero cards from real UI screenshots using a programmatic Playwright HTML/CSS canvas. Preserves 100% lossless UI screenshot clarity while layering 3D perspective depth, percentage-locked feature spotlights, subtle dot-matrix textures, and multi-stop gradient typography.
license: Apache-2.0
metadata:
  author: alanblount
  version: "1.0.0"
---

# YouTube Thumbnail & Hero Card Designer (`youtube-thumbnail-designer`)

## Golden Rule: Programmatic HTML/CSS Canvas vs. Image Diffusion

**Never feed real product UI screenshots or technical typography into generative image diffusion tools (`generate_image`) to make a thumbnail.** Diffusion models re-synthesize pixels and inevitably blur, warp, or garble small UI text, code snippets, prices, and menus.

Instead, **always render thumbnails at `1920x1080` (16:9 Full HD) using Playwright + Headless Chrome/Chromium** with lossless base64 Data-URI injection:
- Every pixel of the real product UI screenshot remains **100% sharp and authentic**.
- Web fonts (`Plus Jakarta Sans`, `Space Grotesk`, `Inter`) render with crisp vector hinting, multi-stop CSS gradients (`-webkit-background-clip: text`), and drop-shadow glows.
- CSS 3D perspective transforms (`perspective`, `rotateY`, `rotateX`), backdrop filters (`backdrop-filter: blur()`), and sub-pixel percentage callouts give broadcast-grade polish.

---

## Layout Archetypes

### Archetype 1: Asymmetric 3D Perspective UI Showcase + Feature Spotlight *(DEFAULT & RECOMMENDED)*

This is the signature high-converting technical thumbnail layout. It pairs an ultra-bold left typography stack with a 3D-tilted product UI showcase on the right and a glowing neon spotlight around the hero UI feature.

#### Mandatory Stylistic Rules for Archetype 1:
1. **Tight Horizontal Gap (No Dead Center Space)**:
   - Position the left hero column (`padding-left: 104px; width: 1050px`) and the right 3D showcase frame (`right: 42px; width: 1375px; transform: rotateY(-7deg) rotateX(2deg) rotateZ(-0.4deg)`) close together so the typography visually locks into the leading edge of the product screen.
2. **Rich Left Background (Dot-Matrix Micro-Texture + Radial Ambient Glow)**:
   - Never leave the left background as flat black or a plain solid color.
   - Layer three subtle background elements behind the left typography:
     1. **Ambient Blurred Screenshot**: A full-bleed copy of the screenshot with `filter: blur(48px) brightness(0.30) saturate(1.5)` so ambient colors match the UI.
     2. **Asymmetric Dark Scrim**: `linear-gradient(95deg, rgba(5,8,18,0.99) 0%, rgba(7,11,24,0.97) 37%, rgba(9,14,29,0.84) 47%, rgba(9,14,29,0.14) 60%, transparent 100%)` to guarantee 100% text contrast while leaving the right-side UI bright and unobstructed.
     3. **Technical Dot-Matrix Texture + Radial Glow**:
        - Radial glow: `radial-gradient(ellipse 650px 550px at 22% 42%, rgba(56, 189, 248, 0.17) 0%, rgba(168, 85, 247, 0.11) 48%, transparent 78%)`
        - Dot-grid micro-texture: `radial-gradient(rgba(148, 163, 184, 0.16) 1.25px, transparent 1.25px)` (`background-size: 24px 24px`) with a horizontal mask (`mask-image: linear-gradient(90deg, rgba(0,0,0,0.95) 0%, rgba(0,0,0,0.65) 36%, transparent 54%)`).
3. **Percentage-Locked Feature Spotlight**:
   - Lock `.showcase-container` to the exact aspect ratio of the source screenshot (`aspect-ratio: <width> / <height>`).
   - Inside `.showcase-frame`, percentage coordinates (`left: X%; top: Y%; width: W%; height: H%`) map **1:1** to the screenshot's pixels regardless of 3D rotation.
   - Frame the hero UI element (e.g., a live voice dropdown, model selector, or key chart) with a glowing cyan/violet border (`border: 3.5px solid #38bdf8; box-shadow: 0 0 38px rgba(56, 189, 248, 0.85)`) and a floating pill badge (`top: -19px; right: 16px`).
4. **Four-Tier Typography Hierarchy**:
   - **Tier 1 (Eyebrow Pill)**: Frosted pill with a glowing cyan dot and uppercase tracking (`Space Grotesk` 800, e.g., `TRAVEL UI DEMO`).
   - **Tier 2 (Primary Headline)**: Two-line `Plus Jakarta Sans` 900 display text (`114px`, `line-height: 0.96`, `letter-spacing: -0.038em`). Top line pure white (`#ffffff`); bottom line multi-stop luminous gradient (`linear-gradient(95deg, #38bdf8 0%, #a855f7 48%, #f472b6 80%, #fb7185 100%)`) with `drop-shadow(0 10px 32px rgba(168, 85, 247, 0.52))`.
   - **Tier 3 (Frosted Subtitle Card)**: Dark glass card (`border-left: 9px solid #c084fc; border-radius: 24px; padding: 26px 40px`) housing warm-to-cool gradient text (`#fde047 -> #f472b6 -> #38bdf8`, `62px` bold, e.g., `A2UI & Gemini 3.8 Live`).
   - **Tier 4 (Footer Accent)**: Audio equalizer waveform bars or concise capability tags (`Speech-to-Speech • Live Surface Streaming`).

---

### Archetype 2: Full-Bleed Dark Glass Hero Card *(Optional)*

Use when the screenshot has dense edge-to-edge visual context that looks best without 3D tilt:
- **Background**: Full-bleed screenshot shifted right (`background-size: 112% auto; background-position: 85% 22%`).
- **Left Glass Panel**: A large frosted glass container (`left: 72px; top: 72px; bottom: 72px; width: 980px; backdrop-filter: blur(22px); border-radius: 32px`) enclosing the eyebrow, headline, subtitle banner, and status dot.
- **Outer Frame**: Subtle inner neon border around the entire `1920x1080` viewport (`inset: 22px; border-radius: 28px; border: 2px solid rgba(255,255,255,0.12)`).

---

### Archetype 3: Split Code / Terminal vs. Live UI Comparison *(Optional)*

Use for developer tool demos comparing declarative code, prompts, or CLI commands against the resulting UI:
- **Left Pane (45% width)**: Dark IDE/terminal window (`#090d16`) with syntax-highlighted code or JSON/YAML schema at `24px` monospace font.
- **Right Pane (55% width)**: The rendered UI screenshot in a glowing frame.
- **Center Bridge**: Glowing circular badge (`⚡` or `→`) connecting the code line directly to the rendered UI component.
- **Top Banner**: Full-width header strip with gradient title and framework badges.

---

### Archetype 4: Centered Hero + Angled Bento Multi-Surface Grid *(Optional)*

Use when showcasing multiple screens or components (e.g., Desktop + Mobile, or Chat + Itinerary + Dashboard):
- **Top Half**: Centered pill badge + massive single-line gradient headline + subtitle.
- **Bottom Half**: 2 or 3 floating screenshot cards arranged in a perspective fan (`rotateY(8deg)`, `rotateY(0deg)`, `rotateY(-8deg)`) with overlapping depth shadows.

---

## Step-by-Step Execution Workflow

1. **Acquire & Inspect Source Screenshot**:
   - Accept a local image path (`.png`, `.jpg`, `.webp`) or download from a URL (`curl -sL <url> -o screenshot.png` or environment-specific screenshot CLI if applicable).
   - Inspect image dimensions (`python3 -c 'from PIL import Image; print(Image.open("screenshot.png").size)'` or `file screenshot.png`) and view the image (`view_file`) to identify the focal UI element for the spotlight callout.
2. **Calculate Spotlight Percentage Coordinates**:
   - Measure where the key UI feature sits horizontally (`left%`, `width%`) and vertically (`top%`, `height%`) relative to the full screenshot dimensions.
3. **Render via Playwright (`scripts/render_thumbnail.mjs`)**:
   - Run the bundled generator script or execute a customized Node.js Playwright script targeting headless Chrome/Chromium (`--no-sandbox`).
   - Example invocation of the bundled CLI helper:
     ```bash
     node scripts/render_thumbnail.mjs \
       --screenshot /path/to/screenshot.png \
       --eyebrow "TRAVEL UI DEMO" \
       --title-top "Audio with" \
       --title-gradient "Generative UI" \
       --subtitle "A2UI & Gemini 3.8 Live" \
       --footer "Speech-to-Speech • Live Surface Streaming" \
       --badge "GEMINI 3.8 LIVE VOICE" \
       --spotlight "53.8,23.6,30.8,24.5" \
       --output youtube_thumbnail.png
     ```
4. **Visual Verification Gate**:
   - **Always** inspect the generated `youtube_thumbnail.png` using `view_file` before presenting it to the user.
   - Verify:
     - No text overlaps awkwardly with bright background elements.
     - The gap between left typography and right 3D screen feels tight and intentional.
     - The spotlight box frames the intended UI feature without clipping its label.
5. **Deliver & Share**:
   - Provide the local file path and embed the image in any markdown artifact.
   - If the user's workspace has an image hosting or screenshot sharing CLI configured, optionally upload and return the shareable URL.
