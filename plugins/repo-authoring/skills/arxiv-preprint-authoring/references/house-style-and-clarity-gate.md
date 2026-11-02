# House-Style and Clarity Gate (`Syntaxis` & Editorial Standards)

This reference defines the mandatory prose and clarity rules for academic preprints and technical manuscripts. Every draft must pass these checks before publication.

---

## 1. Prohibited Rhetorical Devices

1. **Zero Em-Dashes (`—`) in Prose:**
   - Do not use `—` (U+2014) anywhere in abstract, body paragraphs, list items, or figure/table captions.
   - *Why:* Models overuse em-dashes as a generic rhetorical splice instead of specifying whether the second clause is a causal explanation (use a colon `:`), a coordinate independent clause (use a semicolon `;`), or a parenthetical aside (use parentheses `(...)`).
2. **Zero Throat-Clearing Openers:**
   - Ban openers that delay the subject and verb:
     - *"It is important to note that..."*
     - *"It is worth mentioning that..."*
     - *"In the rapidly evolving landscape of..."*
     - *"Needless to say..."*
   - *Fix:* Delete the preamble and begin directly with the actor and action.
3. **Zero Lazy Binary-Contrast Frames (`"Not X, but Y"`):**
   - Avoid formulaic contrast templates such as *"This is not merely X, it is Y"* or *"The goal is not to X, but rather to Y"* unless contrasting two formal mathematical definitions ($P = 0$ vs. $\mathcal{T} = 1$).
4. **Zero Unanchored Evaluative Adjectives:**
   - Never write *"stunning improvement"*, *"massive speedup"*, or *"dramatic reduction"* without immediately binding the noun phrase to the exact numeric multiplier and baseline comparison in the same sentence (for example: *"cuts wall-clock latency by $4.23\times$ (54.10s vs. 229.02s)"*).

---

## 2. Active Voice & Named Actors

Every sentence describing system behavior or experimental methodology must name the concrete actor:
- **Weak (Passive / Unattributed):** *"Candidate outputs are validated and errors are fixed in subsequent turns."*
- **Strong (Named Actor):** *"In Conditions C and D, the executor $M$ invokes `run_validator` on workspace $W_k$, receives line-level AST diagnostics from oracle $V$, and patches the offending struct field in Turn $k+1$."*

---

## 3. Clean-Prose Readability & Technical Density Calibration

1. **Always Measure Clean Prose (Avoid the Raw-Markdown Illusion):**
   - Running Flesch-Kincaid (`FK`) on a raw Markdown file (`paper.md`) produces an artificially low grade (`FK ~11–13`) because Markdown table rows and headers are parsed as short sentences, masking `Very Dense` or `Impenetrable` prose (`FK 20+`).
   - Always strip Markdown tables, fenced code blocks, inline code tokens, and LaTeX display/inline math (`$$...$$`, `$...$`) before evaluating readability (e.g., via `~/projects/docstats` or `scripts/validate_preprint.py`).
2. **Target Clean-Prose Metrics (`Dense` Systems-Paper Band):**
   - **Flesch-Kincaid Grade (`flesch_kincaid_grade`):** **12.0 to 14.5** (warn if $> 16.0$).
   - **Flesch Reading Ease (`flesch_reading_ease`):** **30.0 to 50.0**.
   - **Average Sentence Length (`ASL`):** **15.0 to 19.0 words/sentence** (never exceed `22.0` w/s overall; avoid sentences $\ge 38$ words).
   - **Average Syllables per Word (`ASW`):** **1.75 to 1.88 syllables/word**.
   - **Axis B (`ai_tell_score` in `docstats`):** **$\ge 9.5 / 10.0$** (`0` em-dashes, `0` throat-clearing openers, `0` binary contrasts, `0` offender adverbs, `-ly` adverb rate $\le 1.0 / 100\text{w}$, sentence-length CV $\ge 0.25$).
3. **Three Levers to Lower Technical Density Without Losing Rigor:**
   - **Unpack Multi-Clause Sentences:** Do not pack a conceptual mechanism, 4 parenthetical metrics, and 3 CLI flags into a single 60-word sentence. State the mechanism in one crisp 12–16 word sentence, then report the numeric comparison in the next sentence.
   - **Replace Polysyllabic Nominalizations with Plain Verbs and Short Nouns:** After defining a formal term once, prefer *"syntax checks"* over *"syntactic validity verification"*, *"token generation"* over *"autoregressive generation"*, *"rounding coordinates"* over *"coordinate canonicalization"*, and *"matching path commands"* over *"command-signature parity"*.
   - **Paragraph Unity & Rhythm:** Open each paragraph with a direct 10–15 word topic sentence stating the claim, develop the formal or empirical mechanism in the middle sentences, and close with the quantitative consequence or table/figure reference.
