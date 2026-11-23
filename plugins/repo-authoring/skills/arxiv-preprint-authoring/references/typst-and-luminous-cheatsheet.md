# Typst (`@preview/arkheion:0.1.2`) and Luminous Graphviz Cheatsheet

This reference prevents common compilation errors when generating `@preview/arkheion:0.1.2` Typst manuscripts and Luminous Graphviz `.dot` figures for `../syntaxis`.

---

## 1. Typst Math Mode Rules

1. **Quote Multi-Letter Identifiers:**
   - In Typst math mode (`$...$`), consecutive unquoted letters are parsed as multiplication of single-letter variables (`$FVR$` renders as $F \cdot V \cdot R$).
   - Always quote multi-letter variable or metric names: `$"FVR"$`, `$"SIR"$`, `$"BT"$`, `$"PASS"$`, `$S_"max"$`, `$P_"free"$`, `$P_"struct"$`, `$T_"prompt"$`.
2. **Use Native Typst Math Symbols (Never LaTeX Macros or Invalid Symbol Names):**
   - `\times` $\to$ `times` (`$2 times 2$`, `$3.57 times$`)
   - `\to` / `\rightarrow` $\to$ `arrow.r` (`$V: cal(W) arrow.r [0, 100]$`)
   - `\in` $\to$ `in` (`$x in cal(X)$`)
   - `\mathcal{T}` $\to$ `cal(T)`
   - `\mathbb{I}` $\to$ `bb(I)`
   - `\oplus` / `plus.circle` $\to$ `plus.o` (`$a plus.o b$`; note: `plus.circle` is invalid in Typst)
   - `\cap` / `sect` $\to$ `inter` (`$A inter B$`; note: `sect` is invalid in Typst)
   - `\cup` $\to$ `union` (`$A union B$`)
   - `\emptyset` $\to$ `emptyset`
   - `\sim` $\to$ `tilde.op`
   - `\frac{a}{b}` $\to$ `frac(a, b)`
3. **Escape Dollar Signs in Prose/Tables:**
   - Write `\$0.000240` for currency literals so Typst does not open an unclosed math block.

---

## 2. Typst Booktabs Tables

Never pass `right` or `left` inside `columns: (...)`! In Typst `table(...)`:
- `columns:` accepts only track sizes (`auto`, `1fr`, `2cm`).
- `align:` accepts column alignments (`left`, `center`, `right`).

```typst
#figure(
  table(
    columns: (auto, auto, auto, auto),
    align: (left, center, right, right),
    stroke: none,
    table.hline(stroke: 0.75pt),
    [*Condition*], [*Tool*], [*Score↑*], [*Latency↓*],
    table.hline(stroke: 0.4pt),
    [A (Control)], [No], [85.0%], [33.38s],
    [C (Script)], [*Yes*], [*100.0%*], [*27.47s*],
    table.hline(stroke: 0.75pt),
  ),
  caption: [Booktabs table with separated columns and align tuples.],
) <tbl-example>
```

---

## 3. Luminous Graphviz (`.dot`) Semantic Classes

When authoring `figures/*.dot` for Syntaxis:
- **Never hardcode hex colors (`#RRGGBB`), `fillcolor`, or `fontname` in `.dot` files.**
- Assign semantic `class` attributes that `luminous.gvpr` maps automatically to light/dark palettes:

| Semantic `class` | Visual Role in Luminous Theme | Typical Use in Preprint Figures |
| :--- | :--- | :--- |
| `primary` | Deep blue fill (`#0e57d0`), white text | Active closed-loop executor / main pipeline path |
| `emphasis` | Soft blue container (`#d3e3fd`), dark navy text | Highlighted treatment condition (`Condition B`) |
| `accent` | Cyan container (`#dcf1ff`), dark text | Deterministic validation oracle $V$ (`class="accent code"`) |
| `positive` | Green container (`#daf9d4`), emerald text | Verified `100% PASS` / exit code `0` outcome |
| `warning` | Amber container (`#ffe2be`), brown text | Unverified artifact / deliberation loop / diagnostic feedback |
| `error` | Rose container (`#ffdeec`), crimson text | Failed condition / latency explosion (`3.57x slowdown`) |
| `muted` | Neutral surface (`#faf9f9`), grey text | Disabled tool / static linter grade |
| `terminal` | Slate container (`#e8eef6`) | Task input / initial workspace fixture $W_0$ |
| `store` | Cylinder/storage styling | Hermetic sandbox `/tmp/ablation_*` & checkpoint store |
| `code` | Monospace font (`Google Sans Code`) | Combine with colour class: `class="accent code"` |
