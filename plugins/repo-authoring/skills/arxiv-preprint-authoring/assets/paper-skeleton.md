# <Title: Concise Mechanism Name>: <Subtitle Isolating Causal Variables in Domain>

**Authors:**  
- **<First Author>** (`<email@domain.com>`)  
- **<Second Author>** (`<email@domain.com>`)  

**Affiliation:** <Organization / Research Group>  
**Date:** <Month Year>  

---

## Abstract

<Single paragraph, 150-220 words. Sentence 1: State the domain and operational role of the system under study. Sentence 2-3: State the methodological bottleneck or confound in existing evaluation/engineering conventions. Sentence 4: Introduce the proposed framework and its formal mechanism. Sentence 5-6: State the experimental scope (number of domains, models, harnesses) and exact quantitative headline metrics ($"Metric" = X$, speedup $Y\times$, defect elimination $Z\%$).>

---

## 1 Introduction

<Paragraph 1: Operational context and why rigorous evaluation/engineering of the target system matters in production.>

<Paragraph 2: Failure mode of prevailing conventions (e.g., static linters, global unconstrained rewrites, or end-state-only grading) and the specific confound they introduce.>

<Paragraph 3: Overview of the proposed framework and its isolated conditions:>
1. **Condition A (Control):** <Description>
2. **Condition B (<Treatment 1>):** <Description>
3. **Condition C (<Treatment 2>):** <Description>
4. **Condition D (<Combined Package>):** <Description>

![Comparison of paradigms](figures/fig1_paradigms.png)
*Figure 1: Comparison of paradigms. (a) Baseline approach. (b) Conventional heuristic/static approach. (c) Proposed closed-loop approach.*

<Paragraph 4: Summary of the primary empirical discovery (e.g., the trade-off or paradox uncovered by trajectory telemetry) with exact ratios.>

Our primary contributions are three-fold:
- **<Contribution 1 Title>:** <Formal methodology and normalized quantitative ratios.>
- **<Contribution 2 Title>:** <Oracles, telemetry instrumentation, and anti-fragile grading principles.>
- **<Contribution 3 Title>:** <Empirical validation across orthogonal domains, models, and runtime harnesses.>

---

## 2 Related Work

### <Thematic Subsection 2.1: Architectures & Representations>
<Situate prior systems, citing relevant literature and contrasting their scope with the present work.>

### <Thematic Subsection 2.2: Evaluation Benchmarks & Telemetry>
<Situate evaluation benchmarks and explain how combining factorial isolation with trajectory telemetry resolves prior blind spots.>

---

## 3 Method

### 3.1 Problem Setting and Overview

We consider an executor $M$ performing task $x \in \mathcal{X}$ within an isolated workspace $W_0$ under configuration $H = (P, \mathcal{T})$:

$$\tau = \left( (a_1, o_1), (a_2, o_2), \dots, (a_K, o_K) \right) \sim \mathcal{E}(M, P, \mathcal{T}, x, W_0)$$

![Architecture Pipeline](figures/fig2_pipeline.png)
*Figure 2: Overview of the evaluation and telemetry pipeline.*

### 3.2 Formal Representation and Matrix Isomorphism

<Define the orthogonal factors and map each cell $H_A, H_B, H_C, H_D$ to its corresponding delivery modality.>

### 3.3 Normalized Quantitative Metrics

1. **<Metric 1> ($\text{M}_1$):**
   $$\text{M}_1 = \frac{S(H_B)}{S(H_A)}$$

2. **<Metric 2> ($\text{M}_2$):**
   $$\text{M}_2 = \frac{S(H_C) - S(H_A)}{S_{\max} - S(H_A)} \times 100\%$$

### 3.4 Closed-Loop Execution and Anti-Fragile Oracles

<Detail how in-situ verification tools operate and state the anti-fragile grading principles.>

### 3.5 Developer Velocity Telemetry

<Define the trajectory velocity metrics: Turns ($K$), Mutations ($M_{\text{mut}}$), Exploration Waste ($W_{\text{exp}}$), Clock Latency ($t_{\text{clock}}$), and Token Footprint ($T_{\text{total}}$).>

---

## 4 Experiments

### 4.1 Evaluation Setup

#### Benchmarks and Metrics
<Describe the orthogonal evaluation domains and their deterministic validation checks.>

#### Comparators
<Describe the compared conditions and runtime harnesses.>

#### Evaluation and Reporting
<Specify model pinning, decoding temperature, turn budgets, and cloud routing.>

### 4.2 Main Results

| Domain | Condition | Tool | Score (%) $\uparrow$ | PASS (%) $\uparrow$ | Turns ($K$) $\downarrow$ | Latency (s) $\downarrow$ | Total Tokens $\downarrow$ |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **Domain 1** | **A (Control)** | No | 85.0 | 0.0 | 2 | 33.38 | 5,427 |
| | **B (Format Only)** | No | **100.0** | **100.0** | 1 | **24.05** | **2,539** |
| | **C (Script Only)** | **Yes** | **100.0** | **100.0** | 2 | 27.47 | 6,453 |
| | **D (Full Package)** | **Yes** | **100.0** | **100.0** | 2 | \underline{26.71} | \underline{5,074} |

*Table 1: Main evaluation results across benchmark domains. Bold indicates best; underline indicates runner-up.*

---

## 5 Analysis

### 5.1 Ablation Studies

#### 5.1.1 <Ablation 1: Velocity vs. Deliberation Trade-off>
<Analyze trajectory telemetry with Table 2 and Figure 3.>

#### 5.1.2 <Ablation 2: Cross-Model and Cross-Harness Invariance>
<Analyze invariance across model families and SDK harnesses with Table 3.>

### 5.2 Case Studies: Root-Cause Defect Elimination

| Domain | Unassisted Failure Mode | Root Cause | Oracle Diagnostic (Turn $k$) | Self-Correction (Turn $k+1$) |
| :--- | :--- | :--- | :--- | :--- |
| **Domain 1** | <Failure> | <Root cause> | <Exact diagnostic> | <Patch & verification> |

*Table 4: Root-cause failure modes and closed-loop self-corrections.*

---

## 6 Conclusion

<Concise synthesis of the methodology, empirical findings, and operational prescription.>

---

## Limitations

<Discuss scope boundaries and future directions transparently.>

---

## Author Contributions

- **<Author 1>** <Contribution summary.>
- **<Author 2>** <Contribution summary.>

---

## References

- <Author list>. **<Paper Title>.** *<Venue / arXiv preprint>*, <Year>.

---

## Appendix A: Implementation and Evaluation Details

### A.1 Model Configuration
<Details on model IDs, temperature, and endpoints.>

### A.2 Sandbox Execution and Checkpointing
<Details on workspace isolation and fault recovery.>

---

## Appendix B: Case Studies of Deterministic Validation Oracles

### B.1 <Domain 1 Oracle Specification>
<Details on AST/schema checks implemented by the validator.>
