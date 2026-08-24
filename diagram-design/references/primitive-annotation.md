# Annotation Callout (italic aside)

Use for editorial asides — the "pointer" that marks a detail without competing with the primary diagram grammar. Think marginalia: *"structure IS the index"*, *"zero configuration, managed scaling"*.

## Grammar

```svg
<!-- 1. Italic Google Sans Text -->
<text x="904" y="36" fill="#1f1f1f" font-size="13" font-style="italic"
      font-family="'Google Sans Text', 'Google Sans', sans-serif" text-anchor="end">zero configuration, managed scaling</text>
<!-- 2. Dashed Bézier leader -->
<path d="M 820 44 Q 700 84 520 216" fill="none"
      stroke="rgba(31,31,31,0.40)" stroke-width="1" stroke-dasharray="4,3"/>
<!-- 3. Landing dot -->
<circle cx="520" cy="216" r="2.5" fill="#0b57d0"/>
```

## Rules
- Italic Google Sans Text / Roboto signals "editorial voice" against the diagram's structured body.
- Dashed path (`stroke-dasharray="4,3"`) distinguishes the callout leader from primary flow arrows (which are solid).
- Place callouts in margins (top-right, bottom-left). Never inside the active diagram area.
- Max 2 callouts per diagram. More becomes commentary, not signal.

## Colors

| Intent | Text | Leader | Dot |
|---|---|---|---|
| Neutral aside | ink `#1f1f1f` | `rgba(31,31,31,0.40)` | `#444746` |
| Focal / accent | Google Blue `#0b57d0` | `rgba(11,87,208,0.40)` | `#0b57d0` |
| Tertiary (muted) | muted `#444746` | `rgba(31,31,31,0.25)` | `#747775` |

## Anti-patterns
- Solid arrow leader (reads as a flow arrow).
- Callouts crossing primary arrows / lifelines — offset to a clear margin.
- Using a callout to label something the diagram should label directly — put the label on the element.
