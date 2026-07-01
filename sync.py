#!/usr/bin/env python3
"""sync.py — federated skills registry sync.

Reads registry.toml and:
  1. Auto-discovers skills (dirs containing SKILL.md) under each [[source]]
     path, scoped by include/exclude globs. Missing source paths are skipped
     silently so one registry works across machines.
  2. Updates cloudcode.json skills.paths for cloudcode-agent skills.
  3. Creates/cleans symlinks in ~/.gemini/config/skills/ for gemini-agent
     skills that ship a GEMINI.md.
  4. Emits ARD-compliant ai-catalog.json (specVersion 1.0) per source bundle
     plus a root aggregate. See https://agenticresourcediscovery.org/

Usage:
  ./sync.py               # normal sync
  ./sync.py --dry-run     # print what would happen, change nothing
  ./sync.py --verbose     # print all actions including skips

Stdlib only (tomllib, json, pathlib). No pyyaml, no jq.
"""

from __future__ import annotations

import argparse
import fnmatch
import json
import re
import subprocess
import sys
import tomllib
from pathlib import Path

REGISTRY_DIR = Path(__file__).resolve().parent
REGISTRY_FILE = REGISTRY_DIR / "registry.toml"
CATALOG_FILE = REGISTRY_DIR / "ai-catalog.json"

# Defaults; override in registry.toml [targets]
DEFAULT_TARGETS = {
    "cloudcode_config": "~/dotfiles/config/cloudcode/cloudcode.json",
    "gemini_skills_dir": "~/.gemini/config/skills",
}
CLOUDCODE_CONFIG = Path()  # set in main() from [targets]
GEMINI_SKILLS_DIR = Path()  # set in main() from [targets]

ARD_SPEC_VERSION = "1.0"
SKILL_MEDIA_TYPE = "application/ai-skill+md"

DRY_RUN = False
VERBOSE = False


def log(msg: str) -> None:
    print(f"[sync] {msg}")


def verbose(msg: str) -> None:
    if VERBOSE:
        print(f"[sync] {msg}")


def dry(msg: str) -> None:
    print(f"[dry-run] {msg}")


# ---------------------------------------------------------------------------
# SKILL.md frontmatter (handles plain scalars and folded `>-` blocks)
# ---------------------------------------------------------------------------

def parse_frontmatter(skill_md: Path) -> dict[str, str]:
    try:
        text = skill_md.read_text(encoding="utf-8")
    except OSError:
        return {}
    m = re.match(r"\A---\n(.*?)\n---", text, re.DOTALL)
    if not m:
        return {}
    fm: dict[str, str] = {}
    key = None
    folded = False
    buf: list[str] = []

    def flush() -> None:
        nonlocal key, buf
        if key is not None and buf:
            fm[key] = " ".join(s.strip() for s in buf if s.strip())
        key, buf[:] = None, []

    for line in m.group(1).splitlines():
        top = re.match(r"^([A-Za-z_][\w-]*):\s*(.*)$", line)
        if top and not line.startswith((" ", "\t")):
            flush()
            key, val = top.group(1), top.group(2).strip()
            folded = val in (">", ">-", "|", "|-")
            if not folded and val:
                fm[key] = val.strip("'\"")
                key = None
        elif key is not None and folded:
            buf.append(line)
    flush()
    return fm


# ---------------------------------------------------------------------------
# Discovery
# ---------------------------------------------------------------------------

def matches(rel: str, patterns: list[str]) -> bool:
    """fnmatch against the pattern, the pattern as a dir prefix, and parents."""
    for pat in patterns:
        if fnmatch.fnmatch(rel, pat) or fnmatch.fnmatch(rel, pat.rstrip("/") + "/*"):
            return True
        if rel == pat.rstrip("/"):
            return True
    return False


def clone_missing(source: dict) -> None:
    """Clone a source repo if declared with `repo` + `clone_to` but absent."""
    clone_to = source.get("clone_to")
    repo = source.get("repo")
    if not clone_to or not repo:
        return
    dest = REGISTRY_DIR / clone_to
    if dest.exists():
        verbose(f"clone: already present: {dest}")
        return
    if DRY_RUN:
        dry(f"would clone {repo} -> {dest}")
        return
    log(f"cloning {repo} -> {dest}")
    subprocess.run(["git", "clone", "--depth", "1", repo, str(dest)], check=True)


def discover(source: dict, overrides: dict) -> list[dict]:
    root = (REGISTRY_DIR / source["path"]).resolve()
    if not root.is_dir():
        verbose(f"skip source (path missing on this machine): {source['name']} @ {root}")
        return []

    include = source.get("include", ["**"])
    exclude = source.get("exclude", [])
    skills: list[dict] = []

    for skill_md in sorted(root.rglob("SKILL.md")):
        skill_dir = skill_md.parent
        rel = skill_dir.relative_to(root).as_posix()
        if rel == ".":
            continue
        if matches(rel, exclude):
            verbose(f"skip (excluded): {source['name']}/{rel}")
            continue
        if include != ["**"] and not matches(rel, include):
            verbose(f"skip (not included): {source['name']}/{rel}")
            continue

        fm = parse_frontmatter(skill_md)
        name = fm.get("name") or skill_dir.name
        over = overrides.get(name, {}) | overrides.get(skill_dir.name, {})
        if over.get("active") is False:
            verbose(f"skip (inactive): {name}")
            continue

        skills.append({
            "name": name,
            "dir_name": skill_dir.name,
            "description": fm.get("description", ""),
            "path": skill_dir,
            "rel": rel,
            "source": source,
            "agents": over.get("agents", source.get("agents", ["cloudcode"])),
            "tags": over.get("tags", []),
            "audience": source.get("audience", "personal"),
        })
        log(f"resolved: {source['name']}/{rel}")
    return skills


# ---------------------------------------------------------------------------
# CloudCode config
# ---------------------------------------------------------------------------

def sync_cloudcode(skills: list[dict]) -> None:
    paths = [str(s["path"]) for s in skills if "cloudcode" in s["agents"]]
    if not CLOUDCODE_CONFIG.is_file():
        log(f"cloudcode: config not found at {CLOUDCODE_CONFIG}, skipping")
        return
    config = json.loads(CLOUDCODE_CONFIG.read_text())
    config.setdefault("skills", {})["paths"] = paths
    if DRY_RUN:
        dry(f"would write cloudcode.json skills.paths ({len(paths)} paths)")
        for p in paths:
            dry(f"  {p}")
    else:
        CLOUDCODE_CONFIG.write_text(json.dumps(config, indent=2) + "\n")
        log(f"cloudcode: updated skills.paths ({len(paths)} path(s))")


# ---------------------------------------------------------------------------
# Gemini symlinks
# ---------------------------------------------------------------------------

def sync_gemini(skills: list[dict]) -> None:
    if DRY_RUN:
        dry(f"would ensure dir: {GEMINI_SKILLS_DIR}")
    else:
        GEMINI_SKILLS_DIR.mkdir(parents=True, exist_ok=True)

    wanted = {
        s["dir_name"]: s["path"]
        for s in skills
        if "gemini" in s["agents"] and (s["path"] / "GEMINI.md").is_file()
    }

    if GEMINI_SKILLS_DIR.is_dir():
        for link in GEMINI_SKILLS_DIR.iterdir():
            if not link.is_symlink():
                continue
            target = link.resolve()
            if not str(target).startswith(str(REGISTRY_DIR)):
                verbose(f"gemini: skip unmanaged entry: {link.name}")
                continue
            if link.name not in wanted or not target.is_dir():
                if DRY_RUN:
                    dry(f"would remove stale symlink: {link.name}")
                else:
                    link.unlink()
                    log(f"gemini: removed stale symlink: {link.name}")

    for name, path in wanted.items():
        link = GEMINI_SKILLS_DIR / name
        if DRY_RUN:
            dry(f"would symlink: {link} -> {path}")
            continue
        if link.is_symlink() or link.exists():
            link.unlink()
        link.symlink_to(path)
        log(f"gemini: linked {name}")

    skipped = [s["dir_name"] for s in skills
               if "gemini" in s["agents"] and s["dir_name"] not in wanted]
    for name in skipped:
        verbose(f"gemini: skip {name} (no GEMINI.md)")


# ---------------------------------------------------------------------------
# ARD ai-catalog.json
# ---------------------------------------------------------------------------

def safe_urn_part(text: str) -> str:
    return re.sub(r"[^a-zA-Z0-9._-]", "-", text)


def catalog_entry(s: dict) -> dict:
    src = s["source"]
    urn = ":".join([
        "urn", "air",
        safe_urn_part(src.get("publisher", "local")),
        safe_urn_part(src.get("namespace", src["name"])),
        safe_urn_part(s["dir_name"]),
    ])
    entry = {
        "identifier": urn,
        "displayName": s["name"],
        "type": SKILL_MEDIA_TYPE,
        "description": s["description"],
        "tags": s["tags"],
        "metadata": {
            "source": src["name"],
            "audience": s["audience"],
            "agents": ",".join(s["agents"]),
            "relativePath": s["rel"],
        },
    }
    if src.get("url_base"):
        entry["url"] = f"{src['url_base'].rstrip('/')}/{s['rel']}"
    return entry


def make_catalog(host: dict, entries: list[dict]) -> dict:
    # NOTE: no extra root keys — the ai-catalog schema sets
    # additionalProperties: false at the root.
    return {
        "specVersion": ARD_SPEC_VERSION,
        "host": host,
        "entries": entries,
    }


def write_catalogs(host: dict, skills: list[dict]) -> None:
    by_source: dict[str, list[dict]] = {}
    for s in skills:
        by_source.setdefault(s["source"]["name"], []).append(s)

    all_entries: list[dict] = []
    for source_name, group in by_source.items():
        entries = [catalog_entry(s) for s in group]
        all_entries.extend(entries)

        # Always write per-source catalogs next to the registry — never
        # inside an external clone (that would dirty its working tree).
        slug = safe_urn_part(source_name.replace("/", "-"))
        out = REGISTRY_DIR / f"ai-catalog.{slug}.json"

        catalog = make_catalog(host, entries)
        if DRY_RUN:
            dry(f"would write bundle catalog: {out} ({len(entries)} skills)")
        else:
            out.write_text(json.dumps(catalog, indent=2) + "\n")
            log(f"catalog: wrote {out} ({len(entries)} skill(s))")

    aggregate = make_catalog(host, all_entries)
    if DRY_RUN:
        dry(f"would write aggregate catalog: {CATALOG_FILE} ({len(all_entries)} total)")
        print(json.dumps(aggregate, indent=2))
    else:
        CATALOG_FILE.write_text(json.dumps(aggregate, indent=2) + "\n")
        log(f"catalog: wrote aggregate {CATALOG_FILE} ({len(all_entries)} total)")


# ---------------------------------------------------------------------------

def main() -> int:
    global DRY_RUN, VERBOSE, CLOUDCODE_CONFIG, GEMINI_SKILLS_DIR
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--verbose", action="store_true")
    ap.add_argument("--clone-missing", action="store_true",
                    help="git clone any [[source]] with repo+clone_to that is absent")
    args = ap.parse_args()
    DRY_RUN, VERBOSE = args.dry_run, args.verbose

    if not REGISTRY_FILE.is_file():
        log(f"ERROR: {REGISTRY_FILE} not found")
        return 1
    registry = tomllib.loads(REGISTRY_FILE.read_text())

    targets = DEFAULT_TARGETS | registry.get("targets", {})
    CLOUDCODE_CONFIG = Path(targets["cloudcode_config"]).expanduser()
    GEMINI_SKILLS_DIR = Path(targets["gemini_skills_dir"]).expanduser()

    host = registry.get("host", {"displayName": "Skills Registry"})
    overrides = registry.get("skill", {})

    skills: list[dict] = []
    for source in registry.get("source", []):
        if args.clone_missing:
            clone_missing(source)
        skills.extend(discover(source, overrides))

    log(f"{len(skills)} skill(s) resolved on this machine")

    sync_cloudcode(skills)
    sync_gemini(skills)
    write_catalogs(host, skills)

    log("done")
    return 0


if __name__ == "__main__":
    sys.exit(main())
