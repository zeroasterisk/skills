#!/usr/bin/env node
// Claude Code command hook. Usage: hook.mjs session-start | pre-tool
// Reads the hook JSON on stdin. pre-tool exits 2 with the fix on stderr to block.
// Internal errors exit 1 (Claude Code shows them and lets the call proceed).

import { realpathSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { decide, isDisabled } from '../../lib/decide.mjs';
import { sessionStart } from '../../lib/session-store.mjs';
import { extractTargets } from '../../lib/targets.mjs';

export function run(mode, raw, { env = process.env, now = Date.now() } = {}) {
  if (isDisabled(env)) return { code: 0, stderr: '' };
  const input = raw && raw.trim() ? JSON.parse(raw) : {};
  const start = sessionStart(input.session_id, { now, env });
  if (mode === 'session-start') return { code: 0, stderr: '' };
  const res = decide({
    cwd: input.cwd || process.cwd(),
    toolName: input.tool_name,
    targetPaths: extractTargets(input.tool_input),
    sessionStart: start,
    env,
  });
  return res.allow ? { code: 0, stderr: '' } : { code: 2, stderr: res.message };
}

async function main() {
  const chunks = [];
  for await (const c of process.stdin) chunks.push(c);
  let out;
  try {
    out = run(process.argv[2] || 'pre-tool', Buffer.concat(chunks).toString('utf8'));
  } catch (e) {
    out = { code: 1, stderr: `spec-gate: internal error, edit allowed: ${e?.message ?? e}` };
  }
  if (out.stderr) process.stderr.write(out.stderr + '\n');
  process.exit(out.code);
}

function isMain() {
  try {
    return realpathSync(process.argv[1]) === fileURLToPath(import.meta.url);
  } catch {
    return false;
  }
}

if (isMain()) main();
