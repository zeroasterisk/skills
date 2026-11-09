#!/usr/bin/env node
/**
 * audit-go-repo.mjs — Audits one or more Go repositories for go.mod toolchain floors,
 * stdlib security patch floors (go >= 1.26.10), Dockerfile builder/runtime alignment,
 * .gitignore/.gcloudignore hygiene, git sync status, and optional govulncheck summaries.
 *
 * Usage:
 *   ./scripts/audit-go-repo.mjs <path> [--vulncheck] [--json]
 */

import { execFile } from "node:child_process";
import { access, readdir, readFile } from "node:fs/promises";
import { constants } from "node:fs";
import { basename, dirname, join, relative, resolve } from "node:path";
import { promisify } from "node:util";

const run = promisify(execFile);

const RECOMMENDED_GO_FLOOR = [1, 26, 0];
const RECOMMENDED_GO_PATCH_FLOOR = [1, 26, 10];
const RECOMMENDED_IGNORES = [".serena", ".beads", ".dolt"];

async function exists(p) {
  try {
    await access(p, constants.F_OK);
    return true;
  } catch {
    return false;
  }
}

function parseSemver(v) {
  const m = /(\d+)(?:\.(\d+))?(?:\.(\d+))?/.exec(String(v ?? ""));
  return m ? [Number(m[1]), Number(m[2] ?? 0), Number(m[3] ?? 0)] : null;
}

function compareSemver(a, b) {
  for (let i = 0; i < 3; i += 1) {
    if ((a[i] ?? 0) !== (b[i] ?? 0)) return (a[i] ?? 0) - (b[i] ?? 0);
  }
  return 0;
}

async function findGoMods(root, maxDepth = 5, depth = 0) {
  if (depth > maxDepth) return [];
  const results = [];
  let entries = [];
  try {
    entries = await readdir(root, { withFileTypes: true });
  } catch {
    return results;
  }
  for (const e of entries) {
    if (
      e.name === "node_modules" ||
      e.name === ".git" ||
      e.name === "vendor" ||
      e.name === "dist" ||
      e.name === ".astro" ||
      e.name.startsWith(".site-e2e-")
    ) {
      continue;
    }
    const full = join(root, e.name);
    if (e.isFile() && e.name === "go.mod") {
      results.push(full);
    } else if (e.isDirectory()) {
      results.push(...(await findGoMods(full, maxDepth, depth + 1)));
    }
  }
  return results.sort();
}

function parseGoMod(raw) {
  const modMatch = /^module\s+(\S+)/m.exec(raw);
  const goMatch = /^go\s+(\S+)/m.exec(raw);
  const toolchainMatch = /^toolchain\s+(\S+)/m.exec(raw);

  const directDeps = [];
  const lines = raw.split("\n");
  let inRequire = false;
  for (const line of lines) {
    const trimmed = line.trim();
    if (/^require\s*\($/.test(trimmed)) {
      inRequire = true;
      continue;
    }
    if (inRequire && trimmed === ")") {
      inRequire = false;
      continue;
    }
    if (inRequire && trimmed && !trimmed.startsWith("//")) {
      const isIndirect = /\/\/\s*indirect\b/.test(trimmed);
      const parts = trimmed.split(/\s+/);
      if (parts.length >= 2 && !isIndirect) {
        directDeps.push({ module: parts[0], version: parts[1] });
      }
    } else if (/^require\s+\S+\s+\S+/.test(trimmed) && !/\/\/\s*indirect\b/.test(trimmed)) {
      const parts = trimmed.replace(/^require\s+/, "").split(/\s+/);
      directDeps.push({ module: parts[0], version: parts[1] });
    }
  }

  return {
    moduleName: modMatch ? modMatch[1] : null,
    goVersion: goMatch ? goMatch[1] : null,
    toolchain: toolchainMatch ? toolchainMatch[1] : null,
    directDeps,
  };
}

async function inspectDockerfile(modDir, goVersionTuple) {
  const dockerfilePath = join(modDir, "Dockerfile");
  if (!(await exists(dockerfilePath))) {
    return { present: false };
  }
  const raw = await readFile(dockerfilePath, "utf8");
  const fromGolang = /^FROM\s+golang:([^\s]+)/im.exec(raw);
  const golangTag = fromGolang ? fromGolang[1] : null;
  const dockerGoTuple = golangTag ? parseSemver(golangTag) : null;

  let builderAligned = null;
  if (dockerGoTuple && goVersionTuple) {
    builderAligned =
      dockerGoTuple[0] === goVersionTuple[0] && dockerGoTuple[1] === goVersionTuple[1];
  }

  const hasAptGet = /apt-get\s+install/.test(raw);
  const hasAptUpgrade = /apt-get\s+upgrade\s+-y/.test(raw);

  return {
    present: true,
    golangTag,
    builderAligned,
    hasAptGet,
    hasAptUpgrade: hasAptGet ? hasAptUpgrade : null,
  };
}

function hasIgnoreEntry(raw, token, allowSubpath = false) {
  const escaped = token.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
  const pattern = allowSubpath
    ? new RegExp(`^\\s*\\/?${escaped}(?:\\/|$)`, "m")
    : new RegExp(`^\\s*\\/?${escaped}\\/?\\s*$`, "m");
  return pattern.test(raw);
}

async function inspectIgnoreFiles(modDir) {
  const gitignorePath = join(modDir, ".gitignore");
  const gcloudignorePath = join(modDir, ".gcloudignore");

  const hasGitignore = await exists(gitignorePath);
  const hasGcloudignore = await exists(gcloudignorePath);

  const gitRaw = hasGitignore ? await readFile(gitignorePath, "utf8") : "";
  const gcloudRaw = hasGcloudignore ? await readFile(gcloudignorePath, "utf8") : "";

  const missingGitignore = hasGitignore
    ? RECOMMENDED_IGNORES.filter(
        (item) => !hasIgnoreEntry(gitRaw, item, item === ".beads"),
      )
    : [];
  const missingGcloudignore = hasGcloudignore
    ? RECOMMENDED_IGNORES.filter((item) => !hasIgnoreEntry(gcloudRaw, item, false))
    : [];

  return {
    hasGitignore,
    hasGcloudignore,
    missingGitignore,
    missingGcloudignore,
  };
}

async function checkGitStatus(modDir) {
  try {
    const { stdout } = await run("git", ["status", "-sb"], { cwd: modDir });
    const firstLine = stdout.split("\n")[0] ?? "";
    const behind = /\[.*behind\s+\d+.*\]/.test(firstLine);
    return { branchStatus: firstLine.replace(/^##\s*/, "").trim(), behind };
  } catch {
    return { branchStatus: null, behind: false };
  }
}

async function runGovulncheck(modDir) {
  let rawOut = "";
  try {
    const { stdout } = await run(
      "go",
      ["run", "golang.org/x/vuln/cmd/govulncheck@latest", "-json", "./..."],
      { cwd: modDir, maxBuffer: 64 * 1024 * 1024 },
    );
    rawOut = stdout;
  } catch (err) {
    rawOut = err.stdout ?? "";
    if (!rawOut) {
      return { error: err.message };
    }
  }

  const symbolOsvs = new Set();
  const packageOsvs = new Set();
  const moduleOsvs = new Set();

  // Stream of concatenated JSON objects emitted by govulncheck -json
  const decoder = rawOut.split(/\n(?=\{)/);
  let buf = "";
  for (const chunk of decoder) {
    buf += (buf ? "\n" : "") + chunk;
    try {
      const msg = JSON.parse(buf);
      buf = "";
      if (msg.finding && msg.finding.osv) {
        const id = msg.finding.osv;
        const firstTrace = (msg.finding.trace ?? [])[0] ?? {};
        if (firstTrace.function) {
          symbolOsvs.add(id);
        } else if (firstTrace.package) {
          packageOsvs.add(id);
        } else {
          moduleOsvs.add(id);
        }
      }
    } catch {
      // wait for complete JSON object
    }
  }

  for (const id of symbolOsvs) {
    packageOsvs.delete(id);
    moduleOsvs.delete(id);
  }
  for (const id of packageOsvs) {
    moduleOsvs.delete(id);
  }

  const uncalledNotices = [...moduleOsvs].filter((id) => id === "GO-2026-5932");

  return {
    symbolCount: symbolOsvs.size,
    packageCount: packageOsvs.size,
    moduleCount: moduleOsvs.size,
    symbolIds: [...symbolOsvs].sort(),
    packageIds: [...packageOsvs].sort(),
    moduleIds: [...moduleOsvs].sort(),
    uncalledDeprecationNotices: uncalledNotices,
  };
}

async function auditGoModule(modPath, workspaceRoot, withVulncheck = false) {
  const modDir = dirname(modPath);
  const relDir = relative(workspaceRoot, modDir) || basename(modDir);
  const raw = await readFile(modPath, "utf8");
  const parsed = parseGoMod(raw);
  const goTuple = parseSemver(parsed.goVersion);
  const meetsFloor = goTuple ? compareSemver(goTuple, RECOMMENDED_GO_FLOOR) >= 0 : false;
  const meetsPatchFloor = goTuple
    ? compareSemver(goTuple, RECOMMENDED_GO_PATCH_FLOOR) >= 0
    : false;

  const dockerfile = await inspectDockerfile(modDir, goTuple);
  const ignores = await inspectIgnoreFiles(modDir);
  const git = await checkGitStatus(modDir);
  const vulncheck = withVulncheck ? await runGovulncheck(modDir) : null;

  return {
    subproject: relDir,
    path: modDir,
    moduleName: parsed.moduleName,
    goVersion: parsed.goVersion,
    toolchain: parsed.toolchain,
    meetsGo126Floor: meetsFloor,
    meetsGo126PatchFloor: meetsPatchFloor,
    directDependencyCount: parsed.directDeps.length,
    directDependencies: parsed.directDeps,
    dockerfile,
    ignores,
    git,
    ...(vulncheck ? { vulncheck } : {}),
  };
}

async function main() {
  const args = process.argv.slice(2);
  const jsonFlag = args.includes("--json");
  const vulncheckFlag = args.includes("--vulncheck");
  const targetArg = args.find((a) => !a.startsWith("--")) ?? process.cwd();
  const targetPath = resolve(targetArg);

  const modPaths = await findGoMods(targetPath, 5);
  const reports = [];
  for (const modPath of modPaths) {
    reports.push(await auditGoModule(modPath, targetPath, vulncheckFlag));
  }

  const summary = {
    scannedAt: new Date().toISOString(),
    targetPath,
    modulesScanned: reports.length,
    belowGoFloor: reports.filter((r) => !r.meetsGo126Floor).length,
    belowGoPatchFloor: reports.filter((r) => !r.meetsGo126PatchFloor).length,
    dockerfileDrift: reports.filter((r) => r.dockerfile.present && r.dockerfile.builderAligned === false).length,
    reports,
  };

  if (jsonFlag) {
    console.log(JSON.stringify(summary, null, 2));
    return;
  }

  console.log(`# Go & Container Security Audit Report`);
  console.log(`- **Target**: \`${targetPath}\``);
  console.log(
    `- **Go Modules Scanned**: ${summary.modulesScanned} (${summary.belowGoFloor} below \`go 1.26.0\` module floor, ${summary.belowGoPatchFloor} below \`go 1.26.10\` stdlib security floor, ${summary.dockerfileDrift} with Dockerfile toolchain drift)\n`,
  );

  const vulnHeader = vulncheckFlag ? " `govulncheck` (Sym/Pkg/Mod) |" : "";
  const vulnSep = vulncheckFlag ? " :--- |" : "";
  console.log(
    `| Subproject | Module | \`go.mod\` | Floor (\`>=1.26.10\`) | Direct Deps | Dockerfile Builder | \`apt-get upgrade\` |${vulnHeader} Git Sync |`,
  );
  console.log(`| :--- | :--- | :--- | :--- | ---: | :--- | :--- |${vulnSep} :--- |`);

  for (const r of reports) {
    const dfBuilder = !r.dockerfile.present
      ? "—"
      : r.dockerfile.golangTag
        ? `\`golang:${r.dockerfile.golangTag}\` (${r.dockerfile.builderAligned ? "OK" : "DRIFT"})`
        : "no golang stage";
    const dfUpgrade = !r.dockerfile.present || r.dockerfile.hasAptUpgrade === null
      ? "—"
      : r.dockerfile.hasAptUpgrade
        ? "OK"
        : "MISSING";
    const gitState = r.git.behind ? `BEHIND (${r.git.branchStatus})` : "OK";
    const floorStatus = r.meetsGo126PatchFloor
      ? "OK"
      : r.meetsGo126Floor
        ? "STDLIB-PATCH (`<1.26.10`)"
        : "UPGRADE (`<1.26.0`)";
    const vulnCol = vulncheckFlag
      ? r.vulncheck?.error
        ? ` ERROR |`
        : ` **${r.vulncheck.symbolCount}** / ${r.vulncheck.packageCount} / ${r.vulncheck.moduleCount} |`
      : "";
    console.log(
      `| \`${r.subproject}\` | \`${r.moduleName ?? "—"}\` | \`${r.goVersion ?? "—"}\` | ${floorStatus} | ${r.directDependencyCount} | ${dfBuilder} | ${dfUpgrade} |${vulnCol} ${gitState} |`,
    );
  }
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
