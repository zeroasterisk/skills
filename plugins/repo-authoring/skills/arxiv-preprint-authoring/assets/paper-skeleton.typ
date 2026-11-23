#import "@preview/arkheion:0.1.2": arkheion, arkheion-appendices

#show: arkheion.with(
  title: "Paper Title: Isolating Causal Variables in Agent Engineering",
  authors: (
    (
      name: "First Author",
      email: "author1@domain.com",
      affiliation: "Organization",
    ),
    (
      name: "Second Author",
      email: "author2@domain.com",
      affiliation: "Organization",
    ),
  ),
  abstract: [
    Single-paragraph abstract stating the object of study, the methodological bottleneck, the proposed framework, the evaluation scope, and headline quantitative metrics ($"SIR" = 100.0%$, $"FVR" = 1.00$).
  ],
  keywords: ("Agent Skills", "Factorial Ablation", "Deterministic Oracles", "Agent Experience (AX)"),
  date: "October 2026",
)

= Introduction

Contextualize the problem and introduce the experimental conditions.

#figure(
  image("figures/fig1_paradigms.png", width: 100%),
  caption: [Comparison of paradigms across baseline, static, and closed-loop configurations.],
) <fig-paradigms>

= Related Work

== Modular Representations
Situate prior work on agent harnesses and modular skills.

== Evaluation Benchmarks and Telemetry
Situate evaluation frameworks and developer velocity telemetry.

= Method

== Problem Setting and Overview
Formalize the trajectory $tau tilde.op cal(E)(M, P, cal(T), x, W_0)$ and oracle $V: cal(W) arrow.r [0, S_"max"]$.

== Normalized Quantitative Metrics
$ "FVR" = frac(S(H_B), S(H_A)), quad "SIR" = frac(S(H_C) - S(H_A), S_"max" - S(H_A)) times 100% $

= Experiments

== Evaluation Setup
Describe the benchmark domains, comparators, and model pinning.

== Main Results
#figure(
  table(
    columns: (auto, auto, auto, auto, auto, auto, auto),
    align: (left, left, center, right, right, right, right),
    stroke: none,
    table.hline(stroke: 0.75pt),
    [*Domain*], [*Condition*], [*Tool*], [*Score↑*], [*PASS↑*], [*Latency↓*], [*Tokens↓*],
    table.hline(stroke: 0.4pt),
    [`domain-1`], [A (Control)], [No], [85.0%], [0.0%], [33.38s], [5,427],
    [], [C (Script)], [*Yes*], [*100.0%*], [*100.0%*], [*27.47s*], [6,453],
    table.hline(stroke: 0.75pt),
  ),
  caption: [Main factorial evaluation scoreboard.],
) <tbl-main>

= Analysis

== Ablation Studies
Analyze velocity telemetry and cross-model invariance.

== Case Studies
Trace root-cause failures to deterministic oracle diagnostics.

= Conclusion

Summarize findings and operational recommendations.

= Author Contributions

- *First Author:* Conceived the experimental matrix and validation oracles.
- *Second Author:* Conceived the developer velocity telemetry framework.

#show: arkheion-appendices

= Implementation Details

Document sandbox isolation, checkpointing, and oracle rules.
