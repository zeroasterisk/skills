#!/usr/bin/env python3
"""sync-adlc.py — Vendor an ADLC release from voodootikigod/adlc.

Copies a tagged release of https://github.com/voodootikigod/adlc.git into
plugins/adlc and writes an Agent Plugins v1.0.0 manifest. The plugin version
comes from the vendored package.json. CloudCode reads that same package.json to
install @adlc/opencode from npm, so the vendored skills and the runtime plugin
stay on one release.

Usage:
  python3 scripts/sync-adlc.py               # Vendor the latest vX.Y.Z tag
  python3 scripts/sync-adlc.py --ref v1.13.0 # Vendor a specific tag
  python3 scripts/sync-adlc.py --dry-run     # Print the tag that would be vendored
"""

from __future__ import annotations

import argparse
import json
import pathlib
import re
import shutil
import subprocess
import sys

UPSTREAM_REMOTE = "upstream-adlc"
UPSTREAM_URL = "https://github.com/voodootikigod/adlc.git"

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
PLUGINS_DIR = REPO_ROOT / "plugins"
ADLC_PLUGIN_DIR = PLUGINS_DIR / "adlc"


def log(msg: str) -> None:
    print(f"[sync-adlc] {msg}")


def ensure_remote(repo_root: pathlib.Path) -> None:
    remotes = subprocess.run(
        ["git", "remote"], cwd=repo_root, capture_output=True, text=True, check=True
    ).stdout.splitlines()
    if UPSTREAM_REMOTE not in remotes:
        log(f"Adding git remote '{UPSTREAM_REMOTE}' -> {UPSTREAM_URL}")
        subprocess.run(
            ["git", "remote", "add", UPSTREAM_REMOTE, UPSTREAM_URL],
            cwd=repo_root,
            check=True,
        )


def latest_release_tag(repo_root: pathlib.Path) -> str:
    out = subprocess.run(
        ["git", "ls-remote", "--tags", "--refs", UPSTREAM_REMOTE, "v*"],
        cwd=repo_root,
        capture_output=True,
        text=True,
        check=True,
    ).stdout
    tags = [line.rsplit("refs/tags/", 1)[1] for line in out.splitlines()]
    releases = [t for t in tags if re.fullmatch(r"v\d+\.\d+\.\d+", t)]
    if not releases:
        raise RuntimeError(f"No vX.Y.Z tags found on {UPSTREAM_REMOTE}")
    return max(releases, key=lambda t: tuple(int(n) for n in t[1:].split(".")))


def fetch_tag(repo_root: pathlib.Path, tag: str) -> str:
    # Keep upstream tags out of this repo's own refs/tags namespace.
    local_ref = f"refs/remotes/{UPSTREAM_REMOTE}/tags/{tag}"
    log(f"Fetching {tag} from {UPSTREAM_REMOTE}...")
    subprocess.run(
        ["git", "fetch", "--no-tags", UPSTREAM_REMOTE, f"+refs/tags/{tag}:{local_ref}"],
        cwd=repo_root,
        check=True,
    )
    return local_ref


def extract(repo_root: pathlib.Path, tree: str, dest: pathlib.Path) -> None:
    log(f"Extracting {tree} into {dest}...")
    dest.mkdir(parents=True, exist_ok=True)
    archive = subprocess.Popen(["git", "archive", tree], cwd=repo_root, stdout=subprocess.PIPE)
    tar = subprocess.run(["tar", "-x", "-C", str(dest)], stdin=archive.stdout)
    if archive.wait() != 0 or tar.returncode != 0:
        raise RuntimeError(f"Failed to extract {tree}")


def sync_adlc(repo_root: pathlib.Path, ref: str) -> None:
    # Start from an empty directory so files removed upstream do not linger.
    if ADLC_PLUGIN_DIR.exists():
        shutil.rmtree(ADLC_PLUGIN_DIR)

    extract(repo_root, f"{ref}:plugins/adlc-opencode", ADLC_PLUGIN_DIR)
    # Upstream gemini skills: adlc, adlc-doctrine, adlc-prosecutor, adlc-self-orchestrate
    extract(repo_root, f"{ref}:plugins/adlc-gemini/skills", ADLC_PLUGIN_DIR / "skills")

    with open(ADLC_PLUGIN_DIR / "package.json", encoding="utf-8") as f:
        version = json.load(f)["version"]
    manifest = {
        "$schema": "https://agent-plugins.org/schemas/1.0.0/plugin.schema.json",
        "name": "adlc",
        "version": version,
        "description": "Agentic Development Lifecycle (ADLC) toolkit integration: phase router, rail-guard hooks, slash commands, and prosecutor agents.",
        "author": {"name": "Chris Williams", "url": "https://github.com/voodootikigod"},
        "repository": "https://github.com/voodootikigod/adlc",
        "license": "MIT",
        "keywords": ["adlc", "agentic-lifecycle", "rails-guard", "gates", "prosecution"],
    }
    with open(ADLC_PLUGIN_DIR / "plugin.json", "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)
        f.write("\n")
    log(f"Wrote plugin.json (version {version})")

    # adlc >= 1.13.0 exports the OpenCode v2 shape ({id, setup}); CloudCode's loader
    # rejects it ("must default export an object with server()").
    if re.search(r"^export default \{", (ADLC_PLUGIN_DIR / "index.mjs").read_text(), re.M):
        log(f"WARNING: {ref} uses the OpenCode v2 plugin export; CloudCode cannot load it. "
            "Re-run with --ref v1.12.0 or pin @adlc/opencode to a v1 release.")

    for s in ADLC_PLUGIN_DIR.rglob("bin/*"):
        if s.is_file():
            s.chmod(0o755)


def main() -> int:
    parser = argparse.ArgumentParser(description="Vendor an ADLC release from voodootikigod/adlc")
    parser.add_argument("--ref", help="Release tag to vendor (default: latest vX.Y.Z tag)")
    parser.add_argument("--dry-run", action="store_true", help="Print the tag that would be vendored and exit")
    args = parser.parse_args()

    ensure_remote(REPO_ROOT)
    tag = args.ref or latest_release_tag(REPO_ROOT)
    if args.dry_run:
        log(f"[dry-run] Would vendor {tag} into {ADLC_PLUGIN_DIR}")
        return 0
    sync_adlc(REPO_ROOT, fetch_tag(REPO_ROOT, tag))
    log("Done.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
