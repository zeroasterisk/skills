#!/usr/bin/env node
/**
 * scan-remote-repos.mjs — Uses the GitHub CLI (`gh`) to find remote repositories
 * that are not cloned locally in <workspace> and check their git trees for package.json.
 *
 * Usage:
 *   ./scripts/scan-remote-repos.mjs [workspace_dir] [--all-languages]
 */

import { execFile } from "node:child_process";
import { access, readdir } from "node:fs/promises";
import { constants } from "node:fs";
import { join, resolve } from "node:path";
import { promisify } from "node:util";

const run = promisify(execFile);

async function exists(p) {
  try {
    await access(p, constants.F_OK);
    return true;
  } catch {
    return false;
  }
}

async function localClonedRepoNames(workspace) {
  const names = new Set();
  let entries = [];
  try {
    entries = await readdir(workspace, { withFileTypes: true });
  } catch {
    return names;
  }
  for (const e of entries) {
    if (!e.isDirectory()) continue;
    names.add(e.name);
    const dir = join(workspace, e.name);
    if (await exists(join(dir, ".git"))) {
      try {
        const { stdout } = await run("git", ["-C", dir, "remote", "get-url", "origin"]);
        const m = /[:/]([^/:]+\/[^/.]+?)(?:\.git)?$/.exec(stdout.trim());
        if (m) {
          names.add(m[1]);
          names.add(m[1].split("/")[1]);
        }
      } catch {
        // ignore
      }
    }
  }
  return names;
}

async function main() {
  const args = process.argv.slice(2);
  const allLangs = args.includes("--all-languages");
  const includeForks = args.includes("--include-forks");
  const workspaceArg = args.find((a) => !a.startsWith("--")) ?? join(process.env.HOME ?? ".", "projects");
  const workspace = resolve(workspaceArg);

  const { stdout } = await run("gh", [
    "repo",
    "list",
    "--limit",
    "200",
    "--json",
    "name,nameWithOwner,isArchived,isFork,pushedAt,primaryLanguage,defaultBranchRef",
  ]);
  const repos = JSON.parse(stdout).filter((r) => !r.isArchived && (includeForks || !r.isFork));

  const clonedNames = await localClonedRepoNames(workspace);
  const uncloned = [];
  for (const r of repos) {
    if (clonedNames.has(r.name) || clonedNames.has(r.nameWithOwner)) continue;
    uncloned.push(r);
  }

  // Filter to likely Node/web repos unless --all-languages is passed
  const nodeLangs = new Set(["TypeScript", "JavaScript", "HTML", "CSS", "Astro", "Vue", "Svelte"]);
  const candidates = allLangs
    ? uncloned
    : uncloned.filter((r) => nodeLangs.has(r.primaryLanguage?.name ?? "") || !r.primaryLanguage);

  console.log(
    `==> Checking ${candidates.length} uncloned remote repositories for package.json (out of ${uncloned.length} uncloned)...`,
  );

  const found = [];
  for (const r of candidates) {
    const branch = r.defaultBranchRef?.name ?? "main";
    try {
      const { stdout: treeOut } = await run("gh", [
        "api",
        `repos/${r.nameWithOwner}/git/trees/${branch}?recursive=1`,
        "--jq",
        '[.tree[] | select(.path == "package.json" or (.path | endswith("/package.json"))) | select(.path | contains("node_modules/") | not) | .path]',
      ]);
      const paths = JSON.parse(treeOut);
      if (paths.length > 0) {
        found.push({
          repo: r.name,
          nameWithOwner: r.nameWithOwner,
          lang: r.primaryLanguage?.name ?? "-",
          pushedAt: r.pushedAt,
          packageJsons: paths,
        });
      }
    } catch {
      // ignore empty repos or API errors
    }
  }

  console.log(`\nFound ${found.length} remote-only repositories containing package.json:\n`);
  console.log(`| Repository | Primary Lang | Last Pushed | \`package.json\` Paths |`);
  console.log(`| :--- | :--- | :--- | :--- |`);
  for (const f of found.sort((a, b) => b.pushedAt.localeCompare(a.pushedAt))) {
    console.log(
      `| \`${f.nameWithOwner}\` | ${f.lang} | ${f.pushedAt.slice(0, 10)} | ${f.packageJsons.map((p) => `\`${p}\``).join(", ")} |`,
    );
  }
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
