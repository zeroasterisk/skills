# C2PA Specification and Architecture Guide

A technical reference for the Coalition for Content Provenance and Authenticity (C2PA) metadata structures, JUMBF packaging, assertion taxonomy, and JSON manifest schemas.

---

## 1. C2PA Architecture Overview

C2PA defines an open technical standard that enables creators and publishers to attach cryptographically verifiable provenance to digital media.

```text
+-------------------------------------------------------------------+
| Media Container (JPEG, PNG, MP4, WebP, AVIF)                      |
|                                                                   |
|  +-------------------------------------------------------------+  |
|  | C2PA Manifest Store (JUMBF Superbox)                        |  |
|  |                                                             |  |
|  |  +-------------------------------------------------------+  |  |
|  |  | Active Manifest                                       |  |  |
|  |  |  - Claim Generator (e.g. Adobe Photoshop, Credentio)  |  |  |
|  |  |  - Signature & Cert Chain (X.509, TSA timestamp)       |  |  |
|  |  |  - Assertions (actions, hash, ingredients, AI flags)  |  |  |
|  |  +-------------------------------------------------------+  |  |
|  |                                                             |  |
|  |  +-------------------------------------------------------+  |  |
|  |  | Ingredient Manifests (Parent / Input Assets)           |  |  |
|  |  +-------------------------------------------------------+  |  |
|  +-------------------------------------------------------------+  |
+-------------------------------------------------------------------+
```

---

## 2. Container Embeddings

C2PA packages manifests inside ISO/IEC 19566-5 JPEG Universal Metadata Box Format (JUMBF) structures:

- **JPEG:** APP11 application markers (`0xFFEB`) with JUMBF superbox encapsulation (`0x6A756D62`).
- **PNG:** Dedicated chunk types `caPt` (Content Authenticity Passthrough) or `caPI`.
- **MP4 / MOV:** ISOBMFF `uuid` box keyed to C2PA UUID `d8f03db5-4c9b-4263-8e54-11351c7b73d9`, or root `c2pa` box.
- **WebP:** RIFF container with a `JUMB` chunk identifier.
- **AVIF / HEIC:** BMFF item references referencing the `c2pa` metadata item.
- **Standalone:** Files with `.c2pa` extension containing the raw serialized manifest store.

---

## 3. Schema Variations: C2PA v1.x vs v2.x

Parsers must handle both legacy C2PA v1 schemas and modern C2PA v2 schemas resiliently:

| Feature | C2PA v1 Schema | C2PA v2 Schema |
|---|---|---|
| Claim Block | `claim` object | `claim.v2` or `claim` |
| Generator Info | `claim.claim_generator_info` (object or array) | Array of `{ name, version }` objects |
| Certificate Info | `signature_info.issuer` (flat string) | `signature_info.certificateInfo.issuer.CN` |
| Assertions Format | Key-value dictionary indexed by URI | Array of `{ label, data }` items |
| Action Assertion | `c2pa.actions` | `c2pa.actions.v2` |
| Validation Output | `validation.status` array | Categorized `validationResults.{success, failure, informational}` |

---

## 4. Standard Assertions Dictionary

- **`c2pa.actions` / `c2pa.actions.v2`:** Records editing history (created, edited, converted, color_adjustments, cropped).
- **`c2pa.hash.data` / `c2pa.hash.bmff.v3`:** Cryptographic digest over the asset content bytes for tamper detection.
- **`c2pa.ingredient`:** References upstream source assets, thumbnail representations, and prior manifests.
- **`c2pa.training-mining`:** Machine learning training and data mining consent declarations.
- **`c2pa.digital_source_type`:** Standard IPTC digital source categorization (e.g. digitalCapture, trainedAlgorithmicMedia).
