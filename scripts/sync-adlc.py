#!/usr/bin/env python3
"""sync-adlc.py — Vendor an ADLC release from voodootikigod/adlc.

Copies a tagged release of https://github.com/voodootikigod/adlc.git into
plugins/adlc and writes an Agent Plugins v1.0.0 manifest. The plugin version
comes from the vendored package.json. Keep the CloudCode plugin entry
(@adlc/opencode@<version>) on that same version, so the vendored skills and the
runtime plugin match.

Usage:
  python3 scripts/sync-adlc.py               # Vendor the newest release CloudCode can load
  python3 scripts/sync-adlc.py --ref v1.12.0 # Vendor a specific tag
  python3 scripts/sync-adlc.py --dry-run     # Fetch and check tags; leave plugins/adlc alone

adlc >= 1.13.0 exports the OpenCode v2 plugin shape ({id, setup}), which
CloudCode cannot load. Without --ref, the script picks the newest release with
the v1 export. With --ref, it refuses a v2 tag before it touches plugins/adlc,
unless --allow-v2 is given.
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
V2_EXPORT = re.compile(r"^export default \{", re.MULTILINE)


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


def release_tags(repo_root: pathlib.Path) -> list[str]:
    """Upstream vX.Y.Z tags, newest first."""
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
    return sorted(releases, key=lambda t: tuple(int(n) for n in t[1:].split(".")), reverse=True)


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
    tar = subprocess.Popen(["tar", "-x", "-C", str(dest)], stdin=archive.stdout)
    archive.stdout.close()  # let git archive get SIGPIPE if tar exits early
    if tar.wait() != 0 or archive.wait() != 0:
        raise RuntimeError(f"Failed to extract {tree}")


def uses_v2_export(repo_root: pathlib.Path, ref: str) -> bool:
    index = subprocess.run(
        ["git", "show", f"{ref}:plugins/adlc-opencode/index.mjs"],
        cwd=repo_root,
        capture_output=True,
        text=True,
        check=True,
    ).stdout
    return V2_EXPORT.search(index) is not None


def sync_adlc(repo_root: pathlib.Path, ref: str) -> None:
    # Start from an empty directory so files removed upstream do not linger.
    if ADLC_PLUGIN_DIR.exists():
        shutil.rmtree(ADLC_PLUGIN_DIR)

    extract(repo_root, f"{ref}:plugins/adlc-opencode", ADLC_PLUGIN_DIR)
    # Upstream's tests need its npm workspace and cannot run from the vendored copy.
    shutil.rmtree(ADLC_PLUGIN_DIR / "test", ignore_errors=True)
    # Skills and the prosecutor subagents they invoke, as upstream ships them for Gemini harnesses.
    # adlc-gemini/commands is left out: it calls scripts under plugins/adlc-gemini/ that are not vendored.
    for part in ("skills", "agents"):
        extract(repo_root, f"{ref}:plugins/adlc-gemini/{part}", ADLC_PLUGIN_DIR / part)

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

    for s in ADLC_PLUGIN_DIR.rglob("bin/*"):
        if s.is_file():
            s.chmod(0o755)


def main() -> int:
    parser = argparse.ArgumentParser(description="Vendor an ADLC release from voodootikigod/adlc")
    parser.add_argument("--ref", help="Release tag to vendor (default: newest release with the v1 export)")
    parser.add_argument(
        "--allow-v2", action="store_true", help="Vendor a tag even if it uses the OpenCode v2 plugin export"
    )
    parser.add_argument("--dry-run", action="store_true", help="Fetch and check tags, print the one that would be vendored, change nothing in plugins/")
    args = parser.parse_args()

    ensure_remote(REPO_ROOT)
    candidates = [args.ref] if args.ref else release_tags(REPO_ROOT)
    for tag in candidates:
        ref = fetch_tag(REPO_ROOT, tag)
        if args.allow_v2 or not uses_v2_export(REPO_ROOT, ref):
            break
        if args.ref:
            log(f"ERROR: {tag} uses the OpenCode v2 plugin export, which CloudCode cannot load.")
            log("plugins/adlc is unchanged. Pass --ref with a v1 release (e.g. v1.12.0), or --allow-v2.")
            return 1
        log(f"Skipping {tag}: OpenCode v2 plugin export, which CloudCode cannot load.")
    else:
        log("ERROR: no upstream release uses the v1 plugin export.")
        return 1
    if args.dry_run:
        log(f"[dry-run] Would vendor {tag} into {ADLC_PLUGIN_DIR}")
        return 0
    sync_adlc(REPO_ROOT, ref)
    log("Done.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
