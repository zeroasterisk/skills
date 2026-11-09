# Narrative Blueprint (`arXiv:2610.28380` Reference Architecture)

This reference defines the structural, rhetorical, and quantitative blueprint for empirical AI systems preprints modeled after **`arXiv:2610.28380`** (*Object-Oriented Harness: Evolving Agent Harnesses through Object-Oriented Design*).

---

## 1. Macro-Structure & Pacing

An empirical systems preprint must progress through six numbered sections, followed by Limitations, Author Contributions, References, and two structured Appendices:

| Section | Target Length | Core Rhetorical Function | Required Visual / Quantitative Anchor |
| :--- | :--- | :--- | :--- |
| **Abstract** | 150–220 words (1 paragraph) | State the object of study, the methodological confound in prior work, the proposed framework, evaluation scope, and exact headline metrics. | Inline ratios ($\text{SIR} = 100.0\%$, $\text{FVR} = 1.00$, $4.23\times$ speedup). |
| **1 Introduction** | 4–5 paragraphs + 3 bullets | Motivate the operational problem, expose why static/global conventions fail, introduce the isolated conditions, and list 3 contributions. | **Figure 1**: Three-panel paradigm comparison `(a)`, `(b)`, `(c)`. |
| **2 Related Work** | 2 subsections (2–3 paragraphs) | Situate prior agent harnesses/representations (2.1) and evaluation benchmarks/telemetry (2.2). | Explicit contrast showing how this paper resolves an unmeasured confound. |
| **3 Method** | 5 subsections (`3.1`–`3.5`) | Formalize the execution trajectory tuple, matrix isomorphism, normalized equations, oracle mechanics, and velocity telemetry. | **Figure 2**: Multi-stage pipeline architecture + numbered equations. |
| **4 Experiments** | `4.1 Setup` + `4.2 Main Results` | Define orthogonal benchmark domains, comparators, model pinning, and present the master Cross-Domain Mean scoreboard (`Table 1`). | **Table 1**: Master Cross-Domain Mean scoreboard with `↑`/`↓`, **bold**, `\underline`, and per-domain breakdowns in **Appendix C** when $> 10$ rows. |
| **5 Analysis** | `5.1 Ablations` + `5.2 Case Studies` + `5.3 Audit` | Explain *why* the mechanism works: velocity vs. deliberation trade-off, cross-model/harness invariance, and root-cause defect traces. | **Table 2** & **Figure 3** (Velocity Paradox), **Table 3** (Invariance), **Table 4** (Case Studies). |
| **6 Conclusion** | 1 paragraph | Synthesize the causal findings and state a direct operational prescription for engineers. | Summary of key ratios. |
| **Appendices A–C** | 2–3 appendices | Document exact model routing/CLI details (Appendix A), validation oracle specifications (Appendix B), and per-domain evaluation tables (Appendix C). | Reproducible CLI/SDK configuration details & full domain scoreboards. |

---

## 2. Table Design & Quantitative Presentation Standards

1. **Directional Indicators (`↑` / `↓`):** Every metric column header in every table must specify whether higher (`↑`) or lower (`↓`) values are better (for example, `Score (%) ↑`, `PASS (%) ↑`, `Turns (K) ↓`, `Latency (s) ↓`, `Total Tokens ↓`).
2. **Visual Hierarchy & Main-Body Table Economy (`Section 4.2` vs. `Appendix C`):**
   - **Bold (`**100.0**` / `[*100.0%*]`)** marks the best-performing cell in each domain block.
   - **Underline / Italics (`\underline{26.71}` / `*26.71*` / `[#underline[26.71s]]`)** marks the runner-up among passing configurations.
   - **Cross-Domain Mean Summary in `Section 4.2`:** Always present a `Cross-Domain Mean` summary aggregating all evaluated domains so readers can compare conditions globally at a glance. When evaluating multiple domains across many checkpoints ($> 10$ total rows), keep **only** the `Cross-Domain Mean` summary table (`Table 1`) in `Section 4.2` and move the per-domain breakdowns (`Tables C.1–C.k`) to **Appendix C** to prevent main-body table clutter.
3. **Root-Cause Case Study Table (Table 4):**
   - Never stop at aggregate pass rates. Always include a qualitative-to-quantitative trace table with columns:
     `Domain` | `Unassisted Failure Mode` | `Root Cause of Prompt Failure` | `Deterministic Oracle Diagnostic (Turn k)` | `Self-Correction Action (Turn k+1)`.
