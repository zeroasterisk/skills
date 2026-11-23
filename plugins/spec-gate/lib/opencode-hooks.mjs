// Hooks for the OpenCode / CloudCode plugin. Kept out of the plugin entry
// module because OpenCode calls every function that module exports.

import { decide, isDisabled } from './decide.mjs';
import { extractTargets } from './targets.mjs';

const PARENT_LOOKUP_TIMEOUT_MS = 1000;

function withTimeout(promise, ms) {
  let timer;
  return Promise.race([
    promise,
    new Promise((resolve) => {
      timer = setTimeout(() => resolve(undefined), ms);
    }),
  ]).finally(() => clearTimeout(timer));
}

// A subagent runs in a child session. It inherits the parent's start so the
// tier the parent declared still counts. Both SDK call shapes are tried.
async function parentOf(client, id) {
  const get = client?.session?.get;
  if (typeof get !== 'function') return undefined;
  for (const args of [{ path: { id } }, { sessionID: id }]) {
    try {
      const res = await withTimeout(get.call(client.session, args), PARENT_LOOKUP_TIMEOUT_MS);
      const info = res?.data ?? res;
      if (info && typeof info === 'object' && 'id' in info) return info.parentID ?? undefined;
    } catch {
      // Try the next shape.
    }
  }
  return undefined;
}

export function createSpecGate({ directory, worktree, client, env = process.env, now = () => Date.now() } = {}) {
  const starts = new Map();
  const pending = new Map();

  function sessionStart(id) {
    if (!id) return Promise.resolve(null);
    if (starts.has(id)) return Promise.resolve(starts.get(id));
    if (pending.has(id)) return pending.get(id);
    const seen = now();
    const p = parentOf(client, id).then((parent) => {
      const start = parent && starts.has(parent) ? starts.get(parent) : seen;
      starts.set(id, start);
      pending.delete(id);
      return start;
    });
    pending.set(id, p);
    return p;
  }

  return {
    'chat.message': async (input) => {
      await sessionStart(input?.sessionID);
    },
    'tool.execute.before': async (input, output) => {
      if (isDisabled(env)) return;
      const start = await sessionStart(input?.sessionID);
      let res;
      try {
        res = decide({
          cwd: directory || worktree || process.cwd(),
          toolName: input?.tool,
          targetPaths: extractTargets(output?.args ?? input?.args),
          sessionStart: start,
          env,
        });
      } catch (e) {
        console.error(`spec-gate: internal error, edit allowed: ${e?.message ?? e}`);
        return;
      }
      if (!res.allow) throw new Error(res.message);
    },
  };
}
