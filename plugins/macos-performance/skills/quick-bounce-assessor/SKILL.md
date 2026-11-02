---
name: quick-bounce-assessor
description: "Assesses macOS/SwiftUI app launch and runtime performance. Evaluates first-frame ('quick bounce') readiness by finding synchronous main-actor I/O on the launch path, Swift strict-concurrency posture, view-model vs business-logic separation, and steady-state render budget (high-frequency @Published timers, per-body allocations). Produces a PASS/WARNING/FAIL report with file:line evidence and phased fixes. Use when reviewing a macOS/SwiftUI or AppKit app for launch responsiveness, concurrency safety, or UI smoothness."
license: Apache-2.0
metadata:
  version: "1.0.0"
---

# Quick Bounce Assessor

A performance reviewer for macOS applications (SwiftUI and/or AppKit). The
"quick bounce" is the time from launch to the first rendered frame — a clean
bounce off the app icon. This skill assesses how quickly an app can render its
first frame and how well it sustains a smooth frame budget afterward.

## Guiding principle

> At the earliest point in the lifecycle, do all non-main-actor-necessary work
> **off** the main actor so a single SwiftUI/AppKit frame can render
> immediately. Publish results back to the main actor when ready.

## What it assesses

1. **Launch path / main-actor I/O** — synchronous disk reads, JSON decode,
   directory scans, or shell/env parsing running during `init`,
   `@StateObject`/`@State` construction, or `applicationDidFinishLaunching`
   before the first frame.
2. **Strict concurrency posture** — whether Swift strict concurrency is enabled;
   presence of unverified `@unchecked Sendable` promises.
3. **View-model ↔ business-logic separation** — god-object view models mixing UI
   state with orchestration/domain rules; appropriate (and inappropriate) use
   of `actor`.
4. **Steady-state render budget** — high-frequency timers mutating `@Published`
   state that invalidate large view trees; per-`body` allocations
   (`DateFormatter`, `JSONEncoder`/`JSONDecoder`).
5. **App lifecycle & window setup** — heavy work in the app delegate / scene
   setup; observation model (`@Observable` vs `ObservableObject`).

## How to run

1. Read `references/PERF_CATALOG.md` for the anti-pattern → detection → fix
   catalog.
2. Optionally run the heuristic scanner against the target project:
   ```bash
   scripts/scan_launch_path.sh /path/to/project
   ```
   It is read-only and advisory (always exits 0). Treat its output as leads to
   confirm by reading the flagged `file:line` locations.
3. For each lead, open the file and confirm whether the work truly runs on the
   main actor before the first frame (constructors reached from
   `@StateObject`/`@State`, singletons touched during that construction, app
   delegate launch methods).
4. Where possible, verify with Instruments (Time Profiler, `os_signpost`) — the
   scanner finds candidates; Instruments confirms real cost.

## Report format

Produce a structured report:

- A one-line verdict on quick-bounce readiness.
- Per finding: `PASS` / `WARNING` / `FAIL`, the category, `file:line` evidence,
  a short explanation, and a concrete fix.
- A phased remediation summary ordered by ROI:
  1. Clear the first-frame path (move I/O off main; publish back on `@MainActor`).
  2. Adopt strict concurrency incrementally (targeted → complete).
  3. Extract business logic from view models (plain services; actors only for
     shared mutable state; `AsyncStream` over Combine).
  4. Fix steady-state render budget (`TimelineView`/`Canvas`, static formatters).

## Instructions

When invoked to assess a codebase:
1. Identify the app type (SwiftUI/AppKit), platform, min OS, and build system.
2. Run `scripts/scan_launch_path.sh` on the project root, then verify each lead
   by reading the source.
3. Classify every finding PASS/WARNING/FAIL with `file:line` and a fix, mapping
   it to one of the five assessment categories.
4. Emit the phased remediation summary. Recommend `actor` only where shared
   mutable state genuinely crosses threads; prefer plain `Sendable` service
   types and `AsyncStream` over adding Combine pipelines.
