---
name: asciinema-explainer-walkthroughs
description: Create production-grade, synchronous terminal recordings (asciinema .cast) and interactive tabbed web walkthroughs for AI agents, developer tools, and CLI journeys. Includes PTY prompt-synchronization, intelligent time-compression, secret redaction, scenario banner structuring, and zoomable Mermaid flowchart companions.
---

# Asciinema Explainer Walkthroughs Skill

A proven engineering methodology and toolkit for creating crisp, high-signal, deterministic terminal recordings (`.cast` files) and interactive web walkthroughs for AI agents, CLI tools, and developer journeys.

---

## 🎯 When to Use This Skill

Use this skill whenever you need to:
1. **Show Real Agent Behavior**: Demonstrate an AI agent (OpenCode, Claude Code, Gemini CLI, Cursor) solving tasks in real time without screen recording overhead.
2. **Create Interactive Product / Spec Demos**: Build lightweight GitHub Pages demo players (`index.html`) featuring asciinema player tabs and zoomable Mermaid decision flowcharts.
3. **Verify Multi-Turn & Multi-Scenario Journeys**: Create both:
   - **"The Basics (101)"**: Slower, continuous step-by-step walkthrough zooming in on discovery, lookup, install, and usage.
   - **"The Complete Suite"**: Fast, automated multi-scenario test & verification run (e.g. 7/7 passing E2E scenarios).
4. **Eliminate Non-Deterministic Latency**: Compress 10+ minutes of model thinking and container spin-up into punchy 2-3 minute videos while preserving human reading pauses.

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
│  - Realistic keystroke delays (0.025s - 0.035s per char)               │
│  - Types prompts as a real human developer would in their workstation  │
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
│  - Intercepts OAuth browser callbacks and replaces codes with          │
│    [REDACTED_CLIENT_ID] and [REDACTED_OAUTH_CODE]                      │
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
Create a `scripts/banner.sh` helper to output structured ANSI color box headers:
```bash
./scripts/banner.sh 1  # STEP 1: Capability Search
./scripts/banner.sh 2  # STEP 2: Catalog Lookup
```

### Step 2: Write the Synchronous PTY Python Script
Use the provided `scripts/pty_recorder_template.py`:
- Configure target cols (112) and rows (34).
- Define turns using `rec.send_turn(cmd, pause_after=3.0, char_delay=0.03)`.
- Use `--continue` to preserve multi-turn agent conversation history.

### Step 3: Run & Compress Recording
```bash
python3 scripts/record_session.py
# Produces demo.cast (compressed, synchronized, redacted)
```

### Step 4: Verify Content & Zero Errors
Always programmatically verify the `.cast` output stream:
```python
import json
with open('demo.cast') as f:
    text = ''.join(json.loads(l)[2] for l in f.readlines()[1:])
assert 'Traceback' not in text
assert 'No such file or directory' not in text
for step in ['STEP 1', 'STEP 2', 'STEP 3']:
    assert step in text
```

### Step 5: Embed in 2-Tab Interactive Web Player (`index.html`)
- **Tab 1: "The Basics (101)"**: Focus on the 5 foundational steps (Agent $\rightarrow$ Search $\rightarrow$ Lookup $\rightarrow$ Install $\rightarrow$ Execute).
- **Tab 2: "The Complete Suite"**: Multi-scenario progressive disclosure, opt-out handling, and E2E verification.
- **Companion Artifact**: High-contrast, zoomable Mermaid.js decision flowchart.

### Step 6: Automated Skill Verification
Run the built-in unit and integration test suite to verify PTY geometry, prompt synchronization, redaction, and `.cast` schema validity:
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
4. **Lock Terminal Geometry**: Always fix rows and columns in `pty.openpty()` (112x34). Unset geometry causes text wrapping discrepancies across different viewing screens.
5. **Redact Sensitive Strings Before Export**: Never let raw OAuth client secrets, refresh tokens, or bearer keys hit `.cast` files.
6. **Use Native Chapter Markers**: Call `rec.send_turn(..., marker_label="Step 1: Init")` to enable scrubber dots and `[` / `]` keyboard navigation in the player.
