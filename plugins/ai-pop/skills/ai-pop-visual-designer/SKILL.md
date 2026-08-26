---
name: ai-pop-visual-designer
description: Sub-skill for generating cohesive album cover art and track illustrations using NanoBanana.
license: Apache-2.0
---

# AI Pop Visual Designer

This skill coordinates the generation of cohesive visual artwork. It supports both local workspace execution and remote/managed agent execution via GCS staging.

## Instructions

1. **Resolve Output Storage Mode:**
   * **Local Mode (Default):** Pass `output_directory` pointing to the target local workspace directory.
   * **Managed Agent / GCS Mode:** When executing inside a managed agent container where the MCP server runs remotely on Cloud Run, pass `gcs_bucket_uri` (or set `GENMEDIA_BUCKET`) pointing to the mounted GCS environment bucket.

2. **Formulate Imagery Parameters:**
   * Ensure prompts use detailed art styles (e.g., *"detailed lofi illustration, watercolor and ink, retro gradient, synthwave vibe"*) and embed the artist's primary and secondary color tokens.

3. **Generate Cover Art:**
   * Invoke `nanobanana_image_generation` with a `1:1` aspect ratio and `output_filename` set to `album_art.png`.

4. **Generate Track Illustrations:**
   * Generate an illustration for each track in the tracklist, saved as `track[N]_art.png`.

5. **Compression & Formatting:**
   * Verify that output files are standard PNG/JPG files and reside in the root of the project workspace or mounted GCS directory.
