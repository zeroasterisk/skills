#!/usr/bin/env node
/**
 * audit-cobra-cli.mjs — Audits a Go Cobra CLI repository against the
 * Agent-Aware CLI (DX & AX) checklist:
 *  1. Three Pillars of Documentation (Short, Long, Example) & GroupID
 *  2. Machine-readable JSON output coverage (--output json / isJSONOutput)
 *  3. Environment overrides (NO_COLOR, *_NO_TUI)
 *  4. Data scoping & context-window protection (--limit, --status, dry-run)
 *
 * Usage:
 *   ./scripts/audit-cobra-cli.mjs <repo_path> [--json]
 */

import { access, readdir, readFile } from "node:fs/promises";
import { constants } from "node:fs";
import { join, relative, resolve } from "node:path";

async function exists(p) {
  try {
    await access(p, constants.F_OK);
    return true;
  } catch {
    return false;
  }
}

async function walkGoFiles(dir, maxDepth = 4, depth = 0) {
  if (depth > maxDepth) return [];
  let entries = [];
  try {
    entries = await readdir(dir, { withFileTypes: true });
  } catch {
    return [];
  }
  const files = [];
  for (const e of entries) {
    if (
      e.name === ".git" ||
      e.name === "vendor" ||
      e.name === "node_modules" ||
      e.name.startsWith(".")
    ) {
      continue;
    }
    const full = join(dir, e.name);
    if (e.isFile() && e.name.endsWith(".go") && !e.name.endsWith("_test.go")) {
      files.push(full);
    } else if (e.isDirectory()) {
      files.push(...(await walkGoFiles(full, maxDepth, depth + 1)));
    }
  }
  return files.sort();
}

function extractCobraCommands(source, relFile) {
  const commands = [];
  const cmdRegex = /(?:var\s+(\w+)\s*=|(\w+)\s*:=)\s*&cobra\.Command\s*\{/g;
  let match;
  while ((match = cmdRegex.exec(source)) !== null) {
    const varName = match[1] ?? match[2];
    const startIdx = match.index + match[0].length - 1;
    let depth = 0;
    let endIdx = startIdx;
    let inString = false;
    let quoteChar = "";
    for (let i = startIdx; i < source.length; i += 1) {
      const ch = source[i];
      const prev = source[i - 1];
      if (inString) {
        if (ch === quoteChar && prev !== "\\") {
          inString = false;
        }
        continue;
      }
      if (ch === '"' || ch === "`") {
        inString = true;
        quoteChar = ch;
        continue;
      }
      if (ch === "{") depth += 1;
      if (ch === "}") {
        depth -= 1;
        if (depth === 0) {
          endIdx = i + 1;
          break;
        }
      }
    }
    const block = source.slice(startIdx, endIdx);
    const useMatch = /\bUse\s*:\s*["`]([^"`]+)["`]/.exec(block);
    const useStr = useMatch ? useMatch[1] : varName;
    const cmdName = useStr.split(/\s+/)[0];
    const hasShort = /\bShort\s*:/.test(block);
    const hasLong = /\bLong\s*:/.test(block);
    const hasExample = /\bExample\s*:/.test(block);
    const hasGroupID = /\bGroupID\s*:/.test(block);
    const hasRun = /\bRunE?\s*:/.test(block);
    const checksJson =
      /\bisJSONOutput\b|\boutputFormat\b|\bwriteJSON\b|json\.NewEncoder|json\.Marshal/.test(
        block,
      );

    commands.push({
      varName,
      use: useStr,
      name: cmdName,
      file: relFile,
      hasShort,
      hasLong,
      hasExample,
      hasGroupID,
      hasRun,
      checksJson,
    });
  }
  return commands;
}

async function main() {
  const args = process.argv.slice(2);
  const jsonFlag = args.includes("--json");
  const targetArg = args.find((a) => !a.startsWith("--")) ?? process.cwd();
  const targetPath = resolve(targetArg);

  const cmdDir = (await exists(join(targetPath, "cmd")))
    ? join(targetPath, "cmd")
    : targetPath;
  const goFiles = await walkGoFiles(targetPath);
  const cmdFiles = await walkGoFiles(cmdDir);

  let allSource = "";
  for (const f of goFiles) {
    allSource += (await readFile(f, "utf8")) + "\n";
  }

  const commands = [];
  const rootAdditions = new Set();
  for (const f of cmdFiles) {
    const raw = await readFile(f, "utf8");
    const relFile = relative(targetPath, f);
    commands.push(...extractCobraCommands(raw, relFile));
    for (const m of raw.matchAll(/\brootCmd\.AddCommand\(\s*(\w+)\s*\)/g)) {
      rootAdditions.add(m[1]);
    }
  }

  const hasNoColor = /\bNO_COLOR\b/.test(allSource);
  const hasNoTui = /_NO_TUI\b/.test(allSource);
  const hasOutputFlag = /["']output["']/.test(allSource);
  const hasLimitFlag = /["']limit["']/.test(allSource);
  const hasDryRunFlag = /["']dry-run["']/.test(allSource);

  const annotated = commands.map((c) => ({
    ...c,
    isTopLevel: rootAdditions.has(c.varName),
  }));

  const leafCommands = annotated.filter((c) => c.hasRun && c.varName !== "rootCmd");
  const jsonReadyLeaves = leafCommands.filter((c) => c.checksJson);
  const topLevelMissingGroup = annotated.filter(
    (c) => c.isTopLevel && !c.hasGroupID,
  );
  const leavesMissingExample = leafCommands.filter((c) => !c.hasExample);

  const summary = {
    scannedAt: new Date().toISOString(),
    targetPath,
    commandCount: annotated.length,
    leafCommandCount: leafCommands.length,
    jsonReadyLeafCount: jsonReadyLeaves.length,
    signals: {
      hasOutputFlag,
      hasNoColor,
      hasNoTui,
      hasLimitFlag,
      hasDryRunFlag,
    },
    topLevelMissingGroup: topLevelMissingGroup.map((c) => `${c.name} (${c.file})`),
    leavesMissingExample: leavesMissingExample.map((c) => `${c.name} (${c.file})`),
    commands: annotated,
  };

  if (jsonFlag) {
    console.log(JSON.stringify(summary, null, 2));
    return;
  }

  console.log(`# Agent-Aware CLI Audit Report`);
  console.log(`- **Target**: \`${targetPath}\``);
  console.log(
    `- **Commands Discovered**: ${summary.commandCount} (${summary.leafCommandCount} executable leaf commands, ${summary.jsonReadyLeafCount}/${summary.leafCommandCount} with JSON output handling)`,
  );
  console.log(
    `- **AX Signals**: \`--output\`=${hasOutputFlag ? "OK" : "MISSING"}, \`NO_COLOR\`=${hasNoColor ? "OK" : "MISSING"}, \`*_NO_TUI\`=${hasNoTui ? "OK" : "MISSING"}, \`--limit\`=${hasLimitFlag ? "OK" : "MISSING"}, \`--dry-run\`=${hasDryRunFlag ? "OK" : "MISSING"}\n`,
  );

  console.log(
    `| Command | File | Top-Level | \`GroupID\` | \`Short\` | \`Long\` | \`Example\` | JSON Output |`,
  );
  console.log(`| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: |`);
  for (const c of annotated) {
    const grp = c.isTopLevel ? (c.hasGroupID ? "OK" : "MISSING") : "—";
    const ex = c.hasRun ? (c.hasExample ? "OK" : "MISSING") : c.hasExample ? "OK" : "—";
    const js = c.hasRun ? (c.checksJson ? "OK" : "TEXT-ONLY") : "—";
    console.log(
      `| \`${c.use}\` | \`${c.file}\` | ${c.isTopLevel ? "yes" : "no"} | ${grp} | ${c.hasShort ? "OK" : "MISSING"} | ${c.hasLong ? "OK" : "MISSING"} | ${ex} | ${js} |`,
    );
  }
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
