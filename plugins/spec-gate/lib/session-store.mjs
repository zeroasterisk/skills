// First-seen session start times for the command-hook adapters (Claude Code,
// Antigravity), which run as a fresh process per call. One small file per
// session id under the temp dir; the first writer wins.

import { mkdirSync, readFileSync, readdirSync, statSync, unlinkSync, writeFileSync } from 'node:fs';
import { tmpdir, userInfo } from 'node:os';
import { join } from 'node:path';

const PRUNE_AFTER_MS = 7 * 24 * 60 * 60 * 1000;

function uid() {
  try {
    return String(userInfo().uid);
  } catch {
    return 'user';
  }
}

export function stateDir(env = process.env) {
  return env.SPEC_GATE_STATE_DIR || join(tmpdir(), `spec-gate-${uid()}`);
}

function sanitize(id) {
  return String(id).replace(/[^A-Za-z0-9_.-]/g, '_').slice(0, 128);
}

function prune(dir, now) {
  try {
    for (const name of readdirSync(dir)) {
      const p = join(dir, name);
      if (now - statSync(p).mtimeMs > PRUNE_AFTER_MS) unlinkSync(p);
    }
  } catch {
    // Pruning is housekeeping; never let it affect the decision.
  }
}

/**
 * Return the recorded start of a session, recording `now` if this is the
 * first time the id is seen. Returns null without an id.
 */
export function sessionStart(id, { now = Date.now(), env = process.env } = {}) {
  if (typeof id !== 'string' || !id.trim()) return null;
  const dir = stateDir(env);
  const file = join(dir, sanitize(id));
  try {
    const v = Number(readFileSync(file, 'utf8'));
    if (Number.isFinite(v) && v > 0) return v;
  } catch {
    // Not seen yet.
  }
  mkdirSync(dir, { recursive: true, mode: 0o700 });
  try {
    writeFileSync(file, String(now), { flag: 'wx', mode: 0o600 });
    prune(dir, now);
    return now;
  } catch (e) {
    if (e?.code !== 'EEXIST') throw e;
    const v = Number(readFileSync(file, 'utf8'));
    return Number.isFinite(v) && v > 0 ? v : now;
  }
}
