#!/usr/bin/env node
/**
 * audit-repo.mjs — Audits one or more repositories for Node.js runtime floors,
 * .nvmrc / .node-version / GitHub Actions workflow pins, npm/pnpm dependency
 * vulnerabilities, exact-pin policies, and coupled guardrail tests.
 *
 * Usage:
 *   ./scripts/audit-repo.mjs <path> [--all] [--json]
 */

import { execFile } from "node:child_process";
import { access, readdir, readFile } from "node:fs/promises";
import { constants, realpathSync } from "node:fs";
import { basename, dirname, join, relative, resolve } from "node:path";
import { promisify } from "node:util";

const run = promisify(execFile);

// Minimum patched Node.js versions per release line (October 21, 2026 Security Release)
const SECURITY_FLOORS = {
  22: [22, 23, 4],
  24: [24, 22, 1],
  26: [26, 12, 1],
};

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

function meetsSecurityFloor(verTupleOrSpec) {
  if (typeof verTupleOrSpec === "string" && verTupleOrSpec.includes("||")) {
    const clauses = verTupleOrSpec
      .split("||")
      .map((s) => s.trim())
      .filter(Boolean);
    const checks = clauses.map((c) => meetsSecurityFloor(parseSemver(c)));
    const allOk = checks.length > 0 && checks.every((c) => c.ok);
    return {
      ok: allOk,
      reason: checks.map((c) => c.reason).join(" ; "),
    };
  }
  const verTuple = Array.isArray(verTupleOrSpec)
    ? verTupleOrSpec
    : parseSemver(verTupleOrSpec);
  if (!verTuple) return { ok: false, reason: "unparseable version" };
  const [maj, min, pat] = verTuple;
  const floor = SECURITY_FLOORS[maj];
  if (!floor) {
    if (maj < 22) return { ok: false, reason: `Node ${maj}.x is End-of-Life (requires >=22.23.4)` };
    return { ok: true, reason: `Node ${maj}.x` };
  }
  const [, fMin, fPat] = floor;
  const ok = min > fMin || (min === fMin && pat >= fPat);
  return {
    ok,
    expected: `>=${floor.join(".")}`,
    reason: ok ? `meets >=${floor.join(".")}` : `below Oct 2026 security floor >=${floor.join(".")}`,
  };
}

async function findPackageJsons(root, maxDepth = 5, depth = 0) {
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
      e.name === "dist" ||
      e.name === ".astro" ||
      e.name.startsWith(".site-e2e-")
    ) {
      continue;
    }
    const full = join(root, e.name);
    if (e.isFile() && e.name === "package.json") {
      results.push(full);
    } else if (e.isDirectory()) {
      results.push(...(await findPackageJsons(full, maxDepth, depth + 1)));
    }
  }
  return results.sort();
}

async function detectRuntimeAndCiFiles(subprojectDir, workspaceRoot) {
  const dirsToCheck = [...new Set([subprojectDir, workspaceRoot])];
  const findings = [];

  for (const d of dirsToCheck) {
    for (const rcName of [".nvmrc", ".node-version"]) {
      const p = join(d, rcName);
      if (await exists(p)) {
        const raw = (await readFile(p, "utf8")).trim();
        const check = meetsSecurityFloor(raw);
        findings.push({
          file: relative(workspaceRoot, p) || rcName,
          version: raw,
          ok: check.ok,
          note: check.reason,
        });
      }
    }
    const wfDir = join(d, ".github", "workflows");
    if (await exists(wfDir)) {
      let wfFiles = [];
      try {
        wfFiles = await readdir(wfDir);
      } catch {
        wfFiles = [];
      }
      for (const wf of wfFiles) {
        if (!/\.(yml|yaml)$/.test(wf)) continue;
        const wfPath = join(wfDir, wf);
        const content = await readFile(wfPath, "utf8");
        for (const m of content.matchAll(/node-version\s*:\s*['"]?([0-9]+\.[0-9]+(?:\.[0-9]+)?|[0-9]+)['"]?/g)) {
          const ver = m[1];
          const check = meetsSecurityFloor(ver);
          findings.push({
            file: relative(workspaceRoot, wfPath) || `.github/workflows/${wf}`,
            version: ver,
            ok: check.ok,
            note: check.reason,
          });
        }
      }
    }
  }
  return findings;
}

async function detectGuardrails(subprojectDir) {
  const testDirs = ["tests", "test", "__tests__"];
  const guardrails = [];
  for (const d of testDirs) {
    const abs = join(subprojectDir, d);
    if (!(await exists(abs))) continue;
    let files = [];
    try {
      files = await readdir(abs);
    } catch {
      continue;
    }
    for (const f of files) {
      if (!/\.(mjs|js|ts|mts)$/.test(f)) continue;
      const content = await readFile(join(abs, f), "utf8");
      const signals = [];
      if (/\bPINNED\b/.test(content) || /pin it exactly/i.test(content)) {
        signals.push("exact-dependency-pins");
      }
      if (/engines\.node/.test(content)) {
        signals.push("engines.node-assertion");
      }
      if (/package-lock\.json/.test(content)) {
        signals.push("lockfile-parity-check");
      }
      if (/workflows/.test(f) || /\.github\/workflows/.test(content)) {
        signals.push("workflow-meta-test");
      }
      if (signals.length > 0) {
        guardrails.push({ file: `${d}/${f}`, signals });
      }
    }
  }
  return guardrails;
}

async function runPackageAudit(subprojectDir) {
  if (await exists(join(subprojectDir, "package-lock.json"))) {
    try {
      const { stdout } = await run("npm", ["audit", "--json"], {
        cwd: subprojectDir,
        maxBuffer: 32 * 1024 * 1024,
      });
      return parseNpmAuditJson(stdout, "npm");
    } catch (err) {
      if (err.stdout) {
        try {
          return parseNpmAuditJson(err.stdout, "npm");
        } catch {
          // fall through
        }
      }
      return { error: err.message };
    }
  }
  if (await exists(join(subprojectDir, "pnpm-lock.yaml"))) {
    try {
      const { stdout } = await run("pnpm", ["audit", "--json"], {
        cwd: subprojectDir,
        maxBuffer: 32 * 1024 * 1024,
      });
      return parsePnpmAuditJson(stdout);
    } catch (err) {
      if (err.stdout) {
        try {
          return parsePnpmAuditJson(err.stdout);
        } catch {
          // fall through
        }
      }
      return { error: err.message };
    }
  }
  return { skipped: true, reason: "no lockfile" };
}

function parseNpmAuditJson(rawJson, manager = "npm") {
  const data = JSON.parse(rawJson);
  const counts = data.metadata?.vulnerabilities ?? {
    info: 0,
    low: 0,
    moderate: 0,
    high: 0,
    critical: 0,
    total: 0,
  };
  const vulns = Object.values(data.vulnerabilities ?? {}).map((v) => ({
    name: v.name,
    severity: v.severity,
    isDirect: Boolean(v.isDirect),
    range: v.range,
    fixAvailable: v.fixAvailable,
    advisories: (v.via ?? [])
      .filter((x) => typeof x === "object" && x !== null)
      .map((x) => ({
        title: x.title,
        url: x.url,
        severity: x.severity,
        range: x.range,
      })),
  }));
  return { skipped: false, manager, counts, vulns };
}

function parsePnpmAuditJson(rawJson) {
  const data = JSON.parse(rawJson);
  const vMeta = data.metadata?.vulnerabilities ?? {};
  const counts = {
    info: vMeta.info ?? 0,
    low: vMeta.low ?? 0,
    moderate: vMeta.moderate ?? 0,
    high: vMeta.high ?? 0,
    critical: vMeta.critical ?? 0,
    total:
      (vMeta.info ?? 0) +
      (vMeta.low ?? 0) +
      (vMeta.moderate ?? 0) +
      (vMeta.high ?? 0) +
      (vMeta.critical ?? 0),
  };
  const vulns = Object.values(data.advisories ?? {}).map((adv) => ({
    name: adv.module_name,
    severity: adv.severity,
    isDirect: (adv.findings ?? []).some((f) => (f.paths ?? []).some((p) => !p.includes(">"))),
    range: adv.vulnerable_versions,
    fixAvailable: adv.patched_versions !== "<0.0.0",
    advisories: [
      {
        title: adv.title,
        url: adv.url,
        severity: adv.severity,
        range: adv.vulnerable_versions,
      },
    ],
  }));
  return { skipped: false, manager: "pnpm", counts, vulns };
}

async function auditSubproject(pkgPath, workspaceRoot) {
  const subprojectDir = dirname(pkgPath);
  const relDir = relative(workspaceRoot, subprojectDir) || basename(subprojectDir);
  const manifest = JSON.parse(await readFile(pkgPath, "utf8"));
  const deps = { ...manifest.dependencies, ...manifest.devDependencies };
  const depEntries = Object.entries(deps);

  const exactMatch = /^\d+\.\d+\.\d+(?:-[0-9A-Za-z.-]+)?$/;
  const allExact = depEntries.length > 0 && depEntries.every(([, v]) => exactMatch.test(v));
  const pinPolicy = depEntries.length === 0 ? "none" : allExact ? "exact" : "range";

  const enginesNode = manifest.engines?.node ?? null;
  const enginesCheck = enginesNode ? meetsSecurityFloor(enginesNode) : null;
  const overrides = manifest.overrides ?? manifest.pnpm?.overrides ?? {};

  const runtimePins = await detectRuntimeAndCiFiles(subprojectDir, workspaceRoot);
  const guardrails = await detectGuardrails(subprojectDir);
  const audit = await runPackageAudit(subprojectDir);

  return {
    subproject: relDir,
    path: subprojectDir,
    name: manifest.name ?? basename(subprojectDir),
    pinPolicy,
    overrides,
    enginesNode,
    enginesFloorOk: enginesCheck ? enginesCheck.ok : null,
    enginesFloorNote: enginesCheck ? enginesCheck.reason : "no engines.node declared",
    runtimePins,
    directDependencies: manifest.dependencies ?? {},
    devDependencies: manifest.devDependencies ?? {},
    guardrails,
    audit,
  };
}

async function main() {
  const args = process.argv.slice(2);
  const jsonFlag = args.includes("--json");
  const targetArg = args.find((a) => !a.startsWith("--")) ?? process.cwd();
  const targetPath = resolve(targetArg);

  const localNodeVer = process.versions.node;
  const localNodeCheck = meetsSecurityFloor(parseSemver(localNodeVer));
  let realExecPath = process.execPath;
  try {
    realExecPath = realpathSync(process.execPath);
  } catch {
    // keep process.execPath
  }

  const pkgPaths = await findPackageJsons(targetPath, 5);
  const reports = [];
  for (const pkgPath of pkgPaths) {
    reports.push(await auditSubproject(pkgPath, targetPath));
  }

  const summary = {
    scannedAt: new Date().toISOString(),
    targetPath,
    localRuntime: {
      node: `v${localNodeVer}`,
      execPath: process.execPath,
      realpath: realExecPath,
      meetsOct2026Floor: localNodeCheck.ok,
      note: localNodeCheck.reason,
    },
    subprojectsScanned: reports.length,
    vulnerableSubprojects: reports.filter((r) => (r.audit?.counts?.total ?? 0) > 0).length,
    totalVulnerabilities: reports.reduce((acc, r) => acc + (r.audit?.counts?.total ?? 0), 0),
    reports,
  };

  if (jsonFlag) {
    console.log(JSON.stringify(summary, null, 2));
    return;
  }

  const binPathNote =
    process.execPath !== realExecPath
      ? ` [\`${process.execPath}\` -> \`${realExecPath}\`]`
      : ` [\`${process.execPath}\`]`;
  console.log(`# Node Security Audit Report`);
  console.log(`- **Target**: \`${targetPath}\``);
  console.log(
    `- **Local Runtime**: \`v${localNodeVer}\` (${localNodeCheck.ok ? "PASS" : "VULNERABLE"}: ${localNodeCheck.reason})${binPathNote}`,
  );
  console.log(
    `- **Subprojects Scanned**: ${summary.subprojectsScanned} (${summary.vulnerableSubprojects} with npm audit vulnerabilities, ${summary.totalVulnerabilities} total findings)\n`,
  );

  console.log(
    `| Subproject | Pin Policy | \`engines.node\` | Crit | High | Mod | Low | Total | Guardrail Tests |`,
  );
  console.log(`| :--- | :--- | :--- | ---: | ---: | ---: | ---: | ---: | :--- |`);
  for (const r of reports) {
    const c = r.audit?.counts;
    const eng = r.enginesNode
      ? `${r.enginesNode} (${r.enginesFloorOk ? "OK" : "OLD"})`
      : "*(missing)*";
    const g =
      r.guardrails.length > 0
        ? r.guardrails.map((x) => `${x.file}`).join(", ")
        : "—";
    if (r.audit?.skipped) {
      console.log(
        `| \`${r.subproject}\` | ${r.pinPolicy} | ${eng} | - | - | - | - | *(no lockfile)* | ${g} |`,
      );
    } else if (r.audit?.error) {
      console.log(
        `| \`${r.subproject}\` | ${r.pinPolicy} | ${eng} | ? | ? | ? | ? | *(audit error)* | ${g} |`,
      );
    } else {
      console.log(
        `| \`${r.subproject}\` | ${r.pinPolicy} | ${eng} | ${c.critical} | ${c.high} | ${c.moderate} | ${c.low} | **${c.total}** | ${g} |`,
      );
    }
  }

  const actionable = reports.filter(
    (r) =>
      (r.audit?.counts?.total ?? 0) > 0 ||
      r.enginesFloorOk !== true ||
      (r.runtimePins ?? []).some((p) => !p.ok),
  );
  if (actionable.length > 0) {
    console.log(`\n## Actionable Findings`);
    for (const r of actionable) {
      console.log(`\n### \`${r.subproject}\` (\`${r.path}\`)`);
      console.log(`- **Pin Policy**: \`${r.pinPolicy}\``);
      if (r.enginesNode) {
        console.log(`- **Engines Floor**: \`${r.enginesNode}\` -> ${r.enginesFloorNote}`);
      } else {
        console.log(
          `- **Engines Floor**: *(missing)* -> add \`"engines": { "node": ">=22.23.4" }\` to \`package.json\``,
        );
      }
      for (const p of r.runtimePins ?? []) {
        if (!p.ok) {
          console.log(`- **CI / Runtime Pin**: \`${p.file}\` (\`${p.version}\`) -> ${p.note}`);
        }
      }
      if (r.guardrails.length > 0) {
        console.log(
          `- **Coupled Guardrail Tests**: ${r.guardrails.map((g) => `\`${g.file}\` (${g.signals.join(", ")})`).join("; ")}`,
        );
      }
      for (const v of r.audit?.vulns ?? []) {
        const kind = v.isDirect ? "Direct" : "Transitive";
        const fix =
          typeof v.fixAvailable === "object"
            ? `upgrade \`${v.fixAvailable.name}@${v.fixAvailable.version}\`${v.fixAvailable.isSemVerMajor ? " (major)" : ""}`
            : v.fixAvailable
              ? "via lockfile refresh / parent upgrade"
              : "no automatic fix";
        const titles = v.advisories.map((a) => `${a.title} (${a.url})`).join("; ");
        console.log(
          `  - **[${v.severity.toUpperCase()}] \`${v.name}\`** (${kind}, vulnerable \`${v.range}\`, fix: ${fix})${titles ? `: ${titles}` : ""}`,
        );
      }
    }
  }
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
