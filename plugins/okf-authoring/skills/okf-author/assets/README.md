# Example OKF v0.2 bundle

`example-bundle/` is a tiny, complete, **conformant OKF v0.2** knowledge bundle,
authored entirely by hand (no OKF binary). Read it or copy it as a starting
scaffold for the `okf-author` skill.

It demonstrates every core feature:

- a bundle-root [`index.md`](example-bundle/index.md) declaring
  `okf_version: "0.2"` (the only legal place for it);
- one concept per non-reserved `.md` file, each with a required non-empty `type`;
- a subdirectory [`index.md`](example-bundle/tables/index.md) with **no**
  frontmatter (only the root index may carry frontmatter);
- bundle-relative markdown links (`/path.md`) as relationship edges;
- the full v0.2 trust vocabulary: `generated`, `verified` (human-reviewed and
  machine-confirmed tiers, **derived**, never stored), `sources` with a per-claim
  footnote citation, `status`, `stale_after`;
- an [Attested Computation](example-bundle/computations/revenue.md) concept
  (`runtime`, `parameters`, `executor`, `attester`) linked from a
  [Metric](example-bundle/metrics/revenue.md), with its executor and attester
  kept as first-class `references/` concepts (§6.3);
- a [`log.md`](example-bundle/log.md) update history.

Broken links are deliberately **not** shipped here so the bundle passes strict
external validators cleanly, but the format tolerates them: a link to a
not-yet-written concept is an advisory, never a rejection (§6, §11). The
`okf-validate` skill explains how to treat them.

This directory is `assets/`, so its markdown files are example content, not
skills.
