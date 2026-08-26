---
name: ai-pop-compiler
description: Sub-skill for validating the artist.json metadata contract, copying files, compiling typescript/Vite templates, and verifying static client builds.
license: Apache-2.0
---

# AI Pop Compiler

This skill handles validation, scaffolding, and client compilation checks. It utilizes the embedded Go CLI scaffolder program located inside the skill's assets directory.

## Embedded Resources

The complete Go-based scaffolder source code and its Web Component template bundles are bundled inside this skill:
*   [Go Main Program](assets/scaffolder/main.go)
*   [Web Component Templates](assets/scaffolder/templates.go)
*   [Go Mod definition](assets/scaffolder/go.mod)

By embedding this code, any agent loading this skill can instantly scaffold or maintain an artist page on-demand.

## Instructions

1. **Verify Contract:**
   * Confirm that the compiled `artist.json` file in the artist workspace is well-formed and matches our strict data contract schema.

2. **Compile the Go Scaffolder On-Demand:**
   * Before running the scaffolder, check if the executable is compiled. If not, build it from the embedded asset source.
   * **Note on Read-Only Environments:** If the skill folder is read-only, compile the binary directly to your writable target artist workspace:
     ```bash
     # Compile the Go CLI tool directly into the writable target workspace
     go build -o /path/to/artist_workspace/ai-pop-scaffolder \
       /path/to/skills/ai-pop-compiler/assets/scaffolder/main.go \
       /path/to/skills/ai-pop-compiler/assets/scaffolder/templates.go
     ```
   * Otherwise, if the environment is writable, you may build locally:
     ```bash
     cd assets/scaffolder
     go build -o ai-pop-scaffolder
     ```

3. **Run Scaffolder:**
   * Run the compiled binary on the target artist directory containing `artist.json`:
     ```bash
     /path/to/ai-pop-scaffolder --dir /path/to/artist_workspace
     ```
   * Confirm that all source files and media assets are written to the `web` subdirectory.

4. **Execute Compiler Check:**
   * Navigate into the newly created `web` folder.
   * Run `npm run build` to verify that the TypeScript compiler (`tsc`) and Vite successfully bundle the assets into `dist/` with no compilation errors.
