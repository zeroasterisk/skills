# Asciinema Explainer Walkthroughs & Terminal Demos

A skill and toolkit for creating deterministic, synchronous asciinema recordings (`.cast`) and interactive 2-tab web walkthroughs for AI coding agents and CLI tools.

## Features

- **Deterministic PTY Driving**: Interacts with subshells character-by-character while strictly waiting for bash prompts to return.
- **Smart Idleness Compression**: Shrinks 10+ minute LLM and container runs into 2-3 minute videos without clipping human reading pauses.
- **Redaction Pipeline**: Automatic token and secret sanitization for OAuth codes and API keys.
- **2-Tab Web Player Template**: Ready-to-deploy HTML/CSS template featuring hot-swappable asciinema streams and zoomable Mermaid decision flowcharts.

## Included Templates & Scripts

- `scripts/pty_recorder_template.py`: Reusable Python PTY recorder engine.
- `scripts/banner_template.sh`: ANSI color double-border banner generator.
- `templates/player_template.html`: Interactive 2-tab GitHub Pages web player with Dracula theme and Mermaid zoom toolbar.
