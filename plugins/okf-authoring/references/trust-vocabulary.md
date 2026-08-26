# OKF v0.2 — provenance, trust, lifecycle & computation vocabulary

The full optional vocabulary from **§5** (provenance, trust, lifecycle) and
**§10** (Attested Computation). All of it is **optional**: a concept carrying
only `type` is conformant (§11). The target spec version is pinned in
[`okf-v0.2-spec-summary.md`](okf-v0.2-spec-summary.md) — this file does not
restate it.

**Two rules govern everything below:**

1. **Derive trust; never store a verdict.** OKF records objective *signals*
   (`author`, `usage_count`, `last_modified`, `verified` events). It does **not**
   store a credibility score or a trust tier — those are *inferred* by the
   consumer. Never write a `credibility`, `score`, `trust`, or `tier` field.
2. **Absence carries meaning, not rejection.** An unverified concept is
   distinguishable from a verified one, but is never rejected. Missing optional
   fields are legal.

---

## 1. Provenance: `sources` (§5.1)

The materials a concept derives from, external or internal to the bundle.

```yaml
sources:
  - id: ga4-schema                     # Optional stable key; needed for per-claim citation.
    resource: https://developers.google.com/analytics/bigquery/export-schema
    title: GA4 BigQuery Export schema  # Optional label.
    author: team:ga4-docs              # Optional — actor convention (§7). Authority signal.
    usage_count: 5000                  # Optional — adoption / liveness signal.
    last_modified: 2026-05-30          # Optional — YYYY-MM-DD; source recency signal.
usage_window: { from: 2026-06-01, to: 2026-06-30 }   # Frames usage_count; sibling of sources.
```

Per entry:

- **`resource`** — REQUIRED *within an entry*. Either a followable artifact (an
  absolute URL, a bundle-relative `/path`, or a path into `references/`) **or** a
  scope descriptor it cannot follow (e.g. `all queries in BigQuery project X`).
- **`id`** — optional stable key; SHOULD be present when the body cites the
  source. Citations join on `id`, not list position, because agents reorder
  these lists constantly.
- **`title`** — optional human label.

**Credibility signals** (each optional, each an objective per-source fact — OKF
records the signal, never a verdict):

- **`author`** — who/what produced the source (actor convention, §7). Authority.
- **`usage_count`** — how often `resource` was exercised over `usage_window`.
  Adoption/liveness. Coarse: read it as alive-vs-dead and order-of-magnitude and
  trend, **not** a precise cross-kind ranking.
- **`last_modified`** — when the source itself last changed (`YYYY-MM-DD`).
  Recency; distinct from `generated.at` (when the *concept* was written).
- **`usage_window`** — written once as a sibling of `sources`; a `{ from, to }`
  range framing every `usage_count`. A single entry MAY carry its own to
  override.

**Per-claim attribution** uses a markdown footnote whose label is a
`sources[].id`:

```markdown
The `events_` table is sharded daily as `events_YYYYMMDD`.[^ga4-schema]

[^ga4-schema]: GA4 BigQuery Export schema
```

The label is the join key into `sources`; consumers resolve attribution through
the matching entry, not by parsing the footnote prose. Lineage is expressed
through links (§6), not a dedicated field: when a `resource` points at another
OKF concept, the derivation edge already exists in the graph.

## 2. Trust: `generated` and `verified` (§5.2)

`generated` = how the current content was produced. `verified` = who/what has
confirmed it. Kept distinct: who *wrote* a concept need not be who *confirmed*
it.

```yaml
generated: { by: reference_agent/gemini-2.5-pro, at: 2026-06-20T22:53:05Z }
```

- **`generated.by`** — REQUIRED *within* `generated`. An actor (§7).
- **`generated.at`** — ISO 8601 datetime; the content's last meaningful change.

```yaml
verified:
  - { by: human:ahormati, at: 2026-06-25T09:00:00Z }
  - { by: process:finance-nightly, at: 2026-06-26T02:00:00Z }
```

- **`verified`** — a list of `{ by, at }` events (actor + ISO 8601 datetime).
  Multiple entries capture independent checks. "How recently" = the latest `at`.
- Independent of `generated.at`: content can change without re-confirmation, and
  facts can be re-confirmed without regeneration.
- A single verifier MAY be written as one bare mapping (no list dash);
  consumers MUST treat a bare mapping as a one-element list:

```yaml
verified: { by: human:ahormati, at: 2026-06-25T09:00:00Z }
```

## 3. Trust tiers (§5.3) — derived, never stored

A consumer *derives* the tier from `verified`, lowest to highest:

| `verified` state                                  | Derived tier        |
|---------------------------------------------------|---------------------|
| No `verified` key                                 | **unverified**      |
| `verified` by non-`human:` actors only            | **machine-confirmed** |
| `verified` includes a `human:<id>` actor          | **human-reviewed**  |

Tiers are advisory signals, not access control. A concept with no trust
frontmatter is still consumable. **Do not persist the tier into frontmatter** —
compute it on read from `verified`.

## 4. Lifecycle: `status` and `stale_after` (§5.4, §5.5)

```yaml
status: stable        # draft | stable | deprecated  (absent ⇒ stable)
stale_after: 2026-09-23   # absolute date YYYY-MM-DD; stale when today >= stale_after
```

- `status`: `draft` (not yet reviewed) · `stable` (default, ready) ·
  `deprecated` (kept for links/history). Absent ⇒ `stable`.
- `stale_after`: an **absolute** date, not a relative TTL, so staleness is a
  plain date comparison independent of when the concept was read.

## 5. Attested Computation (§10) — overview

An **Attested Computation** is a standalone concept (`type: Attested Computation`)
carrying a sanctioned way to *compute* a value, so a consumer can confirm the
value was produced by running it rather than improvised. A concept that needs the
value (`Metric`, `BigQuery Table`) links to it with a normal markdown link.

Contract fields (top-level frontmatter, in addition to the §5 families):

- **`runtime`** — REQUIRED for this type. How to run the computation (and how the
  executor/attester interpret it and what `parameters` mean). E.g. `bigquery`,
  `postgres`, `dbt`, `python`, `Looker`.
- **`parameters`** — list of typed named holes: `{ name, type, required }`.
  Binding semantics follow `runtime`.
- **`computation`** — optional path (§6.2) to a file holding the computation,
  used instead of an inline body fence. Absent ⇒ the body `# Computation` fence
  is the computation.
- **`executor`** — `resource` names run instructions/code; `receipt` declares the
  fields a run must return (e.g. `[job_id, executed_sql, result]`).
- **`attester`** — `resource` names deterministic (no-LLM) code that inspects a
  receipt and returns a verdict; meant to run consumer-side.

```yaml
type: Attested Computation
runtime: bigquery
parameters:
  - { name: year, type: integer, required: true }
executor:
  resource: references/skills/run-on-bq.md
  receipt: [job_id, executed_sql, result]
attester:
  resource: references/attesters/revenue.py
```

Provide the computation **inline** (one fenced block under `# Computation`) or by
**file** (`computation:` path, omit the fence). The agent MAY supply only
*values* for declared `parameters`; it MUST NOT author or edit the computation.

**Verification vs. attestation** (§10.6): `verified` (§5.2) confirms the
*definition* still matches policy — doc-level, recorded in the bundle.
Attestation confirms a single *run* produced the value the sanctioned way —
per-call, runtime, **not stored in the bundle**. Both exist and are distinct.
Runtime artifacts (receipts, verdicts) are never committed to the bundle.

## 6. Worked frontmatter (a fully-signalled concept)

```yaml
---
type: Metric
title: Revenue
description: Recognized revenue for a fiscal year.
tags: [finance, revenue]
status: stable
stale_after: 2026-12-31
generated: { by: reference_agent/gemini-2.5-pro, at: 2026-06-20T22:53:05Z }
verified:
  - { by: human:ahormati, at: 2026-06-25T09:00:00Z }
sources:
  - id: rev-policy
    resource: https://wiki.acme/finance/revenue-recognition
    title: Revenue recognition policy
    author: team:finance
    last_modified: 2026-05-30
---
```

Derived (not stored): trust tier = **human-reviewed** (a `human:` verifier is
present); staleness = fresh until 2026-12-31.
