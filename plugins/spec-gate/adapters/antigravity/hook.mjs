#!/usr/bin/env node
// Antigravity / Jetski command hook. Usage: hook.mjs session-start | pre-tool
// Reads the hook JSON on stdin and always exits 0: the host blocks only on
// {"decision":"deny"} printed to stdout, and ignores (fails open on) a hook
// that crashes, times out, or exits non-zero. A PreToolUse result must carry a
// decision: an empty object reads as the deprecated allowTool=false, a deny.

import { realpathSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { decide, isDisabled } from '../../lib/decide.mjs';
import { sessionStart } from '../../lib/session-store.mjs';
import { extractTargets } from '../../lib/targets.mjs';

const ALLOW = { decision: 'allow' };

export function run(mode, raw, { env = process.env, now = Date.now() } = {}) {
  if (isDisabled(env)) return mode === 'session-start' ? {} : ALLOW;
  const input = raw && raw.trim() ? JSON.parse(raw) : {};
  const id = input.conversationId || env.ANTIGRAVITY_CONVERSATION_ID;
  const start = sessionStart(id, { now, env });
  if (mode === 'session-start') return {};
  const cwd = input.cwd || (Array.isArray(input.workspacePaths) && input.workspacePaths[0]);
  if (!cwd) return ALLOW;
  const call = input.toolCall ?? {};
  const res = decide({
    cwd,
    toolName: call.name,
    targetPaths: extractTargets(call.args),
    sessionStart: start,
    env,
  });
  return res.allow ? ALLOW : { decision: 'deny', reason: res.message };
}

async function main() {
  const chunks = [];
  for await (const c of process.stdin) chunks.push(c);
  const mode = process.argv[2] || 'pre-tool';
  let out;
  try {
    out = run(mode, Buffer.concat(chunks).toString('utf8'));
  } catch (e) {
    process.stderr.write(`spec-gate: internal error, edit allowed: ${e?.message ?? e}\n`);
    out = mode === 'session-start' ? {} : ALLOW;
  }
  process.stdout.write(JSON.stringify(out) + '\n');
  process.exit(0);
}

function isMain() {
  try {
    return realpathSync(process.argv[1]) === fileURLToPath(import.meta.url);
  } catch {
    return false;
  }
}

if (isMain()) main();
