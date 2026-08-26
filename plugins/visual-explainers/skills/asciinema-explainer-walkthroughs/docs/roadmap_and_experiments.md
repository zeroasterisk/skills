# Experiment Roadmap & Validation Plan

A structured roadmap for iteratively experimenting with and advancing the terminal walkthrough toolkit.

---

## 🗺️ Experiment Roadmap

```mermaid
flowchart TD
    E1["<b>Phase 1: Native Chapter Markers</b><br/>Embed v2 'm' events & UI timeline dots<br/><b>[COMPLETE]</b>"] --> E2["<b>Phase 2: Typing Jitter & Human Dynamics</b><br/>Gaussian inter-key delay variance<br/><b>[COMPLETE]</b>"]
    E2 --> E3["<b>Phase 3: Automated Verification Suite</b><br/>Pytest / Unittest suite for cast validation & assertion<br/><b>[COMPLETE]</b>"]
    E3 --> E4["<b>Phase 4: Walkthrough Builder & Reviewer Rubric</b><br/>Chapter sidebar, transcripts, and sign-off rubric<br/><b>[COMPLETE]</b>"]
    E4 --> E5["<b>Phase 5: Multi-Format Pipeline (agg / SVG)</b><br/>Headless GIF/SVG generation for PR summaries"]
```

---

### Phase 1: Native Chapter Markers & Step Scrubbing [COMPLETE]
- **Objective**: Automatically emit Asciicast v2 marker events (`[timestamp, "m", "Step Name"]`) whenever `rec.add_marker(...)` or `rec.send_turn(...)` is called.
- **Player Integration**: Configure `asciinema-player` to read markers and enable `[` / `]` keyboard navigation.
- **Outcome**: Web player displays visible chapter markers on the timeline scrubber and interactive sidebar that jump directly to each step banner.

---

### Phase 2: Natural Typing Dynamics (Gaussian Jitter) [COMPLETE]
- **Objective**: Replace static `char_delay=0.035` with a randomized Gaussian distribution ($30\text{ms} \pm 8\text{ms}$) with slightly longer pauses before spaces and punctuation.
- **Outcome**: Terminal output looks indistinguishable from an experienced software engineer typing at a local workstation.

---

### Phase 3: Automated Skill Verification & Testing Suite [COMPLETE]
- **Objective**: Provide a built-in automated test harness (`tests/test_pty_recorder.py`) testing the recorder engine, time-clamping math, secret redaction, and schema validity.
- **Outcome**: 100% passing unit tests in $< 4$ seconds with zero external dependencies.

---

### Phase 4: Walkthrough Builder & Human Reviewer Rubric [COMPLETE]
- **Objective**: Provide a standalone builder (`scripts/build_walkthrough.py`) and player template (`templates/player_template.html`) with interactive chapter sidebar, full-text transcript search, and an interactive acceptance rubric with one-click sign-off copy.
- **Outcome**: Reviewers can inspect step-by-step progress, read transcripts, check off acceptance criteria, and export sign-off blocks in seconds.

---

### Phase 5: Headless Asset Generation (GIF / Static Previews) [PLANNED]
- **Objective**: Provide an optional rendering step (via `agg` or headless Chromium) to convert `.cast` files into lightweight animated GIFs for embedding directly into Markdown files and PR descriptions.
- **Success Criteria**: Single command `python3 scripts/export_gif.py demo.cast demo.gif` producing an optimized GIF under 5MB.
