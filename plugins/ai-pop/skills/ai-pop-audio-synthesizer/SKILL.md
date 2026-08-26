---
name: ai-pop-audio-synthesizer
description: Sub-skill for composing high-fidelity music tracks via Google DeepMind Lyria and verifying container formats.
license: Apache-2.0
---

# AI Pop Audio Synthesizer

This skill handles the synthesis and verification of music audio assets. It supports both local workspace execution and remote/managed agent execution via GCS staging.

## Instructions

1. **Resolve Output Storage Mode:**
   * **Local Mode (Default):** Pass `local_path` pointing to the target local workspace and set naming scheme (`track[N].wav`).
   * **Managed Agent / GCS Mode:** When executing inside a managed agent container where the MCP server runs remotely on Cloud Run, pass `output_gcs_bucket` (or set `GENMEDIA_BUCKET`) and `output_filename` (`track[N].wav`). The generated file will be staged directly into the mounted GCS environment bucket.

2. **Invoke Lyria 3 Pro:**
   * Call `lyria_generate_music` with the target prompt using the resolved storage parameters.
   * **Robust Model Fallback:** If `lyria-3-pro-preview` encounters API response issues or rate limits, immediately fallback and retry using `lyria-3-clip-preview` or `lyria-002` to ensure consistent and uninterrupted synthesis.

3. **Verify Stream Container:**
   * Run the shell `file` command (or inspect GCS metadata) to check the underlying container encoding (e.g. `file track1.wav`).
   * **CRITICAL:** If the tool reports that the file contains an MPEG layer III (MP3) stream, **rename the file extension to `.mp3`** (e.g. `track1.mp3`) instead of saving it as a `.wav`. This ensures browser decoding compatibility.

4. **Format Check:**
   * Verify the file exists, has a non-zero size, and matches the configuration expected by the Go compiler.
