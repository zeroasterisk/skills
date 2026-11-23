# C2PA Inspector Plugin (`c2pa-inspector`)

An [Agent Plugins v1.0.0](https://github.com/agentplugins/agent-plugins-spec) package providing comprehensive C2PA (Coalition for Content Provenance and Authenticity) Content Credentials inspection, verification, and batch auditing capabilities for AI agents and developers.

> **Disclaimer:** This project is an open-source community contribution and is not an officially supported Google product.

---

## Overview

The `c2pa-inspector` plugin enables autonomous agents and command-line developers to inspect media assets (images, videos, audio, and documents) for embedded C2PA provenance metadata. Built on [Google Credentio](https://mediaprovenance.googlesource.com/credentio/), it audits cryptographic assertions, claim generators, signing certificates, and AI generation/training flags.

### Key Capabilities

- **Single and Multi-Asset Auditing:** Inspect single files, explicit lists of paths, or entire directory trees recursively.
- **Dual-Engine Execution:** Uses native Google Credentio C-ABI via CFFI for complete cryptographic trust validation when available, paired with a zero-dependency pure-Python media container and JUMBF parser fallback.
- **AI Provenance and Training Consent:** Detects generative AI attribution (`trainedAlgorithmicMedia`), generative model prompts and metadata, and training/mining restrictions (`c2pa.ai_generative_training`, `cawg.data_mining`).
- **Agent-Ready JSON:** Generates structured JSON output optimized for tool-calling agents and automated evaluation pipelines.
- **Specification Conformance:** Fully conforms to the Agent Plugins v1.0.0 Specification and Agent Skills Specification.

---

## Plugin Structure

```text
c2pa-inspector/
├── plugin.json               # Agent Plugins v1.0.0 manifest
├── LICENSE                   # Apache 2.0 license
├── README.md                 # Documentation and usage guide
└── skills/
    └── c2pa-inspect/         # Core inspection skill
        ├── SKILL.md          # Skill definition and agent instructions
        ├── scripts/
        │   ├── inspect_c2pa.py       # Dual-engine CLI and batch inspector
        │   └── fetch_native_lib.sh   # Prebuilt libcredentio_c binary fetcher
        ├── references/
        │   ├── c2pa-spec-guide.md    # C2PA assertions, schemas, and taxonomies
        │   ├── badge-states.md       # Validation criteria and status semantics
        │   └── ai-provenance.md      # AI attribution and training-mining guide
        └── assets/
            ├── sample_crjson_v1.json # C2PA v1 sample manifest fixture
            ├── sample_crjson_v2.json # C2PA v2 sample manifest fixture
            └── sample_ai_manifest.json # AI provenance metadata fixture
```

---

## Quick Start

### 1. Inspect a Single Asset

```bash
python3 skills/c2pa-inspect/scripts/inspect_c2pa.py sample.jpg
```

### 2. Inspect a Directory with Recursive Scanning

```bash
python3 skills/c2pa-inspect/scripts/inspect_c2pa.py --dir ./media --recursive
```

### 3. Generate Machine-Readable JSON for Agent Tooling

```bash
python3 skills/c2pa-inspect/scripts/inspect_c2pa.py asset1.jpg asset2.png --json
```

### 4. Filter by Provenance Status

```bash
# Filter only assets with AI attribution or generative provenance
python3 skills/c2pa-inspect/scripts/inspect_c2pa.py --dir ./assets --filter ai-only

# Filter only unsigned assets requiring credentials
python3 skills/c2pa-inspect/scripts/inspect_c2pa.py --dir ./assets --filter unsigned
```

---

## Supported Media Formats

| Format | Extensions | Detection Method |
|---|---|---|
| JPEG | `.jpg`, `.jpeg` | APP11 marker (`0xFFEB`) JUMBF superbox |
| PNG | `.png` | `caPt` / `caPI` chunk |
| WebP | `.webp` | RIFF `JUMB` chunk |
| AVIF / HEIC | `.avif`, `.heic` | ISOBMFF `ftyp` and `c2pa` / `uuid` box |
| MP4 / MOV | `.mp4`, `.mov` | ISOBMFF `moov` / `uuid` box |
| Audio | `.mp3`, `.wav`, `.flac`, `.m4a` | ID3, RIFF `JUMB`, or container boxes |
| Manifest | `.c2pa` | Standalone C2PA manifest store |

---

## License

This project is licensed under the Apache 2.0 License.
