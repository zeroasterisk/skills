import assert from 'node:assert/strict';
import { spawnSync } from 'node:child_process';
import { existsSync, readFileSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { test } from 'node:test';
import { fileURLToPath } from 'node:url';
import * as entry from '../adapters/opencode/index.mjs';
import { FIX_MESSAGE, GATED_TOOLS } from '../lib/decide.mjs';
import { createSpecGate } from '../lib/opencode-hooks.mjs';
import { DAY_MS, makeRepo, makeStateDir } from './helpers.mjs';

const PLUGIN = join(dirname(fileURLToPath(import.meta.url)), '..');
const CLAUDE_HOOK = join(PLUGIN, 'adapters', 'claude-code', 'hook.mjs');
const AG_HOOK = join(PLUGIN, 'adapters', 'antigravity', 'hook.mjs');

function runHook(script, mode, input, env = {}) {
  const raw = typeof input === 'string' ? input : JSON.stringify(input);
  const r = spawnSync(process.execPath, [script, mode], {
    input: raw,
    encoding: 'utf8',
    env: { ...process.env, SPEC_GATE: '', ...env },
  });
  return { code: r.status, stdout: r.stdout, stderr: r.stderr };
}

// --- Claude Code -----------------------------------------------------------

test('claude-code: hooks.json wires PreToolUse on the edit tools and SessionStart', () => {
  const cfg = JSON.parse(readFileSync(join(PLUGIN, 'hooks', 'hooks.json'), 'utf8'));
  const pre = cfg.hooks.PreToolUse[0];
  assert.equal(pre.matcher, 'Edit|Write|MultiEdit|NotebookEdit');
  assert.match(pre.hooks[0].command, /\$\{CLAUDE_PLUGIN_ROOT\}\/adapters\/claude-code\/hook\.mjs" pre-tool$/);
  assert.match(cfg.hooks.SessionStart[0].hooks[0].command, /hook\.mjs" session-start$/);
  for (const name of pre.matcher.split('|')) assert.ok(GATED_TOOLS.has(name.toLowerCase()), name);
});

test('claude-code: blocks with exit 2 and the fix on stderr, then allows after .agent/tier', (t) => {
  const { root, write } = makeRepo(t);
  const env = { SPEC_GATE_STATE_DIR: makeStateDir(t) };
  const call = { session_id: 's1', cwd: root, hook_event_name: 'PreToolUse', tool_name: 'Write', tool_input: { file_path: join(root, 'hello.txt'), content: 'hi' } };
  assert.equal(runHook(CLAUDE_HOOK, 'session-start', { session_id: 's1', cwd: root, source: 'startup' }, env).code, 0);

  let r = runHook(CLAUDE_HOOK, 'pre-tool', call, env);
  assert.equal(r.code, 2);
  assert.ok(r.stderr.includes(FIX_MESSAGE));

  const tierCall = { ...call, tool_input: { file_path: join(root, '.agent', 'tier'), content: 'small' } };
  assert.equal(runHook(CLAUDE_HOOK, 'pre-tool', tierCall, env).code, 0);
  write('.agent/tier', 'small\n');

  r = runHook(CLAUDE_HOOK, 'pre-tool', call, env);
  assert.equal(r.code, 0, r.stderr);
  assert.equal(r.stderr, '');
});

test('claude-code: a tier file older than the session start is stale', (t) => {
  const { root, tier } = makeRepo(t);
  const env = { SPEC_GATE_STATE_DIR: makeStateDir(t) };
  tier('small', Date.now() - DAY_MS);
  runHook(CLAUDE_HOOK, 'session-start', { session_id: 'today', cwd: root }, env);
  const r = runHook(CLAUDE_HOOK, 'pre-tool', { session_id: 'today', cwd: root, tool_name: 'Edit', tool_input: { file_path: join(root, 'a.js') } }, env);
  assert.equal(r.code, 2);
  assert.match(r.stderr, /from before this session started/);
});

test('claude-code: SPEC_GATE=off allows, and internal errors do not block', (t) => {
  const { root } = makeRepo(t);
  const call = { session_id: 's', cwd: root, tool_name: 'Edit', tool_input: { file_path: join(root, 'a.js') } };
  assert.equal(runHook(CLAUDE_HOOK, 'pre-tool', call, { SPEC_GATE: 'off', SPEC_GATE_STATE_DIR: makeStateDir(t) }).code, 0);
  const bad = runHook(CLAUDE_HOOK, 'pre-tool', '{not json', { SPEC_GATE_STATE_DIR: makeStateDir(t) });
  assert.equal(bad.code, 1);
  assert.match(bad.stderr, /internal error, edit allowed/);
});

// --- Antigravity / Jetski --------------------------------------------------

test('antigravity: hooks.json matcher only names gated tools', () => {
  const cfg = JSON.parse(readFileSync(join(PLUGIN, 'hooks.json'), 'utf8'))['spec-gate'];
  const pre = cfg.PreToolUse[0];
  for (const name of pre.matcher.split('|')) assert.ok(GATED_TOOLS.has(name), name);
  assert.match(pre.hooks[0].command, /^node \.\/adapters\/antigravity\/hook\.mjs pre-tool$/);
  assert.ok(existsSync(join(PLUGIN, 'adapters', 'antigravity', 'hook.mjs')));
  assert.match(cfg.SessionStart[0].command, /session-start$/);
});

test('antigravity: denies on stdout with exit 0, then allows after .agent/tier', (t) => {
  const { root, write } = makeRepo(t);
  const env = { SPEC_GATE_STATE_DIR: makeStateDir(t) };
  const call = { conversationId: 'c1', cwd: root, workspacePaths: [root], toolCall: { id: 't1', name: 'write_file', args: { Path: join(root, 'x.md') } } };
  let r = runHook(AG_HOOK, 'pre-tool', call, env);
  assert.equal(r.code, 0);
  const out = JSON.parse(r.stdout);
  assert.equal(out.decision, 'deny');
  assert.ok(out.reason.includes(FIX_MESSAGE));

  const tierCall = { ...call, toolCall: { name: 'write_file', args: { Path: join(root, '.agent', 'tier') } } };
  assert.deepEqual(JSON.parse(runHook(AG_HOOK, 'pre-tool', tierCall, env).stdout), { decision: 'allow' });

  write('.agent/tier', 'trivial\n');
  r = runHook(AG_HOOK, 'pre-tool', call, env);
  assert.equal(r.code, 0);
  assert.deepEqual(JSON.parse(r.stdout), { decision: 'allow' });
});

// Jetski reads an empty PreToolUse result as allowTool=false, a deny, so every
// pass-through must say "allow" explicitly.
test('antigravity: bad input, SPEC_GATE=off and ungated tools emit an explicit allow', (t) => {
  const { root } = makeRepo(t);
  const env = { SPEC_GATE_STATE_DIR: makeStateDir(t) };
  const ALLOW = { decision: 'allow' };
  let r = runHook(AG_HOOK, 'pre-tool', 'garbage', env);
  assert.equal(r.code, 0);
  assert.deepEqual(JSON.parse(r.stdout), ALLOW);
  const call = { conversationId: 'c', cwd: root, toolCall: { name: 'edit_file', args: { Path: join(root, 'a') } } };
  r = runHook(AG_HOOK, 'pre-tool', call, { ...env, SPEC_GATE: 'off' });
  assert.deepEqual(JSON.parse(r.stdout), ALLOW);
  r = runHook(AG_HOOK, 'pre-tool', { ...call, toolCall: { name: 'run_command', args: { CommandLine: 'echo > a' } } }, env);
  assert.deepEqual(JSON.parse(r.stdout), ALLOW);
  r = runHook(AG_HOOK, 'pre-tool', { toolCall: { name: 'edit_file', args: {} } }, env);
  assert.deepEqual(JSON.parse(r.stdout), ALLOW, 'no cwd');
  r = runHook(AG_HOOK, 'session-start', { conversationId: 'c' }, env);
  assert.deepEqual(JSON.parse(r.stdout), {});
});

// --- OpenCode / CloudCode ----------------------------------------------------

test('opencode: the entry module exports only the plugin function', () => {
  const fns = new Set(Object.values(entry));
  assert.equal(fns.size, 1);
  assert.equal(entry.default, entry.SpecGatePlugin);
});

test('opencode: tool.execute.before throws the fix, then allows after .agent/tier', async (t) => {
  const { root, write } = makeRepo(t);
  const hooks = await entry.default({ directory: root, worktree: root });
  const before = hooks['tool.execute.before'];
  await hooks['chat.message']({ sessionID: 'ses_1' });

  await assert.rejects(
    before({ tool: 'edit', sessionID: 'ses_1', callID: 'c1' }, { args: { filePath: join(root, 'src/a.ts') } }),
    (e) => e instanceof Error && e.message.startsWith(FIX_MESSAGE),
  );
  await before({ tool: 'write', sessionID: 'ses_1', callID: 'c2' }, { args: { filePath: join(root, '.agent/tier') } });
  await before({ tool: 'bash', sessionID: 'ses_1', callID: 'c3' }, { args: { command: 'echo hi > a.txt' } });
  await before({ tool: 'read', sessionID: 'ses_1', callID: 'c4' }, { args: { filePath: join(root, 'src/a.ts') } });

  write('.agent/tier', 'small\n');
  await before({ tool: 'edit', sessionID: 'ses_1', callID: 'c5' }, { args: { filePath: join(root, 'src/a.ts') } });
  await before({ tool: 'apply_patch', sessionID: 'ses_1', callID: 'c6' }, { args: { patchText: '*** Begin Patch\n*** Add File: b.ts\n+x\n*** End Patch' } });
});

test('opencode: a new session ignores a tier file left over from before it started', async (t) => {
  const { root, tier } = makeRepo(t);
  tier('small', Date.now() - DAY_MS);
  const hooks = createSpecGate({ directory: root, env: {} });
  await hooks['chat.message']({ sessionID: 'ses_new' });
  await assert.rejects(
    hooks['tool.execute.before']({ tool: 'edit', sessionID: 'ses_new' }, { args: { filePath: join(root, 'a.js') } }),
    /from before this session started/,
  );
});

test('opencode: a subagent session inherits its parent session start', async (t) => {
  const { root, tier } = makeRepo(t);
  let clock = 1_000_000;
  const client = {
    session: {
      async get({ path }) {
        return { data: { id: path.id, parentID: path.id === 'ses_child' ? 'ses_parent' : undefined } };
      },
    },
  };
  const hooks = createSpecGate({ directory: root, client, env: {}, now: () => clock });
  const parentStart = Date.now() - 60_000;
  clock = parentStart;
  await hooks['chat.message']({ sessionID: 'ses_parent' });
  tier('small', parentStart + 1000);
  clock = Date.now() + 60_000; // the child starts after the tier file was written
  await hooks['tool.execute.before']({ tool: 'edit', sessionID: 'ses_child' }, { args: { filePath: join(root, 'a.js') } });

  await assert.rejects(
    hooks['tool.execute.before']({ tool: 'edit', sessionID: 'ses_orphan' }, { args: { filePath: join(root, 'a.js') } }),
    /from before this session started/,
  );
});

test('opencode: SPEC_GATE=off and a broken client never block', async (t) => {
  const { root } = makeRepo(t);
  const off = createSpecGate({ directory: root, env: { SPEC_GATE: 'off' } });
  await off['tool.execute.before']({ tool: 'edit', sessionID: 's' }, { args: { filePath: join(root, 'a.js') } });

  const broken = { session: { get: () => new Promise(() => {}) } };
  const hooks = createSpecGate({ directory: root, client: broken, env: {} });
  await assert.rejects(
    hooks['tool.execute.before']({ tool: 'edit', sessionID: 's' }, { args: { filePath: join(root, 'a.js') } }),
    /Spec gate/,
  );
});
