---
name: okf-author
description: Author a conformant Open Knowledge Format (OKF) v0.2 knowledge bundle by hand or from a description — one concept per markdown file with a required non-empty type, a reserved root index.md declaring okf_version, bundle-relative markdown links as relationship edges, and the correct v0.2 provenance/trust/lifecycle frontmatter (sources, generated, verified, status, stale_after). Derives trust tiers rather than storing a credibility score, and preserves unknown keys for forward-compatibility. Works fully by hand with zero OKF binaries installed; opportunistically uses binder/okfcli/factile/openknowledge when present. Use when asked to create an OKF bundle, write OKF concepts, add trust or provenance frontmatter, or turn notes/a description into OKF.
license: Apache-2.0
metadata:
  version: "1.0.0"
---

# Author an OKF v0.2 bundle

This skill produces a **conformant OKF v0.2 knowledge bundle** — a directory of
markdown files with YAML frontmatter — either by hand or from a description the
user gives you. The whole format is deliberately tiny: *if you can `cat` a file,
you can read OKF; if you can `git clone` a repo, you can ship it.*

*Note: This skill references shared plugin documentation (`../../references/`) and is designed to be installed as part of the `okf-authoring` plugin.*

**Tool-agnostic by design.** Everything here works with **zero OKF binaries
installed** — you are writing markdown and YAML. Where a CLI happens to be
available you MAY use it opportunistically (see [CLI is
opportunistic](#cli-is-opportunistic-never-required)), but never depend on one.

## Load these when you need them (progressive disclosure)

- [`../../references/okf-v0.2-spec-summary.md`](../../references/okf-v0.2-spec-summary.md)
  — bundle structure, concept frontmatter, cross-linking (§6), actor convention
  (§7), reserved files (§8/§9), conformance (§11), versioning (§12). **The spec
  version is pinned there, once.**
- [`../../references/trust-vocabulary.md`](../../references/trust-vocabulary.md)
  — the full provenance / trust / lifecycle vocabulary (§5) and Attested
  Computation (§10). Load before writing any `sources`, `generated`, `verified`,
  `status`, `stale_after`, or `Attested Computation` frontmatter.
- [`assets/example-bundle/`](assets/example-bundle/) — a tiny, complete,
  conformant reference bundle you can read or copy as a starting scaffold.

Don't paste those files into context wholesale up front — open them when the task
in front of you calls for them.

## The three invariants (never violate these)

1. **Never store a credibility score or trust tier.** Record objective signals
   (`author`, `usage_count`, `last_modified`, `verified` events); the *tier* is
   derived on read, not written to frontmatter. No `score`/`credibility`/`tier`
   keys. (§5.1, §5.3)
2. **Never reject or drop unknown keys/types.** Preserve producer-defined keys
   verbatim on any round-trip; unknown `type` values are legal. (§4.1)
3. **Broken links and missing optional fields are legal.** Write bundle-relative
   links even to not-yet-written concepts; do not fabricate targets. (§6)

## Procedure

### 1. Establish the bundle root and layout

- A bundle is a directory tree. One **concept per non-reserved `.md`**. A
  concept's **ID is its path minus `.md`** (`tables/orders.md` → `tables/orders`).
- Organize concepts into subdirectories however the knowledge makes sense — the
  layout is domain-driven, not prescribed.
- Reserved filenames (`index.md`, `log.md`) are **not** concepts. Don't author a
  concept named either.

### 2. Write the reserved root `index.md` — the one place `okf_version` lives

Create a bundle-root `index.md`. It is the **only** file in the whole bundle
whose frontmatter may (and here, should) declare the version:

```markdown
---
okf_version: "0.2"
---

# Concepts

* [Customer Orders](/tables/orders.md) - one row per completed order
* [Revenue](/metrics/revenue.md) - recognized revenue for a fiscal year
```

- Root `index.md` is the **only** `index.md` permitted to carry frontmatter, and
  `okf_version` is the **only** key that belongs there (§8, §12).
- Non-root `index.md` files (in subdirectories) carry **no frontmatter** — just
  the link-list body.
- Entries SHOULD reuse each concept's `description`. Index files are optional
  everywhere except that this is where you declare the version, so write it.

### 3. Write each concept

Every concept file is frontmatter + body:

```markdown
---
type: BigQuery Table          # REQUIRED, non-empty. The only always-required key.
title: Customer Orders        # Recommended.
description: One row per completed customer order across all channels.
tags: [sales, orders]
generated: { by: human:you, at: 2026-08-15T10:00:00Z }
---

# Schema

| Column     | Type   | Description                                   |
|------------|--------|-----------------------------------------------|
| `order_id` | STRING | Globally unique order identifier.             |

Joined with [customers](/tables/customers.md) on `customer_id`.
```

- **`type` is mandatory and non-empty** — this is half of the entire conformance
  test (§11). Pick a descriptive free-text label (`Metric`, `Playbook`,
  `Reference`, `BigQuery Table`, …). No registry; unknown types are fine.
- Prefer structural markdown (headings, tables, lists, fenced code) over prose.
- Add `title`, `description`, `tags`, `resource` when they apply.

### 4. Link concepts — links are the edges

Relationships between concepts *are* standard markdown links (§6):

- Prefer **bundle-relative** links beginning with `/`:
  `[customers](/tables/customers.md)`. Stable when a file moves within its
  subdirectory.
- The link's *meaning* (joins-with, depends-on, parent/child) lives in the
  surrounding prose — the edge itself is untyped.
- Link freely to concepts you haven't written yet; **broken links are allowed**
  and simply mark not-yet-written knowledge. Never invent a file to satisfy a
  link.

### 5. Add trust & provenance frontmatter (optional but recommended)

Load [`../../references/trust-vocabulary.md`](../../references/trust-vocabulary.md)
first. Then add only what you can honestly assert:

- **`generated: { by, at }`** — how the content was produced. `by` uses the
  **actor convention**: `<producer>/<version>` for agents/tools,
  `human:<id>` for people, `process:<id>` for automated processes. `at` is ISO
  8601. Set `by: human:<id>` when *you the author* are a person.
- **`verified: [{ by, at }]`** — who confirmed it, if anyone. A `human:` verifier
  ⇒ the concept *derives* to the **human-reviewed** tier; machine-only ⇒
  **machine-confirmed**; no `verified` ⇒ **unverified**. **Do not write the tier
  itself.**
- **`sources: [{ resource, id?, title?, author?, usage_count?, last_modified? }]`**
  — provenance. `resource` is required within each entry. Cite a specific claim
  with a markdown footnote whose label equals a `sources[].id`.
- **`status`** (`draft`/`stable`/`deprecated`, absent ⇒ `stable`) and
  **`stale_after`** (absolute `YYYY-MM-DD`) for lifecycle.
- For a sanctioned computation, use a standalone `type: Attested Computation`
  concept with `runtime` (required) + `parameters`/`executor`/`attester`; see
  §10 in the trust vocabulary. Runtime receipts are **never** stored in the
  bundle.

### 6. Add `log.md` if history matters (optional)

A `log.md` at any level records changes, newest first, under ISO 8601 date
headings. See §9 in the spec summary.

### 7. Self-check before handing off

Run the [`okf-validate`](../okf-validate/SKILL.md) skill, or at minimum confirm
by hand:

- [ ] Every non-reserved `.md` has parseable frontmatter with a **non-empty
      `type`**.
- [ ] Bundle-root `index.md` declares **`okf_version: "0.2"`**; no other
      `index.md` carries frontmatter.
- [ ] Links use bundle-relative `/…` form; any `generated.by`/`verified[].by`
      uses the actor convention.
- [ ] No stored credibility score / trust tier; unknown keys preserved.

## CLI is opportunistic, never required

The by-hand path above is complete on its own. If — and only if — a producer
tool is already installed, you MAY use it to scaffold or format, then still
hand-verify the output against the invariants above:

- `binder convert <corpus>` — converts a plain-markdown corpus to an OKF v0.2
  bundle (standard markdown links → OKF edges). Useful as a starting point.
- `okfcli`, `factile`, `openknowledge` — may offer authoring/formatting helpers.

If none are present, proceed entirely by hand — that is the expected default.
Detect availability (e.g. `command -v binder`) rather than assuming it.

## Bulk / existing-corpus ingestion → hand off to binder's `okf-convert` skill

This skill authors a **single** bundle by hand. It is deliberately the wrong
tool for turning an **existing markdown corpus** (a whole directory tree of `.md`
files) into OKF at scale. For that, there is a named, purpose-built handoff:

- **Hand off to the binder `okf-convert` skill** (the `okf-convert` Agent Skill
  in the `okf-convert` plugin from `ghchinoy/binder`) when the job is to
  **convert / ingest / migrate an existing corpus**, to drive binder end-to-end
  (`convert → validate → review`), or when you need **deterministic, offline/CI,
  provenance-preserving** ingestion at scale. That skill drives the `binder` CLI
  and reasons over its structured `--json` output; it carries the
  ingestion-analysis judgment (flag choice, pre-convert dry-run triage,
  trust-extraction review, the post-convert acceptance loop) that by-hand
  authoring cannot. Install it with:

  ```
  /plugin marketplace add ghchinoy/binder
  ```

  Like this skill, `okf-convert` **never fabricates trust** — it proposes trust
  and defers all stamping to deterministic binder (no auto `verified`, no
  invented `sources`, no stored tier).

- **Stay in this skill (Layer A)** for hand-authoring or editing an **individual**
  bundle or concept, and for any **zero-binary environment**: `okf-author` has no
  binary dependency and this handoff introduces none. If binder is not installed
  and you only need to write one bundle, author it by hand — that is the default.

## Sources

- Open Knowledge Format (OKF) SPEC.md v0.2 — GoogleCloudPlatform/knowledge-catalog, okf/SPEC.md
