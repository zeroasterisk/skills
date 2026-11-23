import { mkdirSync, mkdtempSync, rmSync, utimesSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { dirname, join } from 'node:path';

export const DAY_MS = 24 * 60 * 60 * 1000;

/** A throwaway directory with a .git entry; returns helpers bound to it. */
export function makeRepo(t) {
  const base = mkdtempSync(join(tmpdir(), 'spec-gate-test-'));
  const root = join(base, 'repo');
  mkdirSync(join(root, '.git'), { recursive: true });
  t?.after?.(() => rmSync(base, { recursive: true, force: true }));
  const write = (rel, content = '', mtimeMs) => {
    const p = join(root, rel);
    mkdirSync(dirname(p), { recursive: true });
    writeFileSync(p, content);
    if (mtimeMs != null) utimesSync(p, mtimeMs / 1000, mtimeMs / 1000);
    return p;
  };
  return { base, root, write, tier: (word, mtimeMs) => write('.agent/tier', `${word}\n`, mtimeMs) };
}

export function makeStateDir(t) {
  const dir = mkdtempSync(join(tmpdir(), 'spec-gate-state-'));
  t?.after?.(() => rmSync(dir, { recursive: true, force: true }));
  return dir;
}
