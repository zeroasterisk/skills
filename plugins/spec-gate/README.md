# spec-gate

A pre-edit hook. Before its first file edit in a git repo, a coding agent must
declare a task tier. For medium or large work it must also write a spec whose
acceptance criteria end in `Verify: <check>`. Prose in AGENTS.md asks for this;
the gate makes the harness enforce it.

## How an agent passes the gate

1. Write `.agent/tier` at the repo root with one word: `trivial`, `small`,
   `medium`, or `large` (`Tier: small (one-line fix)` also works).
2. For `medium` or `large`, also write `specs/<name>/spec.md` (the spec-kit
   layout) or `.agent/spec.md`, with at least one line containing `Verify:`.

A blocked edit returns this message, plus what is missing:

```
Spec gate: before editing, write .agent/tier with one word: trivial, small, medium, or large. For medium or large, also write specs/<name>/spec.md with acceptance criteria that each end in "Verify: <check>".
```

Add `.agent/` to your global gitignore (`git config --global core.excludesFile`).

## Rules

- Gated: structured edit tools only. Claude Code `Edit|Write|MultiEdit|NotebookEdit`;
  OpenCode/CloudCode `edit`, `write`, `multiedit`, `patch`, `apply_patch`;
  Jetski `write_file`, `edit_file`, `write_to_file`, `replace_file_content`,
  `multi_replace_file_content`, `sed_file`, `notebook_edit`, `create_file`, `file_write`.
- Never gated: read-only tools, shell tools, writes under `.agent/` or `specs/`,
  paths outside the session's git repo, sessions outside a git repo, and any
  process with `SPEC_GATE=off`.
- Fresh per session: the tier file counts only if its mtime is at or after the
  session start (2 s slack for coarse filesystem clocks). A tier file from
  yesterday does not unlock today. Session start is the first time the gate
  sees the session id: in memory for OpenCode/CloudCode (a subagent inherits
  its parent's start), a file under `$TMPDIR/spec-gate-<uid>/` for the command
  hooks (Claude Code `session_id`, Jetski `conversationId`).
- A spec only has to exist with a `Verify:` line; it is not checked for freshness.
- Internal errors never block: they are logged and the edit proceeds.

## Layout

| Path | What |
| --- | --- |
| `lib/decide.mjs` | `decide({ cwd, toolName, targetPaths, sessionStart, env }) -> { allow, message, reason }` |
| `lib/targets.mjs` | Tool arguments to target paths, for all three hosts (including `apply_patch` envelopes) |
| `lib/session-store.mjs` | First-seen session start for the command hooks |
| `lib/opencode-hooks.mjs`, `adapters/opencode/index.mjs` | OpenCode / CloudCode plugin (`tool.execute.before` throws to abort) |
| `hooks/hooks.json`, `adapters/claude-code/hook.mjs` | Claude Code plugin hooks (exit 2 + stderr blocks) |
| `hooks.json`, `adapters/antigravity/hook.mjs` | Antigravity / Jetski plugin hooks (`{"decision":"deny"}` on stdout) |

Node builtins only. Tests: `npm test` or `node --test test/*.test.mjs` (from this directory).

## Install and uninstall

Disable for one process with `SPEC_GATE=off` (for example `SPEC_GATE=off cloudcode`).

**CloudCode / OpenCode.** Add the plugin directory to the `plugin` list in
`~/.config/cloudcode/cloudcode.json` (or `opencode.json`):

```json
{ "plugin": ["/abs/path/to/skills/plugins/spec-gate"] }
```

`cloudcode --pure` starts a session without external plugins. Uninstall:

```sh
python3 -c "import json,os;p=os.path.expanduser('~/.config/cloudcode/cloudcode.json');d=json.load(open(p));d['plugin']=[x for x in d.get('plugin',[]) if not x.rstrip('/').endswith('spec-gate')];json.dump(d,open(p,'w'),indent=2)"
```

**Claude Code.** As a plugin: `claude --plugin-dir /abs/path/to/skills/plugins/spec-gate`,
or `/plugin marketplace add zeroasterisk/skills` then `/plugin install spec-gate@skills`
(uninstall: `/plugin uninstall spec-gate@skills`). Or add the hooks to
`~/.claude/settings.json` directly:

```json
{
  "hooks": {
    "SessionStart": [
      { "hooks": [{ "type": "command", "command": "node \"$HOME/Workspaces/open-source/skills/plugins/spec-gate/adapters/claude-code/hook.mjs\" session-start" }] }
    ],
    "PreToolUse": [
      {
        "matcher": "Edit|Write|MultiEdit|NotebookEdit",
        "hooks": [{ "type": "command", "command": "node \"$HOME/Workspaces/open-source/skills/plugins/spec-gate/adapters/claude-code/hook.mjs\" pre-tool" }]
      }
    ]
  }
}
```

Uninstall: delete those two entries.

**Antigravity / Jetski (advisory).** Link the plugin into the global plugin
directory; Jetski reads the root `hooks.json`:

```sh
ln -s /abs/path/to/skills/plugins/spec-gate ~/.gemini/config/plugins/spec-gate
```

Uninstall: `rm ~/.gemini/config/plugins/spec-gate`. The host does block on a
`deny` decision, but it fails open when a hook crashes, times out, or cannot
start (for example `node` missing from its PATH), so treat it as advisory.

## Limitations

- Shell edits (`sed -i`, `echo >`, `cat <<EOF`) are not gated. ADLC makes the
  same call: a shell command is not a structured edit with a known target.
- The agent picks its own tier. The gate makes the choice explicit and visible;
  it cannot judge whether `small` was honest.
- Only git repos (a `.git` entry) are detected; jj-only or CitC clients are not gated.

Patterns (host contracts, apply_patch target parsing, fail-open handling) follow
the ADLC cross-harness rails guard by Chris Williams
([voodootikigod/adlc](https://github.com/voodootikigod/adlc), MIT). No ADLC code is copied.
