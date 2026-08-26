#!/usr/bin/env python3
"""sync-upstream-plugins.py — Sync upstream plugins from ghchinoy/agent-skills.

Fetches the latest plugins from Hussain Chinoy's agent-skills repository,
updates the local vendored plugins, refreshes .claude-plugin/marketplace.json,
ensures script executable bits, and verifies conformance with validate-plugins.sh.

Usage:
  python3 scripts/sync-upstream-plugins.py            # Sync, update marketplace, validate
  python3 scripts/sync-upstream-plugins.py --dry-run  # Preview changes without modifying files
  python3 scripts/sync-upstream-plugins.py --no-fetch # Use existing local remote refs without network fetch
"""

from __future__ import annotations

import argparse
import json
import os
import pathlib
import subprocess
import sys

UPSTREAM_REMOTE = "upstream-ghchinoy"
UPSTREAM_URL = "https://github.com/ghchinoy/agent-skills.git"
UPSTREAM_BRANCH = "main"

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
PLUGINS_DIR = REPO_ROOT / "plugins"
MARKETPLACE_FILE = REPO_ROOT / ".claude-plugin" / "marketplace.json"
VALIDATE_SCRIPT = REPO_ROOT / "scripts" / "validate-plugins.sh"


def log(msg: str) -> None:
    print(f"[sync-upstream] {msg}")


def ensure_remote(repo_root: pathlib.Path) -> None:
    remotes = subprocess.run(
        ["git", "remote"],
        cwd=repo_root,
        capture_output=True,
        text=True,
        check=True
    ).stdout.splitlines()
    if UPSTREAM_REMOTE not in remotes:
        log(f"Adding git remote '{UPSTREAM_REMOTE}' -> {UPSTREAM_URL}")
        subprocess.run(
            ["git", "remote", "add", UPSTREAM_REMOTE, UPSTREAM_URL],
            cwd=repo_root,
            check=True
        )


def fetch_upstream(repo_root: pathlib.Path) -> None:
    log(f"Fetching updates from {UPSTREAM_REMOTE}/{UPSTREAM_BRANCH}...")
    subprocess.run(
        ["git", "fetch", UPSTREAM_REMOTE, UPSTREAM_BRANCH],
        cwd=repo_root,
        check=True
    )


def list_upstream_plugins(repo_root: pathlib.Path) -> list[str]:
    res = subprocess.run(
        ["git", "ls-tree", f"{UPSTREAM_REMOTE}/{UPSTREAM_BRANCH}:plugins"],
        cwd=repo_root,
        capture_output=True,
        text=True,
        check=True
    )
    plugins = []
    for line in res.stdout.splitlines():
        # format: <mode> <type> <object> <file>
        parts = line.split()
        if len(parts) >= 4 and parts[1] == "tree":
            plugins.append(parts[3])
    return sorted(plugins)


def sync_plugin(repo_root: pathlib.Path, plugin_name: str, dry_run: bool = False) -> bool:
    dest = PLUGINS_DIR / plugin_name
    tree_ref = f"{UPSTREAM_REMOTE}/{UPSTREAM_BRANCH}:plugins/{plugin_name}"

    # Check diff if dest exists
    if dest.exists():
        diff_res = subprocess.run(
            ["git", "diff", "--quiet", tree_ref, "--", str(dest.relative_to(repo_root))],
            cwd=repo_root
        )
        if diff_res.returncode == 0:
            log(f"Plugin '{plugin_name}' is already up-to-date.")
            return False

    if dry_run:
        log(f"[dry-run] Would update plugin '{plugin_name}' from {tree_ref}")
        return True

    log(f"Updating plugin '{plugin_name}' from {tree_ref}...")
    dest.mkdir(parents=True, exist_ok=True)
    
    # Extract git archive of tree_ref directly into dest
    archive_proc = subprocess.Popen(
        ["git", "archive", tree_ref],
        cwd=repo_root,
        stdout=subprocess.PIPE
    )
    tar_proc = subprocess.Popen(
        ["tar", "-x", "-C", str(dest)],
        cwd=repo_root,
        stdin=archive_proc.stdout
    )
    if archive_proc.stdout:
        archive_proc.stdout.close()
    tar_proc.communicate()
    if tar_proc.returncode != 0:
        raise RuntimeError(f"Failed to extract plugin '{plugin_name}' archive")

    # Ensure executable permissions on all scripts
    scripts_dir = dest / "skills"
    if scripts_dir.exists():
        for s in scripts_dir.rglob("scripts/*"):
            if s.is_file():
                s.chmod(0o755)

    return True


def regenerate_marketplace(repo_root: pathlib.Path, dry_run: bool = False) -> None:
    plugins_list = []
    for p_dir in sorted(PLUGINS_DIR.iterdir()):
        if not p_dir.is_dir():
            continue
        manifest_file = p_dir / "plugin.json"
        if not manifest_file.exists():
            continue

        with open(manifest_file, "r", encoding="utf-8") as f:
            m_data = json.load(f)

        skills_dir = p_dir / "skills"
        skill_paths = []
        if skills_dir.exists():
            for s in sorted(skills_dir.iterdir()):
                if s.is_dir() and (s / "SKILL.md").exists():
                    skill_paths.append(f"./plugins/{p_dir.name}/skills/{s.name}")

        plugins_list.append({
            "name": m_data.get("name", p_dir.name),
            "source": f"./plugins/{p_dir.name}",
            "description": m_data.get("description", ""),
            "skills": skill_paths
        })

    marketplace = {
        "name": "skills",
        "metadata": {
            "pluginRoot": "./plugins"
        },
        "plugins": plugins_list
    }

    if dry_run:
        log(f"[dry-run] Would write marketplace manifest with {len(plugins_list)} plugins")
        return

    MARKETPLACE_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(MARKETPLACE_FILE, "w", encoding="utf-8") as f:
        json.dump(marketplace, f, indent=2)
        f.write("\n")
    log(f"Updated {MARKETPLACE_FILE} with {len(plugins_list)} plugins and {sum(len(p['skills']) for p in plugins_list)} skills.")


def main() -> int:
    parser = argparse.ArgumentParser(description="Sync plugins from ghchinoy/agent-skills")
    parser.add_argument("--dry-run", action="store_true", help="Preview changes without modifying files")
    parser.add_argument("--no-fetch", action="store_true", help="Skip fetching remote git refs")
    parser.add_argument("--no-validate", action="store_true", help="Skip running validate-plugins.sh")
    args = parser.parse_args()

    ensure_remote(REPO_ROOT)
    if not args.no_fetch:
        fetch_upstream(REPO_ROOT)

    upstream_plugins = list_upstream_plugins(REPO_ROOT)
    log(f"Discovered {len(upstream_plugins)} upstream plugins in {UPSTREAM_REMOTE}/{UPSTREAM_BRANCH}")

    updated_count = 0
    for plugin in upstream_plugins:
        if sync_plugin(REPO_ROOT, plugin, dry_run=args.dry_run):
            updated_count += 1

    regenerate_marketplace(REPO_ROOT, dry_run=args.dry_run)

    if not args.dry_run and not args.no_validate and VALIDATE_SCRIPT.exists():
        log("Running validate-plugins.sh...")
        res = subprocess.run([str(VALIDATE_SCRIPT)], cwd=REPO_ROOT)
        if res.returncode != 0:
            log("Validation failed!")
            return res.returncode

    log(f"Sync complete. {updated_count} plugin(s) updated or added.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
