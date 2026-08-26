---
name: okf-validate
description: Validate an Open Knowledge Format (OKF) v0.2 knowledge bundle for §11 conformance and trust-signal well-formedness, reporting everything as advisories and never rejecting a bundle for optional, unknown, or broken content. Checks that every non-reserved markdown file has parseable frontmatter with a non-empty type, that a root index.md declaring okf_version and any log.md follow their reserved structure, and that provenance/trust frontmatter is well-formed (actor convention, generated/verified shape, no stored credibility score). Prefers shelling out to an installed validator (okfcli/okf validate, factile, openknowledge) but falls back to explaining and running the checks entirely by hand with zero OKF binaries. Use when asked to validate, lint, or conformance-check an OKF bundle.
license: Apache-2.0
metadata:
  version: "1.0.0"
---

# Validate an OKF v0.2 bundle

This skill checks a bundle against **OKF v0.2 §11 conformance** and the
well-formedness of its optional trust vocabulary, and produces an **advisory
report**. It never "fails" a bundle for optional, unknown, or broken content —
OKF is deliberately permissive, and a validator that rejects such things is
wrong, not strict.

*Note: This skill references shared plugin documentation (`../../references/`) and is designed to be installed as part of the `okf-authoring` plugin.*

**Tool-agnostic by design.** The full check runs **by hand with zero OKF binaries
installed**. If a validator is installed you MAY shell out to it first, but the
by-hand path is always available (see [Prefer a validator, fall back by
hand](#prefer-a-validator-fall-back-by-hand)).

## Load these when you need them (progressive disclosure)

- [`../../references/okf-v0.2-spec-summary.md`](../../references/okf-v0.2-spec-summary.md)
  — conformance (§11), reserved-file structure (§8/§9), cross-linking (§6). **The
  spec version is pinned there, once.**
- [`../../references/trust-vocabulary.md`](../../references/trust-vocabulary.md)
  — the provenance / trust / lifecycle field shapes to check optional frontmatter
  against.

## The reject/advise rule (do not get this wrong)

There are exactly **three** hard conformance requirements (§11). Everything else
is an **advisory** — surfaced to help the author, never a rejection.

**Hard requirements — a bundle is non-conformant only if one of these fails:**

1. A non-reserved `.md` file lacks a **parseable YAML frontmatter block**.
2. A frontmatter block has **no non-empty `type`** field.
3. A reserved file (`index.md`, `log.md`) is present but **violates its
   structure** (§8 / §9) — e.g. a non-root `index.md` carries frontmatter, or the
   root `index.md` puts anything other than `okf_version` in frontmatter.

**Advisory only — MUST NOT cause rejection (§11):**

- Missing optional frontmatter fields (`title`, `description`, `generated`, …).
- Unknown `type` values.
- Unknown / additional frontmatter keys.
- Broken cross-links (a link whose target file doesn't exist).
- Missing `index.md` files.
- Trust-signal shape issues (below) — report, don't reject.

## Procedure

### 1. Enumerate the bundle

List every `.md` file in the tree. Classify each as **reserved** (`index.md`,
`log.md`) or a **concept** (everything else).

### 2. Conformance checks (§11) — these can be non-conformant

For each **concept** file:

- **Frontmatter present & parseable.** File starts with `---`, has a closing
  `---`, and the block is valid YAML. → *fail #1* if not.
- **Non-empty `type`.** The block has a `type:` key with a non-empty value. →
  *fail #2* if not.

For each **reserved** file:

- `index.md` **not at the bundle root** → MUST have **no frontmatter**. → *fail
  #3* if it does.
- **Root** `index.md` → frontmatter, if any, contains **only** `okf_version`
  (value `"0.2"` for this spec version). Any other key there → *fail #3*.
- `log.md` → date headings are ISO 8601 `YYYY-MM-DD`. Malformed structure →
  *fail #3*; loose prose in entries is fine.

### 3. Trust well-formedness checks — advisory only

When the optional families are present, check shape and report advisories (load
[`trust-vocabulary.md`](../../references/trust-vocabulary.md) for exact shapes):

- **Actor convention (§7):** `generated.by` and every `verified[].by` match
  `<producer>/<version>`, `human:<id>`, or `process:<id>`. Flag anything else.
- **`generated`:** if present, has `by` (required within it); `at` is ISO 8601.
- **`verified`:** a list of `{ by, at }`, **or** a single bare mapping (which is a
  valid one-element list — do **not** flag it). `at` is ISO 8601.
- **`sources`:** each entry has `resource`; `last_modified` is `YYYY-MM-DD`;
  footnote citations reference an existing `sources[].id`.
- **`status`** ∈ {`draft`, `stable`, `deprecated`}; **`stale_after`** is an
  absolute `YYYY-MM-DD`.
- **No stored verdict:** flag any `credibility` / `score` / `trust` / `tier`
  frontmatter key — trust tiers must be **derived** from `verified`, not stored
  (§5.3). Report the *derived* tier instead (unverified / machine-confirmed /
  human-reviewed).
- **Attested Computation:** if `type: Attested Computation`, `runtime` is
  present; `computation` is inline (`# Computation` fence) *xor* a `computation:`
  path. Runtime receipts must **not** be committed to the bundle.

### 4. Link advisories — never a rejection

Resolve each markdown link between concepts. A link whose target file does not
exist is a **broken-link advisory**, not an error — it may be not-yet-written
knowledge (§6). List them so the author can decide, and stop there.

### 5. Report

Produce a report with three clearly separated sections:

1. **Conformance verdict** — `conformant` / `non-conformant`, listing only true
   §11 failures (checks in step 2). This is the only pass/fail line.
2. **Advisories** — trust-shape, actor-convention, and other soft findings
   (step 3), each with file + line.
3. **Broken links** — the list from step 4.

Also surface each concept's **derived trust tier** and **staleness**
(`today >= stale_after`) as informational output — derived on read, never taken
from a stored field. Today's date for the staleness comparison should be the
current date at validation time.

## Prefer a validator, fall back by hand

If an OKF validator is already installed, you MAY run it first and fold its
output into your report — then still apply the reject/advise rule above, since
some tools are stricter than the spec permits:

- `okf validate <bundle>` (from `okfcli/okf`) — checks OKF v0.2 §11 conformance;
  JSON-by-default, structured error envelopes. Install per its repo
  (`github.com/okfcli/okf`) only if you want it.
- `binder validate <bundle>` (from `ghchinoy/binder`) — OKF v0.2 §11 conformance.
- `factile` / `openknowledge` — offer `validate`-style commands.

Detect availability first (e.g. `command -v okf`, `command -v binder`). **If none
are installed, run the by-hand checks above** — that is the expected default, and
it is complete on its own. When a tool reports a "failure" that the spec treats
as advisory (unknown key, broken link, unknown type), **downgrade it to an
advisory** in your report and say why.

## Validating a whole corpus / driving binder end-to-end → the `okf-convert` skill

The checks above validate a **single** bundle — by hand, with zero binaries, or
by folding in an installed validator. When the job is instead to **ingest an
existing markdown corpus** into OKF and validate it as part of driving binder
end-to-end (`convert → validate → review`), especially for **deterministic,
offline/CI, provenance-preserving** work at scale, hand off to the named,
purpose-built skill:

- **The binder `okf-convert` skill** (the `okf-convert` Agent Skill in the
  `okf-convert` plugin from `ghchinoy/binder`) drives the `binder` CLI and
  reasons over its structured `--json` output — including `binder validate --json`
  for §11 conformance — instead of scraping prose. It carries the
  ingestion-analysis judgment (pre-convert triage, trust-extraction review, the
  post-convert acceptance loop) that single-bundle validation does not. Install
  it with:

  ```
  /plugin marketplace add ghchinoy/binder
  ```

  It **assumes binder is installed** and **never fabricates trust** (no auto
  `verified`, no invented `sources`, no stored tier). **Stay in this skill
  (Layer A)** for validating an individual bundle and for any **zero-binary
  environment** — this handoff adds no binary dependency.

## Sources

- Open Knowledge Format (OKF) SPEC.md v0.2 — GoogleCloudPlatform/knowledge-catalog, okf/SPEC.md
