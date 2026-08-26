---
name: ai-pop-producer
description: Primary orchestrator skill for creating concept-driven AI Pop Artists. Use when a user asks to generate a new artist profile, album narrative, audio-visual assets, local web-player dashboard, and hosted live endpoint.
license: Apache-2.0
metadata:
  version: "1.0.0"
---

# AI Pop Producer (Primary Orchestrator)

This skill coordinates the generation, compilation, and live hosting of virtual, bespoke musicians based on a high-level theme or mood. It orchestrates five specialized sub-skills to handle lore creation, audio generation, visual design, software scaffolding, and public hosting deployment.

## Execution Workflow

When a theme or mood is provided, execute the following steps in sequence:

1. **Creative Concept Planning**
   * Activate and delegate to [ai-pop-concept-planner](../ai-pop-concept-planner/SKILL.md).
   * Prompt the sub-skill with the user's base mood/theme to draft the name, lore, album, tracklist, and visual color guidelines.

2. **Audio Composition Synthesis**
   * Activate and delegate to [ai-pop-audio-synthesizer](../ai-pop-audio-synthesizer/SKILL.md).
   * Pass the tracklist prompt blueprints generated in Step 1 to synthesize and verify high-fidelity `.mp3` master files using Lyria.

3. **Visual Artwork Synthesis**
   * Activate and delegate to [ai-pop-visual-designer](../ai-pop-visual-designer/SKILL.md).
   * Pass the color palettes and scene prompt blueprints generated in Step 1 to generate the album cover and track-specific illustrations using NanoBanana.

4. **Verify, Compile and Scaffold**
   * Activate and delegate to [ai-pop-compiler](../ai-pop-compiler/SKILL.md).
   * Save the master metadata contract to `artist.json` and invoke the compiled Go CLI scaffolder to build, install, and bundle the final Vite + Lit + Material 3 interactive web-player.

5. **Publish and Host Public Endpoint**
   * Activate and delegate to [ai-pop-publisher](../ai-pop-publisher/SKILL.md).
   * Deploy the compiled `web/dist` bundle to a public endpoint (Firebase Hosting or GCS static website bucket) and return the live verified URL to the user.

## Common Edge Cases
* **MCP Failures:** If an audio or image generation tool encounters rate limits or errors, retry with a slightly simplified prompt or report back the failure within the active sub-skill.
* **Mismatched Formats:** Ensure that raw audio from Lyria is outputted or renamed to `.mp3` to prevent browser `<audio>` decoder issues.
