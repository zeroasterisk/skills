# OKF v0.2 — spec summary (structure, conformance, versioning)

> **Target spec version — pinned here, once.**
> This plugin targets **Open Knowledge Format (OKF) v0.2**.
> The literal frontmatter value a bundle declares is **`okf_version: "0.2"`**.
> This file is the single source of truth for the version. Every other file in
> this plugin refers back here rather than restating a version number, so an
> additive spec bump is a one-line change in one place.
>
> Authoritative spec: `GoogleCloudPlatform/knowledge-catalog` → `okf/SPEC.md`
> (v0.2). Section numbers below (§n) reference that document.

This file covers bundle **structure**, **conformance** (§11), **cross-linking**
(§6), **actor convention** (§7), and **reserved files** (§8, §9). The
provenance / trust / lifecycle vocabulary lives in
[`trust-vocabulary.md`](trust-vocabulary.md). Load whichever you need — this is
progressive disclosure, not required reading up front.

---

## What OKF is (one paragraph)

An OKF **bundle** is a directory tree of UTF-8 markdown files. Each non-reserved
`.md` file is one **concept**. A concept's **ID** is its path within the bundle
with the `.md` suffix removed (`tables/orders.md` → `tables/orders`). Each
concept has YAML **frontmatter** (delimited by `---`) and a markdown **body**.
Ordinary markdown links between files *are* the relationships between concepts.
The only always-required frontmatter key is `type`. There is no schema registry
and no required tooling: "if you can `cat` a file, you can read OKF."

## Bundle structure (§3)

```
bundle/
  index.md                 # Optional. Directory listing (§8). Root index MAY carry okf_version.
  log.md                   # Optional. Chronological update history (§9).
  <concept>.md             # A concept at the bundle root.
  <subdir>/
    index.md               # Optional per-directory listing.
    <concept>.md
    <subdir>/ ...
```

Directory layout is a producer choice; organize concepts however the knowledge
makes sense. A bundle may be shipped as a git repo (recommended), a tarball, or
a subdirectory of a larger repo.

### Reserved filenames (§3.1)

| Filename   | Meaning                       | Frontmatter? |
|------------|-------------------------------|--------------|
| `index.md` | Directory listing (§8).       | None — **except** a bundle-root `index.md` MAY carry `okf_version` (§12). |
| `log.md`   | Update history (§9).          | None.        |

`index.md` and `log.md` MUST NOT be used as concept documents. Every other
`.md` file is a concept.

## Concept frontmatter (§4.1)

```yaml
---
type: <Type name>                  # REQUIRED — short free-text label; no registry.
title: <display name>              # Recommended.
description: <one-line summary>    # Recommended.
resource: <canonical URI>          # Optional — for concepts bound to an asset.
tags: [<tag>, <tag>]               # Optional.
# provenance / trust / lifecycle families (§5) — see trust-vocabulary.md
# computation fields for Attested Computation concepts (§10) — see trust-vocabulary.md
# ... any additional producer-defined keys
---
```

- `type` is the **only** always-required key. A concept carrying just `type` is
  fully conformant. Pick descriptive, self-explanatory values
  (`BigQuery Table`, `Metric`, `Playbook`, `Reference`, `Attested Computation`).
- **Unknown keys and unknown `type` values are legal.** Preserve unknown keys on
  round-trip; never reject a document for an unrecognized field or type.

### Body (§4.2)

Standard markdown. Prefer structural markdown (headings, lists, tables, fenced
code) over prose. No body section is required. Conventional headings when
applicable: `# Schema`, `# Examples`, `# Computation` (§10). Per-claim
attribution uses markdown footnotes keyed to a `sources[].id` (see
[`trust-vocabulary.md`](trust-vocabulary.md)).

## Cross-linking and paths (§6)

- Links between concepts are **standard markdown links**. A link from A to B
  asserts a *relationship* (an untyped directed edge); the specific kind lives
  in the surrounding prose, not the link.
- **Bundle-relative form (recommended):** begins with `/`, resolved from the
  bundle root — `[customers](/tables/customers.md)`. Stable when a document
  moves within its subdirectory.
- **Relative form:** a normal relative path — `[other](./other.md)`.
- **Broken links are legal.** A link whose target does not exist is not
  malformed; it may be not-yet-written knowledge. Never reject a bundle for it —
  at most, emit an advisory.
- Path-valued frontmatter fields (`resource`, `sources[].resource`,
  `computation`, `executor.resource`, `attester.resource`) accept an absolute
  URL, a bundle-relative `/path`, or a relative path. A `sources[].resource` may
  instead be a *scope descriptor* (e.g. "all queries in project X"), which is
  not a path.
- The `references/` subdirectory (§6.3) conventionally mirrors external
  material, run instructions, or code as first-class concepts. Convention, not a
  requirement.

## Actor convention (§7)

Identity fields (`generated.by`, `verified[].by`, `sources[].author`) use one
convention:

- `<producer>/<version>` — agents and tools, e.g. `reference_agent/gemini-2.5-pro`.
- `human:<id>` — a person, e.g. `human:ahormati`.
- `process:<id>` — an automated process, e.g. `process:finance-nightly`.

Trust-tier classification keys off the `human:` prefix, so hand-authored or
human-confirmed content MUST use it. See tier derivation in
[`trust-vocabulary.md`](trust-vocabulary.md).

## Index files (§8)

An `index.md` MAY appear in any directory, including the root. It enumerates the
directory's contents for progressive disclosure. **No frontmatter**, except the
bundle-root `index.md` MAY carry `okf_version` (§12). Body = sections of link
lists:

```markdown
# Section / Group Heading

* [Title 1](relative-url-1) - short description
* [Title 2](relative-url-2) - short description

# Another Section

* [Subdirectory](subdir/) - short description
```

Entries SHOULD reuse the linked concept's `description`. Index files are
optional; a consumer may synthesize one when absent.

## Log files (§9)

A `log.md` MAY appear at any level. Flat list of date-grouped entries, newest
first. Date headings MUST be ISO 8601 `YYYY-MM-DD`. The leading bold word is a
convention, not a requirement:

```markdown
# Directory Update Log

## 2026-05-22
* **Update**: Added a BigQuery table reference for [Customer Metrics](/tables/customer-metrics.md).
* **Creation**: Established the [Dataplex Playbook](/playbooks/dataplex.md).

## 2026-05-15
* **Initialization**: Created foundational directory structure.
```

## Conformance (§11) — the whole test

A bundle is **conformant** with OKF v0.2 if:

1. Every non-reserved `.md` file contains a **parseable YAML frontmatter block**.
2. Every frontmatter block contains a **non-empty `type`** field.
3. Every reserved file (`index.md`, `log.md`) follows §8 / §9 when present.

That is the entire hard contract. When the trust / lifecycle / provenance /
computation families are present, producers SHOULD follow §5–§10, and consumers:

- MUST treat a bare `verified` mapping as a one-element list (§5.2).
- MUST NOT reject a concept for missing any optional family (§5.3).
- SHOULD derive trust tiers and staleness only from the specified fields.

Everything else is soft guidance. Consumers **MUST NOT reject** a bundle for:

- Missing optional frontmatter fields.
- Unknown `type` values.
- Unknown additional frontmatter keys.
- Broken cross-links.
- Missing `index.md` files.

This is why `okf-validate` reports these as **advisories, never as failures**.

## Versioning (§12)

- OKF revisions are `<major>.<minor>`. A **minor** bump adds
  backward-compatible optional fields / conventional headings; a **major** bump
  may rename required fields or reserved filenames.
- A bundle MAY declare its target version with **`okf_version: "0.2"`** in the
  **bundle-root `index.md` frontmatter** — **the only place frontmatter is
  permitted in any `index.md`**.
- Forward-compat rule: a consumer that does not understand the declared version
  SHOULD attempt best-effort consumption, not refuse the bundle. Preserve
  unknown keys so an additive bump does not break round-tripping.
