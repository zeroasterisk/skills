#!/usr/bin/env node
// Copyright 2026 Google LLC
//
// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
//
//     http://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.

import { execFileSync } from 'node:child_process';
import fs from 'node:fs';
import path from 'node:path';

const SKIP_DIRS = new Set([
  '.git',
  'node_modules',
  'dist',
  'build',
  'out',
  '.next',
  '.astro',
  '.venv',
  'venv',
  '__pycache__',
  '.mypy_cache',
  '.ruff_cache',
  '.pytest_cache',
  '.beads',
  '.dolt',
  '.serena',
  '.vendor',
  'DerivedData',
  '.build',
  'target',
  'coverage',
]);

function parseArgs(argv) {
  const opts = {
    targets: [],
    json: false,
    outdated: false,
    maxDepth: 5,
    help: false,
  };
  for (let i = 0; i < argv.length; i++) {
    const arg = argv[i];
    if (arg === '--json') {
      opts.json = true;
    } else if (arg === '--outdated') {
      opts.outdated = true;
    } else if (arg === '--help' || arg === '-h') {
      opts.help = true;
    } else if (arg === '--max-depth' && argv[i + 1]) {
      const n = Number.parseInt(argv[++i], 10);
      if (Number.isFinite(n) && n >= 0) opts.maxDepth = n;
    } else if (!arg.startsWith('-')) {
      opts.targets.push(path.resolve(arg));
    }
  }
  if (opts.targets.length === 0) {
    opts.targets.push(process.cwd());
  }
  return opts;
}

function runCmd(cmd, args, cwd, envExtra = {}, timeoutMs = 45000) {
  try {
    const stdout = execFileSync(cmd, args, {
      cwd,
      encoding: 'utf8',
      stdio: ['ignore', 'pipe', 'pipe'],
      timeout: timeoutMs,
      env: { ...process.env, ...envExtra },
      maxBuffer: 16 * 1024 * 1024,
    });
    return { ok: true, stdout, stderr: '', status: 0 };
  } catch (err) {
    return {
      ok: false,
      stdout: typeof err.stdout === 'string' ? err.stdout : '',
      stderr: typeof err.stderr === 'string' ? err.stderr : String(err.message),
      status: typeof err.status === 'number' ? err.status : 1,
    };
  }
}

function parseSemver(raw) {
  if (!raw || typeof raw !== 'string') return null;
  const cleaned = raw.trim().replace(/^v/, '');
  const m = cleaned.match(/^(\d+)\.(\d+)(?:\.(\d+))?/);
  if (!m) return null;
  return {
    major: Number.parseInt(m[1], 10),
    minor: Number.parseInt(m[2], 10),
    patch: m[3] !== undefined ? Number.parseInt(m[3], 10) : 0,
  };
}

function classifyBump(currentRaw, latestRaw) {
  const cur = parseSemver(currentRaw);
  const lat = parseSemver(latestRaw);
  if (!cur || !lat) return 'unknown';
  if (lat.major > cur.major) return 'major';
  if (lat.minor > cur.minor) return 'minor';
  if (lat.patch > cur.patch) return 'patch';
  return 'same';
}

function inspectGit(repoDir) {
  const inside = runCmd('git', ['rev-parse', '--is-inside-work-tree'], repoDir);
  if (!inside.ok || inside.stdout.trim() !== 'true') {
    return { isGitRepo: false };
  }
  const branchRes = runCmd(
    'git',
    ['rev-parse', '--abbrev-ref', 'HEAD'],
    repoDir,
  );
  const statusRes = runCmd('git', ['status', '--porcelain'], repoDir);
  const dirtyFiles = statusRes.ok
    ? statusRes.stdout
        .split('\n')
        .map((l) => l.trimEnd())
        .filter(Boolean)
    : [];

  let ahead = 0;
  let behind = 0;
  let upstream = null;
  const upRes = runCmd(
    'git',
    ['rev-parse', '--abbrev-ref', '--symbolic-full-name', '@{u}'],
    repoDir,
  );
  if (upRes.ok && upRes.stdout.trim()) {
    upstream = upRes.stdout.trim();
    const lr = runCmd(
      'git',
      ['rev-list', '--left-right', '--count', `${upstream}...HEAD`],
      repoDir,
    );
    if (lr.ok) {
      const [b, a] = lr.stdout.trim().split(/\s+/).map(Number);
      behind = Number.isFinite(b) ? b : 0;
      ahead = Number.isFinite(a) ? a : 0;
    }
  }

  return {
    isGitRepo: true,
    branch: branchRes.ok ? branchRes.stdout.trim() : 'unknown',
    upstream,
    ahead,
    behind,
    dirtyCount: dirtyFiles.length,
    dirtyFiles: dirtyFiles.slice(0, 20),
  };
}

function walkRepo(rootDir, maxDepth) {
  const found = {
    goMods: [],
    goWork: [],
    goFiles: 0,
    packageJsons: [],
    pyProjects: [],
    requirements: [],
    pyFiles: 0,
    swiftPackages: [],
    xcodeProjects: [],
    swiftFiles: 0,
    cargoTomls: [],
    dockerfiles: [],
    workflows: [],
    mcpConfigs: [],
    hasBeads: fs.existsSync(path.join(rootDir, '.beads')),
    hasChangelog: fs.existsSync(path.join(rootDir, 'CHANGELOG.md')),
    hasReadme: fs.existsSync(path.join(rootDir, 'README.md')),
    hasMakefile: fs.existsSync(path.join(rootDir, 'Makefile')),
  };

  function visit(dir, depth) {
    if (depth > maxDepth) return;
    let entries;
    try {
      entries = fs.readdirSync(dir, { withFileTypes: true });
    } catch {
      return;
    }
    for (const entry of entries) {
      const fullPath = path.join(dir, entry.name);
      const relPath = path.relative(rootDir, fullPath) || '.';

      if (entry.isDirectory()) {
        if (entry.name.endsWith('.xcodeproj') || entry.name.endsWith('.xcworkspace')) {
          found.xcodeProjects.push(relPath);
          continue;
        }
        if (entry.name === '.github') {
          const wfDir = path.join(fullPath, 'workflows');
          if (fs.existsSync(wfDir)) {
            try {
              for (const wf of fs.readdirSync(wfDir)) {
                if (wf.endsWith('.yml') || wf.endsWith('.yaml')) {
                  found.workflows.push(path.join(relPath, 'workflows', wf));
                }
              }
            } catch {
              // ignore unreadable workflow dir
            }
          }
          continue;
        }
        if (SKIP_DIRS.has(entry.name) || entry.name.startsWith('.')) {
          continue;
        }
        visit(fullPath, depth + 1);
        continue;
      }

      if (!entry.isFile()) continue;

      if (entry.name === 'go.mod') found.goMods.push(relPath);
      else if (entry.name === 'go.work') found.goWork.push(relPath);
      else if (entry.name.endsWith('.go')) found.goFiles++;
      else if (entry.name === 'package.json') found.packageJsons.push(relPath);
      else if (entry.name === 'pyproject.toml') found.pyProjects.push(relPath);
      else if (/^requirements.*\.txt$/i.test(entry.name)) {
        found.requirements.push(relPath);
      } else if (entry.name.endsWith('.py')) found.pyFiles++;
      else if (entry.name === 'Package.swift') found.swiftPackages.push(relPath);
      else if (entry.name.endsWith('.swift')) found.swiftFiles++;
      else if (entry.name === 'Cargo.toml') found.cargoTomls.push(relPath);
      else if (/^Dockerfile(\..+)?$/.test(entry.name)) {
        found.dockerfiles.push(relPath);
      } else if (
        entry.name === 'mcp.json' ||
        entry.name === '.mcp.json' ||
        entry.name === 'mcp-config.json'
      ) {
        found.mcpConfigs.push(relPath);
      }
    }
  }

  visit(rootDir, 0);
  return found;
}

function parseGoMod(repoDir, relPath) {
  const full = path.join(repoDir, relPath);
  const text = fs.readFileSync(full, 'utf8');
  const modMatch = text.match(/^\s*module\s+(\S+)/m);
  const goMatch = text.match(/^\s*go\s+(\S+)/m);
  const tcMatch = text.match(/^\s*toolchain\s+(\S+)/m);
  return {
    path: relPath,
    dir: path.dirname(relPath),
    module: modMatch ? modMatch[1] : null,
    goVersion: goMatch ? goMatch[1] : null,
    toolchain: tcMatch ? tcMatch[1] : null,
  };
}

function parsePackageJson(repoDir, relPath) {
  const full = path.join(repoDir, relPath);
  const dir = path.dirname(full);
  let pkg = {};
  try {
    pkg = JSON.parse(fs.readFileSync(full, 'utf8'));
  } catch {
    return { path: relPath, parseError: true };
  }
  let lockfile = null;
  if (fs.existsSync(path.join(dir, 'package-lock.json'))) lockfile = 'npm';
  else if (fs.existsSync(path.join(dir, 'pnpm-lock.yaml'))) lockfile = 'pnpm';
  else if (fs.existsSync(path.join(dir, 'yarn.lock'))) lockfile = 'yarn';

  return {
    path: relPath,
    dir: path.dirname(relPath),
    name: pkg.name ?? null,
    version: pkg.version ?? null,
    private: Boolean(pkg.private),
    enginesNode: pkg.engines?.node ?? null,
    lockfile,
    hasWorkspaces: Boolean(pkg.workspaces),
    hasNodeModules: fs.existsSync(path.join(dir, 'node_modules')),
  };
}

function parsePyProject(repoDir, relPath) {
  const full = path.join(repoDir, relPath);
  const dir = path.dirname(full);
  const text = fs.readFileSync(full, 'utf8');
  const nameMatch = text.match(/^\s*name\s*=\s*["']([^"']+)["']/m);
  const verMatch = text.match(/^\s*version\s*=\s*["']([^"']+)["']/m);
  const pyMatch = text.match(/^\s*requires-python\s*=\s*["']([^"']+)["']/m);
  let manager = 'pip';
  if (fs.existsSync(path.join(dir, 'uv.lock'))) manager = 'uv';
  else if (fs.existsSync(path.join(dir, 'poetry.lock'))) manager = 'poetry';
  return {
    path: relPath,
    dir: path.dirname(relPath),
    name: nameMatch ? nameMatch[1] : null,
    version: verMatch ? verMatch[1] : null,
    requiresPython: pyMatch ? pyMatch[1] : null,
    manager,
    hasLocalVenv:
      fs.existsSync(path.join(dir, '.venv')) ||
      fs.existsSync(path.join(dir, 'venv')),
  };
}

function inspectWorkflow(repoDir, relPath) {
  const text = fs.readFileSync(path.join(repoDir, relPath), 'utf8');
  const nodeVersions = [
    ...text.matchAll(/node-version\s*:\s*['"]?([^'"\s#]+)['"]?/g),
  ].map((m) => m[1]);
  const goVersions = [
    ...text.matchAll(/go-version(?:-file)?\s*:\s*['"]?([^'"\s#]+)['"]?/g),
  ].map((m) => m[1]);
  const pythonVersions = [
    ...text.matchAll(/python-version\s*:\s*['"]?([^'"\s#]+)['"]?/g),
  ].map((m) => m[1]);
  const usesGeminiCli = /run-gemini-cli/i.test(text);
  return {
    path: relPath,
    nodeVersions: [...new Set(nodeVersions)],
    goVersions: [...new Set(goVersions)],
    pythonVersions: [...new Set(pythonVersions)],
    usesGeminiCli,
  };
}

function detectLockstepVersions(repoDir, packageJsons, pyProjects, cargoTomls) {
  const sources = [];
  const rootPkg = packageJsons.find((p) => p.path === 'package.json');
  if (rootPkg?.version) {
    sources.push({ file: 'package.json', version: rootPkg.version });
  }
  const versionGo = path.join(repoDir, 'version.go');
  if (fs.existsSync(versionGo)) {
    const m = fs
      .readFileSync(versionGo, 'utf8')
      .match(/Version\s*=\s*"([^"]+)"/);
    if (m) sources.push({ file: 'version.go', version: m[1] });
  }
  for (const tsEntry of ['ts/index.ts', 'src/index.ts']) {
    const full = path.join(repoDir, tsEntry);
    if (fs.existsSync(full)) {
      const m = fs
        .readFileSync(full, 'utf8')
        .match(/VERSION\s*=\s*['"]([^'"]+)['"]/);
      if (m) sources.push({ file: tsEntry, version: m[1] });
    }
  }
  const rootPy = pyProjects.find((p) => p.path === 'pyproject.toml');
  if (rootPy?.version) {
    sources.push({ file: 'pyproject.toml', version: rootPy.version });
  }
  if (cargoTomls.includes('Cargo.toml')) {
    const m = fs
      .readFileSync(path.join(repoDir, 'Cargo.toml'), 'utf8')
      .match(/^\s*version\s*=\s*"([^"]+)"/m);
    if (m) sources.push({ file: 'Cargo.toml', version: m[1] });
  }
  const unique = [...new Set(sources.map((s) => s.version))];
  return {
    sources,
    inSync: unique.length <= 1,
    version: unique.length === 1 ? unique[0] : null,
  };
}

function checkGoOutdated(repoDir, goMod) {
  const cwd = path.join(repoDir, goMod.dir);
  const res = runCmd('go', ['list', '-m', '-u', '-json', 'all'], cwd, {
    GOWORK: 'off',
  });
  if (!res.ok) {
    return {
      path: goMod.path,
      error: res.stderr.trim().split('\n')[0] || 'go list failed',
      updates: [],
    };
  }
  const updates = [];
  // `go list -m -u -json all` emits concatenated JSON objects.
  const chunks = res.stdout.replace(/\}\s*\{/g, '}\n---SPLIT---\n{').split('\n---SPLIT---\n');
  for (const chunk of chunks) {
    const trimmed = chunk.trim();
    if (!trimmed) continue;
    try {
      const mod = JSON.parse(trimmed);
      if (mod.Main || !mod.Update?.Version) continue;
      updates.push({
        name: mod.Path,
        current: mod.Version,
        latest: mod.Update.Version,
        indirect: Boolean(mod.Indirect),
        bump: classifyBump(mod.Version, mod.Update.Version),
      });
    } catch {
      // ignore malformed chunk
    }
  }
  return { path: goMod.path, updates };
}

function checkNodeOutdated(repoDir, pkg) {
  if (!pkg.hasNodeModules && !pkg.lockfile) {
    return { path: pkg.path, skipped: 'no lockfile or node_modules', updates: [] };
  }
  const cwd = path.join(repoDir, pkg.dir);
  const res = runCmd('npm', ['outdated', '--json'], cwd);
  // npm outdated exits 1 when outdated packages exist, with JSON on stdout.
  if (!res.stdout.trim()) {
    return { path: pkg.path, updates: [] };
  }
  try {
    const parsed = JSON.parse(res.stdout);
    const updates = Object.entries(parsed).map(([name, rawInfo]) => {
      // npm workspaces may emit an array of entries per package name.
      const info = Array.isArray(rawInfo) ? rawInfo[0] ?? {} : rawInfo;
      return {
        name,
        current: info.current ?? null,
        wanted: info.wanted ?? null,
        latest: info.latest ?? null,
        depType: info.type ?? null,
        bump: classifyBump(info.current, info.latest),
      };
    });
    return { path: pkg.path, updates };
  } catch {
    return {
      path: pkg.path,
      error: res.stderr.trim().split('\n')[0] || 'npm outdated parse failed',
      updates: [],
    };
  }
}

function checkPythonOutdated(repoDir, pyProj) {
  const cwd = path.join(repoDir, pyProj.dir);
  const venvPip = [
    path.join(cwd, '.venv', 'bin', 'pip'),
    path.join(cwd, 'venv', 'bin', 'pip'),
  ].find((p) => fs.existsSync(p));

  if (!venvPip) {
    return {
      path: pyProj.path,
      skipped: 'no local .venv (avoiding global Python scan)',
      updates: [],
    };
  }
  const res = runCmd(venvPip, ['list', '--outdated', '--format=json'], cwd);
  if (!res.ok || !res.stdout.trim()) {
    return {
      path: pyProj.path,
      error: res.stderr.trim().split('\n')[0] || 'pip list --outdated failed',
      updates: [],
    };
  }
  try {
    const rows = JSON.parse(res.stdout);
    const updates = rows.map((r) => ({
      name: r.name,
      current: r.version,
      latest: r.latest_version,
      bump: classifyBump(r.version, r.latest_version),
    }));
    return { path: pyProj.path, updates };
  } catch {
    return { path: pyProj.path, error: 'pip outdated parse failed', updates: [] };
  }
}

function recommendSkills(found, workflows) {
  const skills = [];
  const add = (id, plugin, reason) => {
    if (!skills.some((s) => s.id === id)) {
      skills.push({ id, plugin, reason });
    }
  };

  if (found.goMods.length > 0 || found.dockerfiles.length > 0) {
    add(
      'go-security-audit',
      'repo-authoring',
      `${found.goMods.length} go.mod / ${found.dockerfiles.length} Dockerfile(s)`,
    );
  }
  if (found.goFiles > 0) {
    add('go-readability', 'go-readability', `${found.goFiles} Go source file(s)`);
  }
  if (found.packageJsons.length > 0) {
    add(
      'node-security-audit',
      'repo-authoring',
      `${found.packageJsons.length} package.json manifest(s)`,
    );
  }
  if (
    found.pyFiles > 0 ||
    found.pyProjects.length > 0 ||
    found.requirements.length > 0
  ) {
    add(
      'python-readability',
      'python-readability',
      `${found.pyFiles} Python file(s) / ${found.pyProjects.length} pyproject.toml`,
    );
  }
  if (
    found.swiftFiles > 0 ||
    found.swiftPackages.length > 0 ||
    found.xcodeProjects.length > 0
  ) {
    add(
      'quick-bounce-assessor',
      'macos-performance',
      `${found.swiftFiles} Swift file(s) / ${found.xcodeProjects.length} Xcode project(s)`,
    );
    add(
      'macos-hig-reviewer',
      'macos-hig',
      `${found.swiftFiles} Swift file(s) / macOS UI review`,
    );
  }
  if (workflows.some((w) => w.usesGeminiCli)) {
    add(
      'geminicli-github-action-review',
      'mcp-security',
      'GitHub Actions workflow invokes run-gemini-cli',
    );
  }
  if (found.mcpConfigs.length > 0) {
    add(
      'mcp-auditor',
      'mcp-security',
      `${found.mcpConfigs.length} MCP config file(s)`,
    );
  }
  if (found.hasChangelog) {
    add('changelog-manager', 'repo-authoring', 'CHANGELOG.md present');
  }
  if (found.hasReadme) {
    add('make-readme', 'repo-authoring', 'README.md present');
  }
  if (found.hasBeads) {
    add(
      'bd-dolt-troubleshooter',
      'beads-workflow',
      '.beads/ present (fallback if bd/Dolt errors occur)',
    );
  }

  return skills;
}

function scanTarget(targetDir, opts) {
  if (!fs.existsSync(targetDir)) {
    return { path: targetDir, error: 'path does not exist' };
  }
  const git = inspectGit(targetDir);
  const found = walkRepo(targetDir, opts.maxDepth);
  const goMods = found.goMods.map((p) => parseGoMod(targetDir, p));
  const packageJsons = found.packageJsons.map((p) =>
    parsePackageJson(targetDir, p),
  );
  const pyProjects = found.pyProjects.map((p) => parsePyProject(targetDir, p));
  const workflows = found.workflows.map((p) => inspectWorkflow(targetDir, p));
  const lockstep = detectLockstepVersions(
    targetDir,
    packageJsons,
    pyProjects,
    found.cargoTomls,
  );
  const recommendedSkills = recommendSkills(found, workflows);

  const stacks = [];
  if (goMods.length > 0 || found.goFiles > 0) stacks.push('go');
  if (packageJsons.length > 0) stacks.push('node');
  if (
    pyProjects.length > 0 ||
    found.requirements.length > 0 ||
    found.pyFiles > 0
  ) {
    stacks.push('python');
  }
  if (
    found.swiftPackages.length > 0 ||
    found.xcodeProjects.length > 0 ||
    found.swiftFiles > 0
  ) {
    stacks.push('swift');
  }
  if (found.cargoTomls.length > 0) stacks.push('rust');
  if (found.dockerfiles.length > 0) stacks.push('docker');
  if (workflows.length > 0) stacks.push('github-actions');

  let outdated = null;
  if (opts.outdated) {
    outdated = {
      go: goMods.map((gm) => checkGoOutdated(targetDir, gm)),
      node: packageJsons
        .filter((p) => !p.parseError && (p.lockfile || p.hasNodeModules))
        .map((p) => checkNodeOutdated(targetDir, p)),
      python: pyProjects.map((p) => checkPythonOutdated(targetDir, p)),
    };
  }

  return {
    name: path.basename(targetDir),
    path: targetDir,
    git,
    stacks,
    manifests: {
      go: goMods,
      goWork: found.goWork,
      node: packageJsons,
      python: pyProjects,
      requirements: found.requirements,
      swiftPackages: found.swiftPackages,
      xcodeProjects: found.xcodeProjects,
      cargoTomls: found.cargoTomls,
      dockerfiles: found.dockerfiles,
      workflows,
      mcpConfigs: found.mcpConfigs,
    },
    lockstep,
    flags: {
      hasBeads: found.hasBeads,
      hasChangelog: found.hasChangelog,
      hasReadme: found.hasReadme,
      hasMakefile: found.hasMakefile,
    },
    recommendedSkills,
    outdated,
  };
}

function renderMarkdown(report) {
  const lines = [];
  lines.push('# Repository Health & Stack Detection Report');
  lines.push(`- **Scanned At**: \`${report.scannedAt}\``);
  lines.push(`- **Targets**: ${report.targets.length}`);
  lines.push('');

  for (const t of report.targets) {
    if (t.error) {
      lines.push(`## ${t.path} — ERROR: ${t.error}`);
      lines.push('');
      continue;
    }
    lines.push(`## \`${t.name}\` (\`${t.path}\`)`);
    lines.push(
      `- **Stacks**: ${t.stacks.length ? t.stacks.map((s) => `\`${s}\``).join(', ') : '_(none detected)_'}`,
    );
    if (t.git.isGitRepo) {
      const sync =
        t.git.behind > 0
          ? `**BEHIND ${t.git.behind}** (run \`git fetch && git pull --rebase\` first)`
          : t.git.ahead > 0
            ? `ahead ${t.git.ahead}`
            : 'in sync';
      const dirty =
        t.git.dirtyCount > 0
          ? `${t.git.dirtyCount} dirty path(s) — preserve unrelated edits`
          : 'clean';
      lines.push(
        `- **Git**: branch \`${t.git.branch}\` (${sync}; ${dirty})`,
      );
    }
    if (t.lockstep.sources.length > 0) {
      const status = t.lockstep.inSync
        ? `OK (\`${t.lockstep.version}\`)`
        : '**MISMATCH**';
      const files = t.lockstep.sources
        .map((s) => `${s.file}=${s.version}`)
        .join(', ');
      lines.push(`- **Lockstep Version**: ${status} — ${files}`);
    }
    lines.push('');

    if (t.recommendedSkills.length > 0) {
      lines.push('### Recommended Specialist Skills');
      lines.push('| Skill ID | Plugin | Triggered By |');
      lines.push('| :--- | :--- | :--- |');
      for (const s of t.recommendedSkills) {
        lines.push(`| \`${s.id}\` | \`${s.plugin}\` | ${s.reason} |`);
      }
      lines.push('');
    }

    if (t.outdated) {
      lines.push('### Dependency Freshness (`--outdated`)');
      for (const g of t.outdated.go) {
        const direct = g.updates.filter((u) => !u.indirect);
        const indirect = g.updates.filter((u) => u.indirect);
        lines.push(
          `- **Go \`${g.path}\`**: ${direct.length} direct update(s), ${indirect.length} indirect update(s)${g.error ? ` (error: ${g.error})` : ''}`,
        );
        for (const u of direct) {
          lines.push(
            `  - \`${u.name}\`: ${u.current} → ${u.latest} (${u.bump})`,
          );
        }
      }
      for (const n of t.outdated.node) {
        lines.push(
          `- **Node \`${n.path}\`**: ${n.updates.length} update(s)${n.skipped ? ` (${n.skipped})` : ''}${n.error ? ` (error: ${n.error})` : ''}`,
        );
        for (const u of n.updates) {
          lines.push(
            `  - \`${u.name}\`: ${u.current} → ${u.latest} (${u.bump})`,
          );
        }
      }
      for (const p of t.outdated.python) {
        lines.push(
          `- **Python \`${p.path}\`**: ${p.updates.length} update(s)${p.skipped ? ` (${p.skipped})` : ''}${p.error ? ` (error: ${p.error})` : ''}`,
        );
        for (const u of p.updates.slice(0, 15)) {
          lines.push(
            `  - \`${u.name}\`: ${u.current} → ${u.latest} (${u.bump})`,
          );
        }
      }
      lines.push('');
    }
  }
  return lines.join('\n');
}

function main() {
  const opts = parseArgs(process.argv.slice(2));
  if (opts.help) {
    console.log(`Usage: detect-stack.mjs [target-path...] [options]

Options:
  --outdated       Run read-only dependency freshness checks (go list, npm outdated, local venv pip)
  --json           Emit structured JSON summary
  --max-depth N    Directory recursion depth (default: 5)
  -h, --help       Show this help message`);
    process.exit(0);
  }

  const targets = opts.targets.map((dir) => scanTarget(dir, opts));
  const allSkills = [
    ...new Set(
      targets.flatMap((t) => (t.recommendedSkills ?? []).map((s) => s.id)),
    ),
  ];

  const report = {
    scannedAt: new Date().toISOString(),
    targets,
    summary: {
      targetCount: targets.length,
      stacks: [...new Set(targets.flatMap((t) => t.stacks ?? []))],
      recommendedSkills: allSkills,
      anyBehindRemote: targets.some((t) => t.git?.behind > 0),
      anyDirtyWorktree: targets.some((t) => t.git?.dirtyCount > 0),
      anyLockstepMismatch: targets.some(
        (t) => t.lockstep && !t.lockstep.inSync,
      ),
    },
  };

  if (opts.json) {
    console.log(JSON.stringify(report, null, 2));
  } else {
    console.log(renderMarkdown(report));
  }
}

main();
