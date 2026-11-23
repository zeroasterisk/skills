---
name: arxiv-preprint-authoring
description: Outline, write, package, and deterministically validate arXiv-style academic preprints (Markdown, @preview/arkheion:0.1.2 Typst, CSV telemetry, and Luminous Graphviz diagrams) following the arXiv:2610.28380 empirical narrative blueprint and Syntaxis house-style clarity rules. Use when asked to write a research paper, academic preprint, ablation study manuscript, or Syntaxis publication package.
license: Apache-2.0
compatibility: Requires python3. Optional typst and graphviz (dot, gvpr) for PDF and figure compilation.
metadata:
  author: ghchinoy
  version: "1.0.0"
---

# arXiv Preprint Authoring & Assessment (`arxiv-preprint-authoring`)

Author, outline, and deterministically validate publication-ready academic preprints (`docs/preprint/`) designed for both standalone `@preview/arkheion:0.1.2` Typst PDF compilation and direct ingestion by the **Syntaxis** publication orchestration engine (`../syntaxis`).

This skill combines three pillars:
1. **Empirical Narrative Architecture (`arXiv:2610.28380` Blueprint):** Structured 6-section + 2-appendix empirical systems paper progression where every claim binds to a formal equation, a directional scoreboard table (`↑` / `↓`), or a multi-stage architecture diagram.
2. **House-Style & Clarity Gate:** Active-voice technical prose with named actors, zero em-dashes (`—`), zero throat-clearing openers, and zero lazy binary-contrast clichés (`"not X, but Y"`).
3. **Closed-Loop Deterministic Oracle (`scripts/validate_preprint.py`):** Executable validator that audits section completeness, prose clarity, CSV-to-table alignment, semantic Luminous Graphviz `.dot` classes, and `@preview/arkheion:0.1.2` Typst compilation.

---

## Reference, Asset & Script Files (Progressive Disclosure)

- [`assets/paper-skeleton.md`](assets/paper-skeleton.md) — Starter Markdown manuscript following the `arXiv:2610.28380` section progression, formal notation blocks, directional tables, Author Contributions, and Appendices A & B.
- [`assets/paper-skeleton.typ`](assets/paper-skeleton.typ) — Starter `@preview/arkheion:0.1.2` Typst manuscript with booktabs tables (`stroke: none`, `table.hline`), native Typst math, and appendix blocks.
- [`assets/fig-paradigm-skeleton.dot`](assets/fig-paradigm-skeleton.dot) — Semantic Luminous Graphviz starter comparing baseline, static/heuristic, and closed-loop paradigms using `class` attributes (`primary`, `emphasis`, `accent`, `positive`, `warning`, `error`, `muted`, `code`).
- [`references/narrative-blueprint-2610-28380.md`](references/narrative-blueprint-2610-28380.md) — Detailed section-by-section rhetorical and structural blueprint modeled on *Object-Oriented Harness* (`arXiv:2610.28380`).
- [`references/house-style-and-clarity-gate.md`](references/house-style-and-clarity-gate.md) — Editorial rules enforcing zero em-dashes, active voice with named actors, Grade 12–14 readability calibration, and concrete claim-to-evidence binding.
- [`references/typst-and-luminous-cheatsheet.md`](references/typst-and-luminous-cheatsheet.md) — Typst math identifier quoting rules (`$"FVR"$`), booktabs table syntax, and the `gvpr -c -f luminous.gvpr -a light` diagram rendering pipeline.
- [`scripts/validate_preprint.py`](scripts/validate_preprint.py) — Deterministic validation oracle checking all 6 preprint quality pillars (exit code `0` on `100/100 PASS`).

---

## Workflow

### Step 1: Inventory Empirical Data & Outlining (`docs/preprint/`)

Before drafting prose, inventory all experimental artifacts and create the target directory layout:

```text
docs/preprint/
├── README.md                   # Reproducibility & Syntaxis CLI ingestion commands
├── paper.md                    # Primary Syntaxis-compliant Markdown manuscript
├── paper.typ                   # Companion @preview/arkheion:0.1.2 Typst manuscript
├── paper.pdf                   # Compiled PDF output
├── data/                       # Canonical CSV datasets backing every table
│   └── *.csv
└── figures/                    # Semantic Luminous Graphviz .dot sources + .png/.svg
    └── *.dot
```

1. **Extract Ground-Truth CSVs First (`data/*.csv`):** Populate `docs/preprint/data/*.csv` from your canonical benchmark reports before writing any table in `paper.md` or `paper.typ`. Every numeric claim in the Abstract, Introduction, and Main Results must match `data/*.csv` to the exact decimal place.
2. **Draft the Section Outline:** Follow the 6-section + 2-appendix blueprint in [`references/narrative-blueprint-2610-28380.md`](references/narrative-blueprint-2610-28380.md):
   - **Abstract:** Single paragraph (150–220 words) covering: (1) object of study, (2) failure mode or confound in prior approaches, (3) proposed framework and formal mechanism, (4) evaluation scope across domains/models/harnesses, and (5) exact quantitative headline metrics.
   - **1 Introduction:** Context $\to$ bottleneck of static/existing approaches $\to$ Figure 1 paradigm comparison `(a)`, `(b)`, `(c)` $\to$ proposed framework & headline empirical discovery $\to$ **3 bulleted contributions**.
   - **2 Related Work:** Two focused thematic subsections situating prior work and stating how the proposed methodology resolves a gap or confound.
   - **3 Method:** `3.1 Problem Setting and Overview` (formal tuple notation + Figure 2 architecture pipeline), `3.2 Formal Representation / Matrix`, `3.3 Normalized Quantitative Metrics`, `3.4 Execution / Verification Mechanism`, `3.5 Velocity / Telemetry Instrumentation`.
   - **4 Experiments:** `4.1 Evaluation Setup` (*Benchmarks and metrics*, *Comparators*, *Evaluation and reporting*) and `4.2 Main Results` (Master Table 1 with `↑` / `↓` arrows, **bold** winners, `\underline` / `*italics*` runners-up). **Table Economy Rule:** If the evaluation spans multiple domains/categories totaling $> 10$ rows, keep `Section 4.2` focused on a single **Cross-Domain Mean** summary table (`Table 1`) and move the per-domain breakdowns into **Appendix C (`Tables C.1–C.k`)**.
   - **5 Analysis:** `5.1 Ablation Studies` (isolating efficiency/velocity trade-offs with Table 2 & Figure 3, plus cross-model/cross-harness invariance in Table 3), `5.2 Case Studies` (Table 4 mapping *Unassisted Failure Mode* $\to$ *Root Cause* $\to$ *Oracle Diagnostic* $\to$ *Self-Correction*), and `5.3 Broader Corpus / Correlation Audit` (or Future Roadmap).
   - **6 Conclusion**, **Limitations**, **Author Contributions**, **References**, **Appendix A (Implementation and Evaluation Details)**, **Appendix B (Case Studies / Oracle Specifications)**, and optional **Appendix C (Detailed Per-Domain Evaluation Breakdowns)**.

### Step 2: Author Semantic Luminous Graphviz Diagrams (`figures/*.dot`)

Consult [`references/typst-and-luminous-cheatsheet.md`](references/typst-and-luminous-cheatsheet.md) and start from [`assets/fig-paradigm-skeleton.dot`](assets/fig-paradigm-skeleton.dot):
1. **Semantic Classes Only:** Assign `class="..."` attributes (`primary`, `emphasis`, `accent`, `positive`, `warning`, `error`, `muted`, `store`, `terminal`, `decision`, `code`) to every node and key edge. **Never hardcode hex colors (`#RRGGBB`), `fillcolor`, or `fontname` in `.dot` files.**
2. **Graph Title Format:** Use `label="Figure N · Concise Title"` at the root of the `digraph`.
3. **Render via Luminous `gvpr` (`.webp` for Markdown, `.png` for Typst):**
   ```bash
   for f in docs/preprint/figures/*.dot; do
     base="${f%.dot}"
     gvpr -c -f /path/to/graphviz-style/theme/luminous.gvpr -a light "$f" | dot -Twebp -o "${base}-light.webp"
     gvpr -c -f /path/to/graphviz-style/theme/luminous.gvpr -a dark "$f"  | dot -Twebp -o "${base}-dark.webp"
     gvpr -c -f /path/to/graphviz-style/theme/luminous.gvpr -a light "$f" | dot -Gdpi=288 -Tpng -o "${base}.png"
     gvpr -c -f /path/to/graphviz-style/theme/luminous.gvpr -a light "$f" | dot -Tsvg -o "${base}.svg"
   done
   ```

### Step 3: Draft `paper.md` and `paper.typ` Under the House-Style & Clean-Prose Gate

Consult [`references/house-style-and-clarity-gate.md`](references/house-style-and-clarity-gate.md) while writing:
1. **Zero Em-Dashes (`—`) in Prose:** Never use `—` in body paragraphs, abstracts, or captions. Use a colon (`:`) to introduce an explanation, a semicolon (`;`) to join independent clauses, or parentheses `(...)` for compact asides.
2. **Zero Throat-Clearing or Binary Contrasts:** Eliminate phrases such as *"It is worth noting that"*, *"In recent years"*, and *"not X, but rather Y"*. State the subject, verb, and empirical object directly.
3. **Clean-Prose Technical Density Calibration (`FK 12.0–14.5`, `FRE 30–50`):**
   - Running readability formulas on raw Markdown gives a **false pass** because short Markdown table cells depress average sentence length. Always measure **clean prose** (stripping tables, code blocks, and LaTeX math).
   - Keep clean-prose **Average Sentence Length (`ASL`) at `15–19` words/sentence** and **Average Syllables per Word (`ASW`) at `1.75–1.88` syllables/word**. Unpack 40+ word multi-clause sentences into 2–3 declarative sentences, and replace stacked Latinate nominalizations (*"syntactic validity verification"*) with short verbs and nouns (*"syntax checks"*).
4. **Native Typst Math & Booktabs Tables (`paper.typ`):**
   - Quote multi-letter identifiers in Typst math mode (`$"FVR"$`, `$"SIR"$`, `$"BT"$`, `$"PASS"$`, `$S_"max"$`).
   - Use native Typst math symbols (`$times$`, `$arrow.r$`, `$in$`, `$cal(T)$`, `$bb(I)$`, `$plus.o$`, `$inter$`, `$union$`, `$emptyset$`) rather than LaTeX macros (`\times`, `\to`, `\in`, `\mathcal{T}`) or invalid Typst symbol tokens (`plus.circle`, `sect`).
   - Separate `columns: (auto, auto, ...)` from `align: (left, right, ...)` in Typst `table(...)` definitions.

### Step 4: Run the Closed-Loop Validation Oracle (`scripts/validate_preprint.py`)

Always run the deterministic validator before concluding your turn:

```bash
python3 scripts/validate_preprint.py \
  /path/to/docs/preprint --json

# Optional: verify that a Syntaxis checkout's writer.md and reviewer.md prompts are in sync
python3 scripts/validate_preprint.py \
  --check-syntaxis-prompts ~/projects/syntaxis
```

If any check reports an error or warning (such as a stray em-dash, a hardcoded hex color in `.dot`, an unquoted Typst math token, or a `typst compile` failure), fix the exact line and re-run `validate_preprint.py` until it exits with code `0` (`"passed": true, "score": 100`).
