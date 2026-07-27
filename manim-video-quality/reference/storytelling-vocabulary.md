# Storytelling & Manim Toolbox — Cheatsheet

> Shared vocabulary for talking about Agent Platform videos. Use these terms
> in feedback so we both mean the same thing quickly. Add to this file as we
> discover new patterns — it's a living toolbox, not a fixed spec.

---

## Narrative structure terms

| Term | Definition |
|---|---|
| **Beat** | The smallest unit of narrative — one animation, one small idea landing. A scene is made of several beats. ("The badge Flash is one beat.") |
| **Vignette** | A short, self-contained sub-story within the video that makes one point, often not strictly required for the main arc but adds context or texture. (e.g. "the 4 identity types vignette.") |
| **Pillar** | One of several parallel, roughly-equal-weight concepts the video is structured around (we used "3 pillars": Identity, Gateway, Observability). Pillars are usually presented in sequence with a consistent visual treatment so the viewer recognizes the pattern by the 2nd one. |
| **The Aha Moment** | The single idea the whole video is building toward — there should be exactly ONE per video. Everything before it is setup; everything after it is a brief close. If you can't name the one-sentence aha, the video doesn't have a spine yet. |
| **Payoff** | A moment that resolves tension set up earlier — visually or narratively. Strongest when it reuses the *same object* from the setup (see Persistence Contract) rather than introducing something new that merely resembles it. |
| **Persistence Contract** | A rule we set for a specific video: certain mobjects (e.g. the chaotic network lines) must survive, dimmed, across several scenes and be explicitly `Restore`d/`Transform`ed later — never `FadeOut`'d and recreated — so the payoff reads as "the same thing, transformed" rather than "a new, different, cleaner diagram." |
| **Three-Act Structure** | Problem (tension) → Solution (mechanism) → Resolution (the aha, generalized). Useful as a first pass; not every video needs exactly three acts, but almost every video needs SOME version of tension-then-release. |
| **Chaos-to-Order Arc** | A specific payoff pattern: show a deliberately illegible/overwhelming state early, then later transform that exact same visual object into something legible. Reads as "look how much better this is" more convincingly than showing clean-then-cleaner. |
| **Cold Open** | Starting a video/scene with the visual or an intriguing fragment before any explanatory text — used to earn attention before spending the viewer's patience on exposition. |
| **Landscape / Taxonomy Vignette** | A scene whose only job is to establish "here are the pieces on the board" (e.g. the Agent Frameworks / Agent Harnesses split) before the main narrative uses a subset of them. Purely orienting, not yet making an argument. |

## Manim / visual technique terms

| Term | Definition |
|---|---|
| **Morph** | Using `Transform`/`ReplacementTransform` so object A visibly becomes object B, rather than A disappearing and B appearing separately. The 3b1b signature move — always prefer this when the "before" and "after" are conceptually the same thing. |
| **Camera Reveal** | Using `MovingCameraScene`'s `self.camera.frame.animate` to pan/zoom into new context, instead of cutting to a new static composition. Feels like the world is bigger than the frame, not like slides changing. |
| **LaggedStart Burst** | `LaggedStart(*animations, lag_ratio=X)` — a group of similar objects appearing in a staggered wave rather than all at once. Higher `lag_ratio` = more staggered = calmer; low `lag_ratio` (near simultaneous) reads as chaotic/urgent (used intentionally in the "sprawl" scene). |
| **Dim-and-Restore** | The Manim mechanic behind the Persistence Contract: `mobject.save_state()` early, `.animate.set_opacity(low)` to dim, later `Restore(mobject)` to bring it back to its saved state exactly. |
| **Hub-and-Spoke Layout** | A layout where one central node connects to many peripheral nodes via straight lines — the canonical "clean" resolution shape after a chaos-to-order arc. |
| **Span Waterfall** | An OpenTelemetry/Cloud-Trace-style visualization: horizontal bars on a millisecond timeline, nested by depth, representing a request's execution trace. A legitimate, recognizable observability idiom — treat departures from horizontal-Gantt as a red flag, not a creative opportunity. |
| **Ceremony** | A small multi-beat sequence that dramatizes a normally-invisible technical event (e.g. the "agent gets its identity badge" sequence: approach → flash → badge appears → return). Useful for making abstract infrastructure concepts feel concrete and memorable. |
| **Representative Subset** | When a full taxonomy (e.g. 11 agent frameworks/harnesses) is too dense to reuse in every later diagram, explicitly narrow to a smaller "cast" (e.g. 6) and say so on screen ("let's follow six of them") rather than silently dropping items. |
| **Fake Bold / Phantom Gap** | A rendering bug class where a font lacks a true bold face (or is a `.ttc` collection) and Pango/HarfBuzz mis-shapes text — symptoms include synthetic-bold artifacts or spurious spaces inside single words. Always spot-check new fonts against known compound-word test strings before adopting. |

## Color & typography discipline

| Term | Definition |
|---|---|
| **Reserved Color** | A color used ONLY for one specific meaning throughout a video (e.g. Google Red only ever means "blocked/denied"). The discipline is what makes color legible — the moment a reserved color is reused decoratively, it stops carrying information. |
| **Explanatory Palette vs. Brand Palette** | Two color layers in our hybrid style: the desaturated 3b1b-style palette explains generic concepts (nodes, lines, abstract shapes); the exact Google brand hexes are reserved for "this is the product" or semantic verdicts. Keeping them visually distinct preserves the brand palette's signal value. |
| **Card-itis** (anti-pattern) | Overusing opaque, drop-shadowed `RoundedRectangle` "cards" that make a Manim scene look like a software dashboard mockup instead of an idea explainer. Fix: lower fill_opacity, remove shadows, let the dark background show through. |

## Pacing & QA process terms

| Term | Definition |
|---|---|
| **Incremental QA** | Running the QA tool (Pass 1 only, cheap) against a `-ql` render of ONE scene or a small cluster, before assembling the full video — catches layout/legibility bugs while the blast radius is small. See `video-qa` skill. |
| **Context File** | A markdown file passed to the QA tool (`--context-file`) explaining the video's intentional narrative choices (e.g. "this chaos is deliberate") so the grading model doesn't penalize intentional design as a defect. |
| **Gate** | The Pass 1 QA score threshold (≥6.5) that must be cleared before Pass 2 (marketing) runs. A hard floor — broken/overlapping visuals cap the score regardless of content quality. |
| **Pilot Scene** | A single small scene rebuilt first when adopting a new visual style or technique, specifically to calibrate before applying the change everywhere. Cheaper to iterate on than the full video. |
| **Review Log** | A persistent `REVIEW.md` per video tracking each piece of feedback with a status (open/fixed/verified) — survives across sessions better than chat history. |

---

## Open questions / things we're still calibrating

- How much on-screen text is too little? 3b1b often uses almost none;
  developer-audience technical content may need slightly more than a pure
  math explainer, but current drafts likely have too much.
- Where exactly is the line between "Google brand color, reserved" and
  "looks inconsistent because everything else is desaturated"? Needs a
  pilot scene to see in motion, not just reason about in the abstract.
- Font: **Roboto confirmed clean** (2026-07-05) — reproduced the exact
  phantom-gap bug with Helvetica Neue at `font_size=15, weight=BOLD` in the
  actual `make_agent()` node construction ("LangChain"→"Lang Chain",
  "Pydantic"→"Pyd antic", "OpenClaw"→"Op enClaw", "Antigravity"→"Antig
  ravity", verified at 4K to rule out compression artifacts), then re-ran
  the identical test with Roboto — all four render correctly with no gaps.
  Roboto is now the default font going forward. Still worth testing "Google
  Sans" per-weight files for a more on-brand look, if a non-.ttc version is
  available, using this same repro test before adopting.
