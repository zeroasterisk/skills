# Diagram House Style

Every article needs a hero image plus one diagram per numbered section. Keeping the visual style consistent across every piece ensures the series is instantly recognizable in developer feeds.

---

## The Look: Hand-Drawn Whiteboard Sketch (Dark Mode)

- **Canvas:** Charcoal near-black background (`#0e1116`).
- **Linework:** Off-white, slightly wobbly hand-sketched strokes, styled like an engineer drawing on a dark digital whiteboard. Excalidraw dark theme is the reference standard.
- **Accents:** A single warm-yellow or Google-blue accent used sparingly to highlight the critical node, human-in-the-loop, or data flow boundary.
- **Typography:** Neat handwritten-style marker labels. High contrast and easily legible on mobile screens.
- **Composition:** Generous negative space, uncluttered. No 3D gloss, no photorealism, no heavy gradients.

---

## Diagram Types (Match to Section Purpose)

- **Loop & Cycle:** For self-improving loops, feedback flywheels, or iterative retry mechanisms.
- **Architecture & Data Flow:** For event buses, state machines, or append-only log to model pipelines.
- **Failure Boundary / Layer Stack:** For showing what security or validation checks stop at each layer (e.g., Model Armor vs Agent Gateway).
- **Decision Tree:** For guiding the reader through selecting the right design pattern.

---

## Prompt Template (For Image Generation Tools)

```text
A hand-drawn sketch-style technical diagram in dark mode, Excalidraw dark theme. Charcoal near-black background (#0e1116). [DESCRIBE the nodes / flow: shapes, labels, arrows]. Rough hand-sketched rounded rectangles with slightly wobbly off-white strokes, hand-drawn arrows with sketchy arrowheads, neat handwritten marker labels. One warm-yellow accent on [the key node]. Hand-lettered title at top: "[TITLE]". Clean, uncluttered, generous negative space, engineer-at-a-dark-whiteboard aesthetic. Not photorealistic, no gradients.
```

- **Aspect Ratio:** 16:9 for hero image and inline section diagrams.
- **Resolution:** 2K.

---

## Alternatives & Fallbacks

- If image generation is unavailable, use the local `diagram-design` skill to generate standalone Material Design 3 HTML/SVG dark-mode diagrams.
- Verify every label is legible. If a generated image garbles a word, regenerate with simpler text.
- Store all source images in the article's Google Drive assets folder and include the folder link at the top of the working draft.
