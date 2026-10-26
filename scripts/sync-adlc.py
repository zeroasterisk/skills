#!/usr/bin/env python3
"""sync-adlc.py — Sync upstream ADLC plugins and skills from voodootikigod/adlc.

Fetches the latest release/branch from https://github.com/voodootikigod/adlc.git,
vendors plugins/adlc into this repository with Agent Plugins v1.0.0 and OpenCode
compatibility, and prepares it for sync.py.

Usage:
  python3 scripts/sync-adlc.py            # Sync, update plugins/adlc
  python3 scripts/sync-adlc.py --dry-run  # Preview changes without modifying files
  python3 scripts/sync-adlc.py --no-fetch # Use existing local remote refs without network fetch
"""

from __future__ import annotations

import argparse
import json
import os
import pathlib
import subprocess
import sys

UPSTREAM_REMOTE = "upstream-adlc"
UPSTREAM_URL = "https://github.com/voodootikigod/adlc.git"
UPSTREAM_BRANCH = "main"

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
PLUGINS_DIR = REPO_ROOT / "plugins"
ADLC_PLUGIN_DIR = PLUGINS_DIR / "adlc"


def log(msg: str) -> None:
    print(f"[sync-adlc] {msg}")


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


def sync_adlc(repo_root: pathlib.Path, dry_run: bool = False) -> None:
    if dry_run:
        log(f"[dry-run] Would sync adlc files into {ADLC_PLUGIN_DIR}")
        return

    ADLC_PLUGIN_DIR.mkdir(parents=True, exist_ok=True)

    # 1. Extract opencode plugin tree
    opencode_tree = f"{UPSTREAM_REMOTE}/{UPSTREAM_BRANCH}:plugins/adlc-opencode"
    log(f"Extracting {opencode_tree} into {ADLC_PLUGIN_DIR}...")
    archive_proc = subprocess.Popen(
        ["git", "archive", opencode_tree],
        cwd=repo_root,
        stdout=subprocess.PIPE
    )
    tar_proc = subprocess.Popen(
        ["tar", "-x", "-C", str(ADLC_PLUGIN_DIR)],
        cwd=repo_root,
        stdin=archive_proc.stdout
    )
    if archive_proc.stdout:
        archive_proc.stdout.close()
    tar_proc.communicate()
    if tar_proc.returncode != 0:
        raise RuntimeError("Failed to extract plugins/adlc-opencode")

    # 2. Extract gemini skills into skills/ directory
    # Upstream gemini has skills: adlc, adlc-doctrine, adlc-prosecutor, adlc-self-orchestrate
    skills_dest = ADLC_PLUGIN_DIR / "skills"
    skills_dest.mkdir(parents=True, exist_ok=True)
    gemini_skills_tree = f"{UPSTREAM_REMOTE}/{UPSTREAM_BRANCH}:plugins/adlc-gemini/skills"
    log(f"Extracting {gemini_skills_tree} into {skills_dest}...")
    archive_proc = subprocess.Popen(
        ["git", "archive", gemini_skills_tree],
        cwd=repo_root,
        stdout=subprocess.PIPE
    )
    tar_proc = subprocess.Popen(
        ["tar", "-x", "-C", str(skills_dest)],
        cwd=repo_root,
        stdin=archive_proc.stdout
    )
    if archive_proc.stdout:
        archive_proc.stdout.close()
    tar_proc.communicate()
    if tar_proc.returncode != 0:
        raise RuntimeError("Failed to extract plugins/adlc-gemini/skills")

    # 3. Write a compliant Agent Plugin v1.0.0 plugin.json
    manifest_file = ADLC_PLUGIN_DIR / "plugin.json"
    manifest = {
        "$schema": "https://agent-plugins.org/schemas/1.0.0/plugin.schema.json",
        "name": "adlc",
        "version": "1.11.0",
        "description": "Agentic Development Lifecycle (ADLC) toolkit integration: phase router, rail-guard hooks, slash commands, and prosecutor agents.",
        "author": {
            "name": "Chris Williams",
            "url": "https://github.com/voodootikigod"
        },
        "repository": "https://github.com/voodootikigod/adlc",
        "license": "MIT",
        "keywords": [
            "adlc",
            "agentic-lifecycle",
            "rails-guard",
            "gates",
            "prosecution"
        ]
    }
    with open(manifest_file, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)
        f.write("\n")
    log("Wrote Agent Plugins v1.0.0 plugin.json")

    # 4. Make all scripts executable if any
    for s in ADLC_PLUGIN_DIR.rglob("bin/*"):
        if s.is_file():
            s.chmod(0o755)

    log("ADLC synchronization complete.")


def main() -> int:
    parser = argparse.ArgumentParser(description="Sync ADLC plugin and skills from voodootikigod/adlc")
    parser.add_argument("--dry-run", action="store_true", help="Preview changes without modifying files")
    parser.add_argument("--no-fetch", action="store_true", help="Skip fetching remote git refs")
    args = parser.parse_args()

    ensure_remote(REPO_ROOT)
    if not args.no_fetch:
        fetch_upstream(REPO_ROOT)

    sync_adlc(REPO_ROOT, dry_run=args.dry_run)
    return 0


if __name__ == "__main__":
    sys.exit(main())
