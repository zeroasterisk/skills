// The spec gate decision, shared by every harness adapter. Node builtins only.
//
// decide() reads the repository (tier file, specs) but keeps no state and has
// no side effects: the adapters own session tracking and the host protocol.

import { closeSync, existsSync, openSync, readdirSync, readSync, realpathSync, statSync } from 'node:fs';
import { basename, dirname, isAbsolute, join, relative, resolve, sep } from 'node:path';

export const TIERS = ['trivial', 'small', 'medium', 'large'];
const SPEC_TIERS = new Set(['medium', 'large']);

// Structured file mutators, by harness. Everything else (read-only tools,
// shell tools, MCP tools) is never gated.
export const GATED_TOOLS = new Set([
  // Claude Code
  'edit', 'write', 'multiedit', 'notebookedit',
  // OpenCode / CloudCode
  'patch', 'apply_patch',
  // Antigravity / Jetski
  'write_to_file', 'replace_file_content', 'multi_replace_file_content',
  'write_file', 'edit_file', 'sed_file', 'notebook_edit', 'create_file', 'file_write',
]);

// Paths the agent must be able to write to pass the gate.
const EXEMPT_DIRS = ['.agent', 'specs'];

export const FIX_MESSAGE =
  'Spec gate: before editing, write .agent/tier with one word: trivial, small, medium, or large. ' +
  'For medium or large, also write specs/<name>/spec.md with acceptance criteria that each end in "Verify: <check>".';

// Filesystem timestamps can be coarse or slightly skewed against the local
// clock (network and FUSE filesystems), so allow a small margin.
export const MTIME_SLACK_MS = 2000;

const SPEC_WALK_MAX_DEPTH = 4;
const SPEC_WALK_MAX_ENTRIES = 5000;
const READ_LIMIT_BYTES = 256 * 1024;

export function isDisabled(env = {}) {
  const v = String(env.SPEC_GATE ?? '').trim().toLowerCase();
  return v === 'off' || v === '0' || v === 'false' || v === 'disabled';
}

export function isGatedTool(name) {
  return GATED_TOOLS.has(String(name ?? '').toLowerCase());
}

/** Resolve symlinks for the longest existing prefix of p, keeping the rest as written. */
export function realpathLoose(p) {
  const tail = [];
  let cur = p;
  for (;;) {
    try {
      const real = realpathSync(cur);
      return tail.length ? join(real, ...tail.reverse()) : real;
    } catch {
      const parent = dirname(cur);
      if (parent === cur) return p;
      tail.push(basename(cur));
      cur = parent;
    }
  }
}

/** The nearest ancestor of start (inclusive) holding a .git entry, or null. */
export function findRepoRoot(start) {
  if (!start) return null;
  let dir = realpathLoose(resolve(start));
  for (;;) {
    if (existsSync(join(dir, '.git'))) return dir;
    const parent = dirname(dir);
    if (parent === dir) return null;
    dir = parent;
  }
}

function isInside(root, p) {
  const rel = relative(root, p);
  return rel === '' || (!isAbsolute(rel) && rel.split(sep)[0] !== '..');
}

function isExempt(root, p) {
  const first = relative(root, p).split(sep)[0];
  return EXEMPT_DIRS.includes(first);
}

function readHead(path, limit = READ_LIMIT_BYTES) {
  const fd = openSync(path, 'r');
  try {
    const buf = Buffer.alloc(limit);
    const n = readSync(fd, buf, 0, limit, 0);
    return buf.subarray(0, n).toString('utf8');
  } finally {
    closeSync(fd);
  }
}

/** Parse tier file content: the first word, optionally after "Tier:". */
export function parseTier(text) {
  const m = String(text ?? '').trim().toLowerCase().match(/^(?:tier\s*:\s*)?([a-z]+)/);
  return m && TIERS.includes(m[1]) ? m[1] : null;
}

export function readTier(root) {
  const path = join(root, '.agent', 'tier');
  let st;
  try {
    st = statSync(path);
  } catch {
    return { path, exists: false };
  }
  if (!st.isFile()) return { path, exists: false };
  const raw = readHead(path, 4096);
  return { path, exists: true, mtimeMs: st.mtimeMs, raw: raw.trim(), tier: parseTier(raw) };
}

function hasVerifyLine(path) {
  try {
    return /verify:/i.test(readHead(path));
  } catch {
    return false;
  }
}

function walkSpecs(dir, depth, budget, out) {
  if (depth > SPEC_WALK_MAX_DEPTH) return;
  let entries;
  try {
    entries = readdirSync(dir, { withFileTypes: true });
  } catch {
    return;
  }
  for (const e of entries) {
    if (budget.left-- <= 0) return;
    const p = join(dir, e.name);
    if (e.isFile() && e.name === 'spec.md') out.push(p);
    else if (e.isDirectory() && !e.name.startsWith('.') && e.name !== 'node_modules') {
      walkSpecs(p, depth + 1, budget, out);
    }
  }
}

/** Specs the gate accepts: .agent/spec.md and specs/**\/spec.md (spec-kit layout). */
export function findSpec(root) {
  const candidates = [];
  const agentSpec = join(root, '.agent', 'spec.md');
  if (existsSync(agentSpec)) candidates.push(agentSpec);
  walkSpecs(join(root, 'specs'), 1, { left: SPEC_WALK_MAX_ENTRIES }, candidates);
  const found = candidates.find(hasVerifyLine) ?? null;
  return { found, candidates };
}

const allow = (reason) => ({ allow: true, message: '', reason });
const deny = (reason, detail) => ({ allow: false, message: `${FIX_MESSAGE}\n${detail}`, reason });

/**
 * @param {object} p
 * @param {string} p.cwd            the agent's working directory
 * @param {string} p.toolName       the host's tool name
 * @param {string[]} p.targetPaths  paths the call writes, absolute or relative to cwd
 * @param {number|null} p.sessionStart  epoch ms; a tier file older than this is stale. null skips the check.
 * @param {object} p.env            environment (SPEC_GATE=off disables the gate)
 * @returns {{ allow: boolean, message: string, reason: string }}
 */
export function decide({ cwd, toolName, targetPaths = [], sessionStart = null, env = {} } = {}) {
  if (isDisabled(env)) return allow('disabled');
  if (!isGatedTool(toolName)) return allow('ungated-tool');
  const root = findRepoRoot(cwd);
  if (!root) return allow('no-repo');

  const targets = targetPaths
    .filter((t) => typeof t === 'string' && t.trim())
    .map((t) => realpathLoose(resolve(cwd, t)));
  // A gated tool whose target we cannot see is treated as an edit inside the repo.
  if (targets.length && !targets.some((t) => isInside(root, t) && !isExempt(root, t))) {
    return allow('exempt-or-outside');
  }

  const tierFile = join(root, '.agent', 'tier');
  const tier = readTier(root);
  if (!tier.exists) return deny('no-tier', `No ${tierFile} yet.`);
  if (sessionStart != null && tier.mtimeMs < sessionStart - MTIME_SLACK_MS) {
    return deny('stale-tier', `${tierFile} is from before this session started (${new Date(tier.mtimeMs).toISOString()}). Write it again for this task.`);
  }
  if (!tier.tier) {
    return deny('bad-tier', `${tierFile} says "${tier.raw.slice(0, 40)}"; the first word must be trivial, small, medium, or large.`);
  }
  if (!SPEC_TIERS.has(tier.tier)) return allow(`tier-${tier.tier}`);

  const spec = findSpec(root);
  if (spec.found) return allow(`tier-${tier.tier}-spec`);
  const seen = spec.candidates.length
    ? ` Found ${spec.candidates.map((c) => relative(root, c)).join(', ')}, but none has a "Verify:" line.`
    : '';
  return deny('no-spec', `Tier is ${tier.tier}: write ${join(root, 'specs', '<name>', 'spec.md')} (or ${join(root, '.agent', 'spec.md')}) before editing.${seen}`);
}
