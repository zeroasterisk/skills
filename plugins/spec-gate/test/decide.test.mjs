import assert from 'node:assert/strict';
import { mkdirSync, mkdtempSync, rmSync, symlinkSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { test } from 'node:test';
import { decide, FIX_MESSAGE, MTIME_SLACK_MS, parseTier } from '../lib/decide.mjs';
import { DAY_MS, makeRepo } from './helpers.mjs';

const edit = (root, rel = 'src/app.js', extra = {}) => ({
  cwd: root,
  toolName: 'edit',
  targetPaths: [join(root, rel)],
  sessionStart: null,
  env: {},
  ...extra,
});

test('AC1: an edit with no tier file is blocked with the exact fix', (t) => {
  const { root } = makeRepo(t);
  const res = decide(edit(root));
  assert.equal(res.allow, false);
  assert.equal(res.reason, 'no-tier');
  assert.ok(res.message.startsWith(FIX_MESSAGE));
  assert.match(res.message, /write \.agent\/tier with one word: trivial, small, medium, or large/);
  assert.match(res.message, /"Verify: <check>"/);
});

test('AC1: every gated tool name is blocked without a tier', (t) => {
  const { root } = makeRepo(t);
  for (const toolName of ['Edit', 'Write', 'MultiEdit', 'NotebookEdit', 'edit', 'write', 'multiedit', 'patch', 'apply_patch',
    'write_to_file', 'replace_file_content', 'multi_replace_file_content', 'write_file', 'edit_file', 'sed_file', 'notebook_edit']) {
    assert.equal(decide(edit(root, 'a.txt', { toolName })).allow, false, toolName);
  }
});

test('AC2: a fresh trivial or small tier allows edits', (t) => {
  const { root, tier } = makeRepo(t);
  const start = Date.now() - 60_000;
  for (const word of ['trivial', 'small', 'Small', 'Tier: small', 'small (one-line fix)']) {
    tier(word);
    const res = decide(edit(root, 'src/app.js', { sessionStart: start }));
    assert.equal(res.allow, true, word);
  }
});

test('AC3: medium and large are blocked until a spec with a Verify: line exists', (t) => {
  const { root, tier, write } = makeRepo(t);
  for (const word of ['medium', 'large']) {
    tier(word);
    const res = decide(edit(root));
    assert.equal(res.allow, false, word);
    assert.equal(res.reason, 'no-spec');
    assert.match(res.message, new RegExp(`Tier is ${word}`));
  }
  write('specs/001-thing/spec.md', '# Spec\n- It works.\n');
  let res = decide(edit(root));
  assert.equal(res.allow, false, 'spec without Verify: does not count');
  assert.match(res.message, /specs\/001-thing\/spec\.md, but none has a "Verify:" line/);

  write('specs/001-thing/spec.md', '# Spec\n- It works. Verify: npm test\n');
  res = decide(edit(root));
  assert.equal(res.allow, true);
});

test('AC3: .agent/spec.md and nested spec-kit layouts count', (t) => {
  const { root, tier, write } = makeRepo(t);
  tier('large');
  write('.agent/spec.md', 'Goal\n- AC one. Verify: curl localhost\n');
  assert.equal(decide(edit(root)).allow, true);

  const other = makeRepo(t);
  other.tier('medium');
  other.write('specs/area/002-feature/spec.md', '- AC. verify: go test ./...\n');
  assert.equal(decide(edit(other.root)).allow, true);
});

test('AC4: writes under .agent/ and specs/ are never blocked', (t) => {
  const { root } = makeRepo(t);
  assert.equal(decide(edit(root, '.agent/tier', { toolName: 'write' })).allow, true);
  assert.equal(decide(edit(root, '.agent/spec.md', { toolName: 'write' })).allow, true);
  assert.equal(decide(edit(root, 'specs/003-x/spec.md', { toolName: 'write' })).allow, true);
  const rel = decide({ cwd: root, toolName: 'Write', targetPaths: ['.agent/tier'], env: {} });
  assert.equal(rel.allow, true, 'relative path to .agent/tier');
});

test('AC4: a call that also touches a non-exempt file is still gated', (t) => {
  const { root } = makeRepo(t);
  const res = decide({ cwd: root, toolName: 'apply_patch', targetPaths: ['.agent/tier', 'src/a.js'], env: {} });
  assert.equal(res.allow, false);
});

test('AC4: paths outside the repo are never blocked', (t) => {
  const { root, base } = makeRepo(t);
  assert.equal(decide(edit(root, '../scratch.txt')).allow, true);
  assert.equal(decide({ ...edit(root), targetPaths: [join(base, 'elsewhere', 'x.md')] }).allow, true);
  assert.equal(decide({ ...edit(root), targetPaths: [join(tmpdir(), 'spec-gate-outside.txt')] }).allow, true);
});

test('AC4: sessions outside a git repo are never blocked', (t) => {
  const dir = mkdtempSync(join(tmpdir(), 'spec-gate-norepo-'));
  t.after(() => rmSync(dir, { recursive: true, force: true }));
  const res = decide({ cwd: dir, toolName: 'edit', targetPaths: [join(dir, 'a.txt')], env: {} });
  assert.equal(res.allow, true);
  assert.equal(res.reason, 'no-repo');
});

test('AC4: SPEC_GATE=off disables the gate', (t) => {
  const { root } = makeRepo(t);
  for (const v of ['off', 'OFF', '0', 'false']) {
    assert.equal(decide(edit(root, 'a.js', { env: { SPEC_GATE: v } })).allow, true, v);
  }
  assert.equal(decide(edit(root, 'a.js', { env: { SPEC_GATE: 'on' } })).allow, false);
});

test('AC4: read-only and shell tools are never gated', (t) => {
  const { root } = makeRepo(t);
  for (const toolName of ['Read', 'Grep', 'Glob', 'read', 'grep', 'glob', 'list', 'view_file', 'read_file', 'webfetch',
    'Bash', 'bash', 'shell', 'run_command', 'task', 'todowrite', 'write_artifact', undefined]) {
    assert.equal(decide(edit(root, 'src/a.js', { toolName })).allow, true, String(toolName));
  }
});

test('AC5: a tier file from before the session start does not count', (t) => {
  const { root, tier } = makeRepo(t);
  const now = Date.now();
  tier('small', now - DAY_MS);
  const res = decide(edit(root, 'a.js', { sessionStart: now - 1000 }));
  assert.equal(res.allow, false);
  assert.equal(res.reason, 'stale-tier');
  assert.match(res.message, /from before this session started/);

  tier('small', now);
  assert.equal(decide(edit(root, 'a.js', { sessionStart: now - 1000 })).allow, true);
});

test('AC5: freshness tolerates small timestamp skew, and is skipped without a session start', (t) => {
  const { root, tier } = makeRepo(t);
  const start = Date.now();
  tier('small', start - MTIME_SLACK_MS / 2);
  assert.equal(decide(edit(root, 'a.js', { sessionStart: start })).allow, true);
  tier('small', start - DAY_MS);
  assert.equal(decide(edit(root, 'a.js', { sessionStart: null })).allow, true);
});

test('an unreadable tier word is blocked with what was found', (t) => {
  const { root, tier } = makeRepo(t);
  tier('huge');
  const res = decide(edit(root));
  assert.equal(res.allow, false);
  assert.equal(res.reason, 'bad-tier');
  assert.match(res.message, /says "huge"/);
});

test('a gated tool with no visible target is treated as an in-repo edit', (t) => {
  const { root } = makeRepo(t);
  assert.equal(decide({ cwd: root, toolName: 'apply_patch', targetPaths: [], env: {} }).allow, false);
});

test('the tier file lives at the repo root even when cwd is a subdirectory', (t) => {
  const { root, tier } = makeRepo(t);
  const sub = join(root, 'pkg', 'web');
  mkdirSync(sub, { recursive: true });
  assert.equal(decide({ cwd: sub, toolName: 'edit', targetPaths: ['index.js'], env: {} }).allow, false);
  tier('small');
  assert.equal(decide({ cwd: sub, toolName: 'edit', targetPaths: ['index.js'], env: {} }).allow, true);
});

test('a cwd reached through a symlink still sees real targets as inside the repo', (t) => {
  const { root, base } = makeRepo(t);
  const link = join(base, 'link');
  symlinkSync(root, link);
  const res = decide({ cwd: link, toolName: 'edit', targetPaths: [join(root, 'a.js')], env: {} });
  assert.equal(res.allow, false);
  assert.equal(res.reason, 'no-tier');
});

test('parseTier', () => {
  assert.equal(parseTier('medium'), 'medium');
  assert.equal(parseTier('  TIER: Large (migration)\n'), 'large');
  assert.equal(parseTier(''), null);
  assert.equal(parseTier('smallish'), null);
});
