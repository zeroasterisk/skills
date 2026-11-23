// Extract the file paths a tool call writes, across the argument shapes of
// Claude Code, OpenCode/CloudCode and Antigravity/Jetski.

import { fileURLToPath } from 'node:url';

const PATH_KEYS = [
  'file_path', 'notebook_path', // Claude Code
  'filePath', 'path', // OpenCode / CloudCode
  'TargetFile', 'targetFile', 'target_file', 'Path', 'AbsolutePath', 'FilePath', 'notebookPath', // Jetski
];
const PATCH_KEYS = ['patchText', 'patch', 'input'];
const PATCH_LINE = /^\*\*\* (?:(?:Add|Update|Delete) File|Move to): (.+)$/;

function clean(v) {
  if (typeof v !== 'string') return null;
  let s = v.trim();
  // Jetski sometimes sends string args JSON-encoded a second time.
  if (s.length > 1 && s.startsWith('"') && s.endsWith('"')) {
    try {
      s = JSON.parse(s);
    } catch {
      s = s.slice(1, -1);
    }
  }
  if (s.startsWith('file://')) {
    try {
      s = fileURLToPath(s);
    } catch {
      return null;
    }
  }
  return s || null;
}

/** Paths named in an apply_patch envelope ("*** Update File: x"). */
export function patchPaths(text) {
  const out = [];
  if (typeof text !== 'string' || !text.includes('*** ')) return out;
  for (const line of text.split(/\r?\n/)) {
    const m = line.trim().match(PATCH_LINE);
    if (m) out.push(m[1].trim());
  }
  return out;
}

export function extractTargets(args) {
  const out = new Set();
  if (!args || typeof args !== 'object') return [];
  const take = (obj) => {
    for (const k of PATH_KEYS) {
      const v = clean(obj?.[k]);
      if (v) out.add(v);
    }
  };
  take(args);
  if (Array.isArray(args.edits)) for (const e of args.edits) if (e && typeof e === 'object') take(e);
  for (const k of PATCH_KEYS) for (const p of patchPaths(args[k])) out.add(p);
  return [...out];
}
