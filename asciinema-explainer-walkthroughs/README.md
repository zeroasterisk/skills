# Asciinema Explainer Walkthroughs & Terminal Demos

A production-grade skill and toolkit for creating deterministic, synchronous asciinema recordings (`.cast`) and interactive multi-tab web walkthroughs for AI coding agents and CLI tools.

## Key Features

- **Deterministic PTY Driving**: Interacts with subshells character-by-character while strictly waiting for shell prompts (`$PS1`) to return (0% command collision guarantee).
- **Smart Idleness Compression**: Shrinks 10+ minute LLM and container runs into 2-3 minute videos without clipping human reading pauses.
- **Comprehensive Redaction Pipeline**: Automatic token and secret sanitization for OAuth codes, API keys (Google, Anthropic, OpenAI, GitHub, AWS), and private key blocks.
- **ANSI Banner Generator**: Width-calibrated double/single/rounded border scenario headers with ANSI colors.
- **Interactive Multi-Tab Web Player**: Ready-to-deploy HTML template featuring hot-swappable asciinema streams, interactive chapter navigation sidebar, zoomable Mermaid decision flowcharts, full-text transcript search, and an interactive human reviewer rubric.
- **Walkthrough Builder & Preview Server**: CLI tool to parse `.cast` files, validate schema integrity, generate standalone `index.html`, and host a local review server.

## Included Toolkit

- `scripts/pty_recorder_template.py`: Reusable Python PTY recorder engine with typing jitter, assertion helpers, and secret redaction.
- `scripts/banner.py`: Width-calibrated ANSI double-border scenario header generator.
- `scripts/banner_template.sh`: Bash wrapper for banner generation.
- `scripts/build_walkthrough.py`: Builder and local HTTP preview server for compiling `.cast` recordings into interactive web walkthroughs.
- `templates/player_template.html`: Interactive multi-tab web player with chapter navigation and reviewer rubric.
- `tests/test_pty_recorder.py`: Automated verification suite for the recorder, compression, redactions, and player builder.

## Quick Start

### 1. Run Unit & Integration Tests
```bash
python3 -m unittest discover -s tests -v
```

### 2. Generate a Banner
```bash
python3 scripts/banner.py --step 1 "Capability Search" "Agent queries catalog for matching tools" --color green
```

### 3. Record a Session
```bash
python3 scripts/pty_recorder_template.py
```

### 4. Build Walkthrough & Preview
```bash
python3 scripts/build_walkthrough.py --cast demo.cast --output index.html --serve --port 8080
```
