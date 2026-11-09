# macOS / SwiftUI Performance Catalog

Anti-pattern → detection → fix reference for the `quick-bounce-assessor` skill.
Grouped by assessment category. "Quick bounce" = time-to-first-rendered-frame.

---

## 1. Launch path / main-actor I/O

### 1.1 Synchronous I/O in `init` reached from `@StateObject`/`@State`
**Why it hurts:** view-model constructors run on the main actor during view
construction, before the first frame. Any disk read/decode blocks the bounce.

**Detect:** inside `init(` bodies — `Data(contentsOf:`, `String(contentsOf:`,
`contentsOfDirectory`, `JSONDecoder().decode`, `FileManager` reads, or calls to
`load*/scan*/decode*` helpers. Trace which objects are built as
`@StateObject`/`@State` at app entry.

**Fix:** initialize with empty/default state; load asynchronously in a `Task`
or `.task`, then assign `@Published`/observed state back on `@MainActor`. Run
the pure decode/scan off-main (`Task.detached` or a `nonisolated` async func).

### 1.2 Singletons that do I/O in their initializer
**Why it hurts:** a `static let shared` whose `init` parses files runs that work
synchronously on whichever thread first touches it — often main, during launch.

**Detect:** `static let shared = Type()` where `init` reads/parses files
(`.zshrc`, `.env`, credentials probes, config).

**Fix:** make the initializer cheap; expose an explicit `async load()` awaited
before first use (e.g., before the first network/subprocess call), not lazily on
main.

### 1.3 Heavy work in `applicationDidFinishLaunching` / scene setup
**Detect:** file I/O, network, or large allocations in `NSApplicationDelegate`
methods or `App`/`Scene` initializers.

**Fix:** defer nonessential work; kick off async after the window is shown.

---

## 2. Blocking / allocating in `body`

### 2.1 Work inside a SwiftUI `body` getter
**Why it hurts:** `body` can run many times per second; any I/O, network, or
heavy compute there multiplies.

**Detect:** file/network calls or sorting/decoding inside `var body`.

**Fix:** precompute in the view model; expose ready-to-render state.

### 2.2 Per-render allocations
**Detect:** `DateFormatter(`, `JSONEncoder(`, `JSONDecoder(`,
`NumberFormatter(` constructed inside `body` or computed properties used by
`body`.

**Fix:** hoist to a `static let` shared instance, or use `Date.FormatStyle` /
`.formatted(...)`.

---

## 3. Strict concurrency posture

### 3.1 Strict concurrency not enabled
**Why it hurts:** hand-maintained concurrency invariants are unverified; data
races ship silently.

**Detect:** no `swiftSettings` with `.enableUpcomingFeature("StrictConcurrency")`
or `.enableExperimentalFeature("StrictConcurrency")` in `Package.swift`; no
`SWIFT_STRICT_CONCURRENCY` build setting; no Swift 6 language mode.

**Fix:** enable per target, **targeted** first then **complete**, resolving
warnings before bumping the language mode. Adopt incrementally, module by module.

### 3.2 Unverified `@unchecked Sendable`
**Why it hurts:** `@unchecked` is a promise the compiler cannot check. Under
minimal checking these accumulate untested.

**Detect:** `@unchecked Sendable` conformances.

**Fix:** with strict concurrency on, verify each holds; remove `@unchecked`
where the compiler can prove `Sendable`; keep it only for genuinely
lock-guarded types, documented.

---

## 4. View-model / business-logic separation

### 4.1 God-object view model
**Detect:** a single `ObservableObject`/`@Observable` VM of many hundreds of
lines mixing UI state with orchestration, queueing, selection, persistence
side-effects, and inline `print` logging.

**Fix:** keep the VM a thin `@MainActor` holder of observed state; extract plain
`Sendable` service types (e.g. `QueueService`, `Selector`, `Composer`) it calls.

### 4.2 Over-use (or mis-use) of `actor`
**Why it matters:** wrapping main-actor UI logic in actors adds `await` hops and
reentrancy hazards for logic that isn't contended.

**Rule:** use `actor` only where shared mutable state genuinely crosses threads
(e.g. a subprocess/JSON-RPC transport). For everything else prefer plain
`Sendable` types on the appropriate actor.

### 4.3 Message passing: prefer structured concurrency over Combine
**Detect:** new Combine `sink`/subjects added for coordination in a codebase
that otherwise uses `async/await`.

**Fix:** use `async/await` + `AsyncStream` (which an `actor` can vend) rather
than Combine pipelines. Combine used only for `@Published` is fine; don't grow
it.

### 4.4 Observation model
**Detect:** `ObservableObject` + `@Published` where fine-grained invalidation
matters.

**Fix (macOS 14+):** consider the `@Observable` (Observation) macro for narrower
view invalidation — only views reading a changed property re-render.

---

## 5. Steady-state render budget

### 5.1 High-frequency timer mutating `@Published`
**Why it hurts:** a 20–60 Hz timer that writes `@Published` state invalidates
every observing view each tick.

**Detect:** `Timer(timeInterval: <small>` or `Timer.scheduledTimer` /
`DispatchSourceTimer` whose handler mutates `@Published`/observed state
(metering, progress, animations).

**Fix:** drive continuous visuals with `TimelineView` + `Canvas` so the tick
doesn't invalidate the SwiftUI subtree; decouple the meter/sample source from
published state; coalesce updates.

### 5.2 Expensive view bodies re-run each tick
**Detect:** views iterating many elements with gradients/shadows/springs rebuilt
on each state publish.

**Fix:** render in `Canvas`; minimize per-element modifiers; use `drawingGroup()`
judiciously; avoid `.shadow` in hot loops.

---

## Verification

The scanner finds candidates; confirm with **Instruments**:
- **Time Profiler** — main-thread time during launch and playback.
- **os_signpost** — bracket launch phases and hot loops to measure real cost.
- **SwiftUI instrument** — view body counts / invalidations.
