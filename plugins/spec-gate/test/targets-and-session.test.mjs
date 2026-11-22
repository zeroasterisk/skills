import assert from 'node:assert/strict';
import { test } from 'node:test';
import { sessionStart } from '../lib/session-store.mjs';
import { extractTargets, patchPaths } from '../lib/targets.mjs';
import { makeStateDir } from './helpers.mjs';

test('targets: Claude Code argument shapes', () => {
  assert.deepEqual(extractTargets({ file_path: '/r/a.js', old_string: 'x', new_string: 'y' }), ['/r/a.js']);
  assert.deepEqual(extractTargets({ notebook_path: '/r/n.ipynb', new_source: '' }), ['/r/n.ipynb']);
});

test('targets: OpenCode / CloudCode argument shapes', () => {
  assert.deepEqual(extractTargets({ filePath: 'src/a.ts', oldString: 'a', newString: 'b' }), ['src/a.ts']);
  assert.deepEqual(extractTargets({ filePath: 'a.ts', edits: [{ filePath: 'a.ts' }, { filePath: 'b.ts' }] }), ['a.ts', 'b.ts']);
  const patchText = [
    '*** Begin Patch',
    '*** Add File: new.txt',
    '+hi',
    '*** Update File: src/old.js',
    '*** Move to: src/moved.js',
    '@@',
    '-a',
    '+b',
    '*** Delete File: gone.md',
    '*** End Patch',
  ].join('\n');
  assert.deepEqual(extractTargets({ patchText }), ['new.txt', 'src/old.js', 'src/moved.js', 'gone.md']);
});

test('targets: Antigravity / Jetski argument shapes', () => {
  assert.deepEqual(extractTargets({ TargetFile: '/w/a.go', CodeContent: 'x' }), ['/w/a.go']);
  assert.deepEqual(extractTargets({ Path: '"/w/double-encoded.md"', Replacement: 'x' }), ['/w/double-encoded.md']);
  assert.deepEqual(extractTargets({ Path: 'file:///w/uri.txt' }), ['/w/uri.txt']);
  assert.deepEqual(extractTargets({ notebookPath: '/w/n.ipynb' }), ['/w/n.ipynb']);
});

test('targets: junk input yields nothing', () => {
  assert.deepEqual(extractTargets(null), []);
  assert.deepEqual(extractTargets('x'), []);
  assert.deepEqual(extractTargets({ command: 'echo hi > a.txt' }), []);
  assert.deepEqual(patchPaths('no envelope here'), []);
});

test('session store: first seen wins, per session id', (t) => {
  const env = { SPEC_GATE_STATE_DIR: makeStateDir(t) };
  assert.equal(sessionStart('abc', { now: 1000, env }), 1000);
  assert.equal(sessionStart('abc', { now: 5000, env }), 1000);
  assert.equal(sessionStart('other', { now: 7000, env }), 7000);
  assert.equal(sessionStart('../../etc/passwd', { now: 9000, env }), 9000);
  assert.equal(sessionStart('../../etc/passwd', { now: 9999, env }), 9000);
});

test('session store: no id means no session start', (t) => {
  const env = { SPEC_GATE_STATE_DIR: makeStateDir(t) };
  assert.equal(sessionStart(undefined, { env }), null);
  assert.equal(sessionStart('', { env }), null);
});
