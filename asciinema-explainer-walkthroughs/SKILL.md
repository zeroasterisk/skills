---
name: asciinema-explainer-walkthroughs
description: Create production-grade, synchronous terminal recordings (asciinema .cast) and interactive tabbed web walkthroughs for AI agents, developer tools, and CLI journeys. Includes PTY prompt-synchronization, intelligent time-compression, secret redaction, scenario banner structuring, and zoomable Mermaid flowchart companions.
---

# Asciinema Explainer Walkthroughs Skill

A proven engineering methodology and toolkit for creating crisp, high-signal, deterministic terminal recordings (`.cast` files) and interactive web walkthroughs for AI agents, CLI tools, and developer journeys.

---

## 🎯 When to Use This Skill

Use this skill whenever you need to:
1. **Show Real Agent Behavior**: Demonstrate an AI agent (OpenCode, Claude Code, Gemini CLI, Cursor, ADK) solving tasks in real time without screen recording overhead or video compression artifacts.
2. **Create Interactive Product / Spec Demos**: Build lightweight GitHub Pages / internal web demo players (`index.html`) featuring hot-swappable asciinema player tabs, interactive step chapters, and zoomable Mermaid decision flowcharts.
3. **Verify Multi-Turn & Multi-Scenario Journeys**: Create both:
   - **"The Basics (101)"**: Slower, continuous step-by-step walkthrough zooming in on discovery, lookup, install, and usage.
   - **"The Complete Suite"**: Fast, automated multi-scenario test & verification run (e.g. 7/7 passing E2E scenarios).
4. **Eliminate Non-Deterministic Latency**: Compress 10+ minutes of model thinking and container spin-up into punchy 2-3 minute videos while preserving human reading pauses.
5. **Simplify Peer & Lead Human Review**: Provide reviewers with clickable chapter scrubbers, full-text searchable transcripts, and an interactive acceptance rubric with one-click sign-off summaries.

---

## 🛠️ The Architecture: Synchronous PTY Recorder Pattern

Naive terminal recording (`asciinema rec` in a live human session) fails for automated agents because:
- Variable model generation latency creates boring 30-second dead air pauses.
- Typing scripts directly into subshells causes prompt-race collisions.
- Sensitive credentials, OAuth tokens, and API keys are accidentally leaked.

### The 6 Core Pillars of the Recorder Engine:

```
┌────────────────────────────────────────────────────────────────────────┐
│                        Master / Slave PTY                              │
│  - Locked geometry: 112 cols x 34 rows (optimal web player 16:9 ratio) │
│  - Clean environment: custom PS1, no terminal noise, UTF-8 streaming   │
└──────────────────────────────────┬─────────────────────────────────────┘
                                   │
                                   ▼
┌────────────────────────────────────────────────────────────────────────┐
│                  Character-by-Character Typing Sim                     │
│  - Realistic keystroke delays with Gaussian jitter (0.025s - 0.035s)   │
│  - Natural pauses on spaces, punctuation, and path delimiters          │
└──────────────────────────────────┬─────────────────────────────────────┘
                                   │
                                   ▼
┌────────────────────────────────────────────────────────────────────────┐
│               Strict Prompt-Return Synchronization                     │
│  - Uses select.select() to stream stdout and wait for $PS1 prompt      │
│  - 0% command collision guarantee (never sends next turn prematurely)  │
└──────────────────────────────────┬─────────────────────────────────────┘
                                   │
                                   ▼
┌────────────────────────────────────────────────────────────────────────┐
│                  Intelligent Time Compression                          │
│  - Clamps idle gaps > 2.5s down to 2.5s (preserves reading pauses)     │
│  - Collapses 10+ min container/LLM waits into a fast 2 min playback   │
└──────────────────────────────────┬─────────────────────────────────────┘
                                   │
                                   ▼
┌────────────────────────────────────────────────────────────────────────┐
│                  Token & Secret Redaction Pipeline                     │
│  - Intercepts OAuth tokens, PATs, Anthropic/OpenAI keys, and private   │
│    key blocks with standardized [REDACTED_...] placeholders            │
└──────────────────────────────────┬─────────────────────────────────────┘
                                   │
                                   ▼
┌────────────────────────────────────────────────────────────────────────┐
│               Structured Visual Scenarios & Banners                    │
│  - Clean ANSI double-border banner headers for each step/scenario      │
│  - Clear visual demarcation of user actions vs agent execution         │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 📂 Step-by-Step Workflow

### Step 1: Define Scenarios & Banners
Generate width-calibrated double-border ANSI banners using [scripts/banner.py](file:///usr/local/google/home/alanblount/Workspaces/skills/asciinema-explainer-walkthroughs/scripts/banner.py) or [scripts/banner_template.sh](file:///usr/local/google/home/alanblount/Workspaces/skills/asciinema-explainer-walkthroughs/scripts/banner_template.sh):

```bash
# Python CLI generator
python3 scripts/banner.py --step 1 "Capability Search" "Agent queries catalog for matching tools" --color green

# Or Bash wrapper
./scripts/banner_template.sh 1
```

### Step 2: Write the Synchronous PTY Python Script
Use [scripts/pty_recorder_template.py](file:///usr/local/google/home/alanblount/Workspaces/skills/asciinema-explainer-walkthroughs/scripts/pty_recorder_template.py) to script the recording:

```python
from scripts.pty_recorder_template import SynchronousPTYRecorder

rec = SynchronousPTYRecorder(cols=112, rows=34)
rec.start()
try:
    # Step 1: Search & Discover
    rec.execute_and_verify(
        cmd="./scripts/banner.py --step 1 'Discovery' 'Search catalog' && echo 'Found 3 skills'",
        expected_substrings=["Found 3 skills"],
        marker_label="Step 1: Discovery",
        pause_after=2.5,
    )

    # Step 2: Autonomous Execution
    rec.execute_and_verify(
        cmd="./scripts/banner.py --step 2 'Execute' 'Run agent' && python3 run_agent.py",
        expected_substrings=["Success"],
        forbidden_substrings=["Traceback", "FATAL"],
        marker_label="Step 2: Execution",
        pause_after=3.0,
    )
finally:
    rec.stop()
    rec.export(filepath="demo.cast", max_idle=2.5)
```

### Step 3: Build & Validate the Interactive Walkthrough
Use [scripts/build_walkthrough.py](file:///usr/local/google/home/alanblount/Workspaces/skills/asciinema-explainer-walkthroughs/scripts/build_walkthrough.py) to validate the `.cast` file and render the interactive HTML walkthrough:

```bash
# Validate recording and generate standalone index.html
python3 scripts/build_walkthrough.py --cast demo.cast --output index.html

# Start local preview server for human review
python3 scripts/build_walkthrough.py --serve --port 8080
```

### Step 4: Human Review & Sign-Off
Open the interactive player in a browser:
- **Clickable Step Chapters**: Jump directly to specific markers/timestamps.
- **Reviewer Acceptance Rubric**: Verify prompt synchronization, latency clamping, secret masking, and zero errors with interactive checkboxes.
- **Copy Sign-off Summary**: One-click export of markdown review block for PR descriptions and bug trackers.
- **Full Text Transcript**: Search and copy raw terminal output without waiting for video playback.

### Step 5: Automated Test Suite
Run the automated verification suite to validate recorder primitives, time clamping, redactions, and templates:

```bash
python3 -m unittest discover -s tests -v
```

---

## 📚 Advanced Documentation & Research

- [Competitive Analysis & Ecosystem Patterns](file:///usr/local/google/home/alanblount/Workspaces/skills/asciinema-explainer-walkthroughs/docs/competitive_analysis_and_patterns.md): In-depth comparison of Asciinema v2/v3, Charm VHS, Pexpect, `agg`, and high-value patterns.
- [Lessons Learned & Common Pitfalls](file:///usr/local/google/home/alanblount/Workspaces/skills/asciinema-explainer-walkthroughs/docs/lessons_learned_and_pitfalls.md): Guidance on avoiding prompt race conditions, dead air, path leaks, and geometry reflow.
- [Experiment Roadmap & Validation Plan](file:///usr/local/google/home/alanblount/Workspaces/skills/asciinema-explainer-walkthroughs/docs/roadmap_and_experiments.md): Multi-phase plan for typing jitter, markers, automated test harnesses, and GIF export.

---

## 💡 Best Practices & Hard-Earned Lessons

1. **Pre-Authenticate the Basics**: Keep 101 walkthroughs zero-friction. Don't distract beginners with OAuth errors or missing keys in introductory demos.
2. **Never Hardcode Machine Paths**: In skill files and demo scripts, always use relative repository paths (e.g. `./scripts/resolver.py` rather than absolute user home paths).
3. **Always Add a Post-Command Reading Pause**: Set `pause_after=2.5` to `4.0` seconds so human viewers have time to read model output before the next prompt types.
4. **Lock Terminal Geometry**: Always fix rows and columns in `pty.openpty()` (default 112x34). Unset geometry causes text wrapping discrepancies across different viewing screens.
5. **Redact Sensitive Strings Before Export**: Never let raw OAuth client secrets, refresh tokens, bearer keys, or API tokens hit `.cast` files.
6. **Use Native Chapter Markers**: Call `rec.send_turn(..., marker_label="Step 1: Init")` to enable scrubber dots and `[` / `]` keyboard navigation in the player.
7. **Simplify for Human Review**: Always provide clickable chapter jump lists, searchable transcripts, and one-click review sign-off summaries.
