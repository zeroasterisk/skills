# Lessons Learned & Common Pitfalls

A collection of hard-earned engineering insights and edge cases discovered while building and debugging automated terminal walkthroughs for AI coding agents and CLI tools.

---

## ⚠️ Pitfall 1: Blind Delays vs. True Prompt Synchronization

### The Symptom:
Commands are typed into the terminal while the previous tool or agent response is still streaming output, resulting in mangled commands, broken JSON strings, or command-not-found errors.

### The Fix:
Never rely on `time.sleep()` to wait for a command to finish. Implement an active PTY reader using `select.select()` that continuously decodes terminal bytes and verifies that the shell prompt (e.g. `developer@workstation:~$ ` or a unique `export PS1=...`) is anchored at the end of the recent stream before typing the next turn.

---

## ⚠️ Pitfall 2: Excessive Latency & "Dead Air"

### The Symptom:
A 5-turn session takes 12 minutes to record because the agent spends 15–30 seconds reasoning on each turn, creating long stretches of a static terminal screen that bores human reviewers.

### The Fix:
Apply post-recording time clamping:
```python
delta = raw_timestamp - previous_raw_timestamp
clamped_delta = min(delta, max_idle_seconds) # e.g. 2.5s
```
This preserves the natural reading pause immediately following output generation while collapsing long background model or network pauses.

---

## ⚠️ Pitfall 3: Leaking Local Machine Paths into Generic Skills

### The Symptom:
Skill documentation or scripts contain hardcoded user home directories (e.g. `/usr/local/google/home/<user>/...` or `/home/<user>/.config/...`). When another developer or agent executes the workflow in a container or on a different machine, the commands fail with `FileNotFoundError: [Errno 2]`.

### The Fix:
Always use relative paths resolved from the repository root (e.g. `./scripts/resolver.py` or `Path(__file__).resolve().parent`) or standard environment variable expansions (`${XDG_CONFIG_HOME:-$HOME/.config}`).

---

## ⚠️ Pitfall 4: Unlocked Terminal Geometry & Text Reflow

### The Symptom:
A recording created on an ultrawide monitor looks microscopic on a laptop, or formatted ASCII box headers wrap awkwardly with broken corners when rendered in web players.

### The Fix:
Explicitly lock PTY window dimensions at startup using `struct.pack("HHHH", rows, cols, 0, 0)` and `fcntl.ioctl(fd, termios.TIOCSWINSZ, ...)`:
- **Recommended Web Aspect Ratio**: `112 cols x 34 rows` (standard 16:9 responsive display).
- **Environment Parity**: Export `COLUMNS=112` and `LINES=34` in the subshell environment.

---

## ⚠️ Pitfall 5: Interactive OAuth & Secret Masking

### The Symptom:
Automated agent runs encounter interactive authentication workflows (such as browser OAuth URLs, client secrets, or refresh tokens) that either hang waiting for human browser interaction or write sensitive credentials directly into the public `.cast` recording.

### The Fix:
1. **Pre-Authentication in 101 Demos**: Ensure introductory and basic walkthroughs are run in an environment with pre-seeded test credentials or mock zero-auth configurations.
2. **Stream Sanitizer**: Run all output chunks through a regex redaction filter before writing to the `.cast` event stream to replace sensitive tokens with placeholder strings like `[REDACTED_CLIENT_ID]`.

---

## ⚠️ Pitfall 6: State Pollution Across Scenarios

### The Symptom:
Running a multi-scenario recording where Scenario 3 modifies global configuration causes subsequent Scenarios 4 and 5 to fail unexpectedly.

### The Fix:
- In **Multi-Scenario Recordings**: Execute a clean workspace reset hook between independent test cases (e.g. wiping `.config/` state and resetting mock files).
- In **Continuous 101 Walkthroughs**: Explicitly use `--continue` flags and preserve session files to demonstrate realistic, uninterrupted multi-turn context retention.
