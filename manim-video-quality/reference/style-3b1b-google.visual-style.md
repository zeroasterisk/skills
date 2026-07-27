---
name: "3Blue1Brown x Google Agent Platform"
version: "1.0"
tags:
  - math-explainer
  - dark-theatrical
  - technical-minimalism
author: "Alan Blount + CloudCode"
source_url: "https://www.3blue1brown.com/"
created: "2026-07-05"

style_prompt_short: >
  3Blue1Brown's dark, patient, idea-first explainer grammar — one clear
  object per beat, generous negative space, morph-driven continuity — with
  Google's brand palette introduced subtly, reserved for the product itself
  and semantic states (confirm/alert), not as general decoration.

style_prompt_full: >
  A dark theatrical canvas (near-black #0E0E10 or true black #000000
  background) in the visual grammar of 3Blue1Brown: one idea, one clear
  focal object, on screen at a time. Generous negative space — most of the
  frame is empty at any given moment. Objects are simple geometric primitives
  (lines, circles, thin rounded rectangles) rendered with THIN strokes
  (stroke_width 2-3, never thick filled UI-chrome blocks) and LOW fill
  opacity (0.08-0.20) so the dark background shows through — nothing should
  read as an opaque "card" or "panel" the way software dashboards look.
  Text is sparse: prefer NO on-screen title for a beat if the visual and a
  single short phrase can carry the idea alone; when text appears, it is
  white (#FFFFFF) or light grey (#BBBBBB) sans-serif, never more than one
  short sentence at a time, and it fades in only after the visual has
  finished forming (never simultaneously competing for attention). The 3b1b
  palette carries the "explaining math/ideas" layer: soft blue-teal
  (#58C4DD), gold (#F0AC5F), muted green (#83C167), soft red (#FC6255),
  muted purple (#9A72AC), all desaturated enough to sit calmly on black.
  Google's brand colors (#4285F4 blue, #EA4335 red, #FBBC04 yellow, #34A853
  green) are used SUBTLY and ONLY where the content is literally about the
  Google product or a semantic status that maps directly to those exact
  roles (confirmed/success = Google green, blocked/error = Google red) —
  never as a general accent applied broadly. Motion is slow and deliberate:
  favor Transform/ReplacenentTransform morphs over cuts, camera pans/zooms
  over hard scene changes, run_times in the 1.5-3s range for anything the
  viewer needs to read or understand (not the 0.3-0.6s "UI micro-interaction"
  speed of software product demos), and at least one full beat (2-4s) of
  stillness after each idea lands before moving on. Avoid: opaque rounded
  rectangles that look like app UI components, drop shadows, gradients,
  multiple simultaneous competing animations, dense multi-panel dashboards,
  marketing-style bold headline text, more than ~3 colors visible at once.

colors:
  primary:
    - name: "Near Black"
      hex: "#0E0E10"
      role: "dominant background — the theatrical dark canvas everything sits on"
    - name: "White"
      hex: "#FFFFFF"
      role: "primary text, primary line-art strokes, the 'default' object color before it's assigned meaning"
  accent:
    - name: "3b1b Blue"
      hex: "#58C4DD"
      role: "default explanatory accent — the 'this is the concept we're building' color"
    - name: "3b1b Gold"
      hex: "#F0AC5F"
      role: "secondary emphasis, highlighting a specific detail within a blue explanation"
    - name: "Google Blue"
      hex: "#4285F4"
      role: "RESERVED — only when the content IS the Google product/platform itself (e.g. the Agent Platform node, Gemini branding)"
    - name: "Google Green"
      hex: "#34A853"
      role: "RESERVED — confirmed / success / allowed states only"
    - name: "Google Red"
      hex: "#EA4335"
      role: "RESERVED — blocked / error / denied states only"
    - name: "Google Yellow"
      hex: "#FBBC04"
      role: "RESERVED — caution / in-progress states only, use sparingly"
  neutral:
    - name: "Light Grey"
      hex: "#BBBBBB"
      role: "secondary text, captions, de-emphasized labels"
    - name: "Dark Grey"
      hex: "#444444"
      role: "dimmed/background-layer objects (e.g. a de-emphasized network still visible at low opacity)"
    - name: "Mid Grey"
      hex: "#888888"
      role: "borders and strokes on neutral/uncategorized objects"

typography:
  display:
    family: "Roboto"
    weight: "medium"
    style: "sentence case, no all-caps, minimal — often omitted entirely in favor of the visual alone"
  body:
    family: "Roboto"
    weight: "regular"
    style: "sentence case, short phrases only (under ~8 words), never paragraphs"
  caption:
    family: "Roboto"
    weight: "regular"
    style: "small, light grey, used for secondary annotation only"
  rules:
    - "AVOID macOS .ttc font-collection files (Helvetica Neue, Arial, Times) with ManimCE/Pango — they have a confirmed phantom-word-gap bug on compound words (e.g. 'LangChain' renders as 'Lang Chain'). Use single-weight TTF fonts instead (Roboto, or per-weight Google Sans files)."
    - "Before adopting any new font in production, render this exact test string and visually confirm no phantom gaps: 'LangChain Pydantic OpenClaw BigQuery'"
    - "No bold marketing headlines — 3b1b rarely uses large bold display text; let the diagram be the headline"
    - "One short phrase per beat, appears AFTER the visual, never simultaneously"

layout:
  grid: "No visible grid or chrome — pure canvas. Objects positioned by visual/conceptual relationship, not a UI grid"
  alignment: "Centered or camera-frame-relative; avoid corner-anchored UI patterns (top-left title + content area) that read as software chrome"
  aspect_ratio: "16:9"
  notes:
    - "Most of the frame should be empty at any given moment — resist the urge to fill space"
    - "One focal object per beat. If two things must be compared, they should be the ONLY two things on screen"
    - "Titles are optional, not mandatory — many 3b1b beats have zero on-screen text"

motion:
  transitions:
    - "Transform / ReplacementTransform (morph one shape into what it becomes) over FadeOut+FadeIn cuts"
    - "Camera pan/zoom (MovingCameraScene) to reveal new context, rather than a hard scene cut"
    - "Slow LaggedStart with generous lag_ratio (0.3+) instead of near-simultaneous fades"
  animation_style: >
    Slow, deliberate, one-thing-moves-at-a-time. Ease functions are smooth
    (rate_func=smooth), never bouncy or elastic. An object earns its
    on-screen time — let it sit still and be looked at before the next beat.
  pacing: >
    Patient. run_time 1.5-3s for anything meant to be understood, not
    glanced at. wait(2)-wait(4) after key reveals. This is the opposite of
    software-demo pacing (0.2-0.4s micro-transitions) — if it feels "slow"
    compared to a product demo, it's probably closer to correct.
  audio_cues: []

mood:
  keywords:
    - "patient"
    - "contemplative"
    - "rigorous"
    - "theatrical"
    - "calm"
  era: "contemporary (2015-present) math/CS explainer video, ManimGL house style"
  cultural_reference: "3Blue1Brown (Grant Sanderson) — ManimGL default palette and directorial pacing"
  avoid:
    - "opaque rounded-rectangle 'cards' that look like software UI components"
    - "drop shadows, gradients, glossy highlights"
    - "multiple simultaneous competing animations"
    - "dense multi-panel dashboards — many simultaneous labelled boxes on one screen reads as a product UI, not an explainer"
    - "marketing-bold headline text"
    - "more than ~3 colors visible in a single frame"
    - "fast (<0.5s) transitions on anything the viewer needs to read"

assets:
  reference_images: []
  gsep_elements: []
  html_snippets: []
  color_palette_image:
    url: ""

x_manim:
  background_color: "#0E0E10"
  font: "Roboto"
  known_font_bug: >
    Helvetica Neue (and other macOS .ttc collection fonts) cause Pango to
    insert phantom spaces inside compound words in ManimCE. Confirmed on
    "LangChain" -> "Lang Chain", "Pydantic" -> "Pyd antic", "OpenClaw" ->
    "Op enClaw". Always spot-check new fonts against this before adopting.
  stroke_width_range: [2, 3]
  fill_opacity_range: [0.08, 0.20]
  min_run_time_for_readable_text: 1.5
  min_wait_after_key_beat: 2.0
---

## Design Principles

The visual is the headline. Text is a caption, not the message. If an idea
needs a sentence of on-screen text to land, the diagram probably isn't doing
enough work yet — try again with the shape/motion before reaching for words.

Color is meaning, not decoration. In the 3b1b tradition, a color is assigned
to a *concept* once and reused consistently. In our hybrid, Google's exact
brand colors are additionally reserved as a *second, narrower* layer of
meaning: they mark "this is literally the product" or "this is a
governance/status verdict" (confirmed vs. blocked). Everything else —
generic framework nodes, abstract network lines, illustrative shapes — uses
the softer 3b1b palette so the Google colors keep their signal value instead
of blending into general decoration.

Patience is a feature. The single biggest gap between our current renders
and 3b1b's actual pacing is speed: our transitions and waits are tuned like
a software product demo (get to the point fast, cram information density
per second). 3b1b's videos feel unhurried because they trust the viewer to
sit with an idea for 2-4 seconds before moving on. When in doubt, slow down.

## Connectors

### ManimCE (primary use case)

- Set `config.background_color = "#0E0E10"` at module level.
- Default all `Text(...)` calls to `font="Roboto"` (see `known_font_bug`
  above — do not use Helvetica Neue/Arial for production renders).
- Replace `RoundedRectangle(fill_opacity=0.7+)` "card" patterns with either
  (a) no fill at all — just a stroked outline — or (b) `fill_opacity` in the
  0.08-0.20 range so the dark background remains visible through the shape.
- Prefer `Transform`/`ReplacementTransform` chains over `FadeOut` + `FadeIn`
  pairs when one idea becomes the next.
- Default `run_time` for anything with text: 1.5-2.5s. Default `self.wait()`
  after a key reveal: 2-3s. If a scene currently reads "busy," the fix is
  almost always fewer simultaneous animations + longer holds, not more
  content.

## Extraction Notes

Extracted 2026-07-05 from general knowledge of 3Blue1Brown's video visual
grammar (ManimGL default color constants + observed directorial pacing
across the channel's catalog) rather than a single fetchable source — the
3blue1brown.com website itself (fetched this session) is a video index page
and doesn't carry much of the in-video visual system. The Google color
integration and `x_manim` font-bug note are original additions for this
project, informed by the phantom-word-gap bug found in the Security Deep
Dive v4 render (Helvetica Neue on macOS).
