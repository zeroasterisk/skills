#!/usr/bin/env python3
"""sync.py — federated 3-tier skills registry sync.

Reads registry.toml (plus optional machine-local ~/.config/skills-sync/local.toml)
and synchronizes three strictly isolated skill tiers without mixing them:
  1. "zeroasterisk" — Public OSS personal & vendored plugins (github.com/zeroasterisk/skills)
  2. "opm"          — Shared team skills (configured in local.toml)
  3. "work"         — Personal work skills (configured in local.toml)

Agent routing (configured in [agents.<name>] or overridden via --agents / --tiers):
  - jetski     : subscribes to all 3 ("zeroasterisk", "opm", "work"). Links plugins
                 into ~/.gemini/config/plugins/, avoids duplicate plugin skill symlinks
                 in ~/.gemini/config/skills/, and skips "work" symlinks once present at
                 native_piper_skills_dir (when auto-mounted natively).
  - cloudcode  : subscribes to 2 ("zeroasterisk", "opm") via cloudcode.json skills.paths.
  - gemini-cli : opt-in symlink dir (~/.gemini/skills), default ("zeroasterisk", "opm").
  - claude     : opt-in symlink dir (~/.claude/skills), default ("zeroasterisk").
  - codex      : opt-in symlink dir (~/.codex/skills), default ("zeroasterisk").

Catalog isolation:
  - Repo-tracked ai-catalog.json and ai-catalog.<slug>.json include ONLY "zeroasterisk"
    public sources — zero internal URLs or corp/OPM skills ever enter the git repo.
  - Non-public ("opm", "work") and machine-wide federated ARD catalogs are written to
    ~/.config/skills-sync/.

Usage:
  ./sync.py                                       # sync enabled agents & catalogs
  ./sync.py --list-tiers                          # inspect tiers, counts & agent routing
  ./sync.py --dry-run                             # preview all actions without changes
  ./sync.py --agents claude                       # one-shot sync for an opt-in agent
  ./sync.py --agents claude --tiers zeroasterisk,opm

Stdlib only (tomllib, json, os, pathlib). No pyyaml, no jq.
"""

from __future__ import annotations

import argparse
import fnmatch
import json
import os
import re
import subprocess
import sys
import tomllib
from pathlib import Path

REGISTRY_DIR = Path(__file__).resolve().parent
REGISTRY_FILE = REGISTRY_DIR / "registry.toml"
PUBLIC_CATALOG_FILE = REGISTRY_DIR / "ai-catalog.json"
PUBLIC_TIER = "zeroasterisk"
KNOWN_TIERS = ("zeroasterisk", "opm", "work")

CLOUDCODE_CANDIDATES = [
    "~/dotfiles/config/cloudcode/cloudcode.json",
    "~/.config/cloudcode/cloudcode.json",
]
DEFAULT_TARGETS = {
    "cloudcode_config": "",
    "gemini_skills_dir": "~/.gemini/config/skills",
    "gemini_plugins_dir": "~/.gemini/config/plugins",
    "local_catalog_dir": "~/.config/skills-sync",
}

ARD_SPEC_VERSION = "1.0"
SKILL_MEDIA_TYPE = "application/ai-skill+md"

DRY_RUN = False
VERBOSE = False

MANAGED_WORKSPACE_ROOTS: list[str] = [
    str(REGISTRY_DIR),
    str(Path("~/Workspaces/skills").expanduser()),
]


def register_managed_roots(sources: list[dict], agents_cfg: dict[str, dict]) -> None:
    """Derive managed symlink prefixes dynamically from configured sources and agents."""
    seen = set(MANAGED_WORKSPACE_ROOTS)
    raw_paths: list[str] = []
    for src in sources:
        if src.get("path"):
            raw_paths.append(src["path"])
        raw_paths.extend(src.get("fallback_paths", []))
    for cfg in agents_cfg.values():
        if cfg.get("native_piper_skills_dir"):
            raw_paths.append(cfg["native_piper_skills_dir"])

    for raw in raw_paths:
        norm = str(norm_path(raw))
        for candidate in (norm, str(Path(norm).parent) if norm.endswith("/skills") else norm):
            if candidate not in seen:
                seen.add(candidate)
                MANAGED_WORKSPACE_ROOTS.append(candidate)


def log(msg: str) -> None:
    print(f"[sync] {msg}")


def verbose(msg: str) -> None:
    if VERBOSE:
        print(f"[sync] {msg}")


def dry(msg: str) -> None:
    print(f"[dry-run] {msg}")


def norm_path(raw: str | Path, base: Path = REGISTRY_DIR) -> Path:
    """Normalize path without dereferencing dynamic head/version symlinks."""
    expanded = Path(raw).expanduser()
    if expanded.is_absolute():
        return Path(os.path.abspath(str(expanded)))
    return Path(os.path.abspath(str(base / expanded)))


def find_cloudcode_config(configured: str) -> Path | None:
    if configured:
        return Path(configured).expanduser()
    for candidate in CLOUDCODE_CANDIDATES:
        p = Path(candidate).expanduser()
        if p.is_file():
            return p
    return None


def is_managed_link(link: Path, extra_roots: list[str] | None = None) -> bool:
    """Return True if a symlink points into one of our managed skill/plugin roots."""
    roots = MANAGED_WORKSPACE_ROOTS + (extra_roots or [])
    candidates: list[str] = []
    try:
        raw_target = os.readlink(link)
        if not os.path.isabs(raw_target):
            raw_target = os.path.abspath(str(link.parent / raw_target))
        candidates.append(raw_target)
    except OSError:
        pass
    try:
        candidates.append(str(link.resolve()))
    except OSError:
        pass
    return any(c.startswith(root) for c in candidates for root in roots)


# ---------------------------------------------------------------------------
# SKILL.md frontmatter (handles plain scalars and folded/literal blocks)
# ---------------------------------------------------------------------------

def parse_frontmatter(skill_md: Path) -> dict[str, str]:
    try:
        text = skill_md.read_text(encoding="utf-8")
    except OSError:
        return {}
    if text.startswith("\ufeff"):
        text = text[1:]
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
# Local overlay merging & Discovery
# ---------------------------------------------------------------------------

def load_registry() -> dict:
    registry = tomllib.loads(REGISTRY_FILE.read_text(encoding="utf-8"))
    targets = DEFAULT_TARGETS | registry.get("targets", {})
    local_dir = Path(targets["local_catalog_dir"]).expanduser()
    local_toml = local_dir / "local.toml"
    if not local_toml.is_file():
        return registry

    overlay = tomllib.loads(local_toml.read_text(encoding="utf-8"))
    verbose(f"loaded local overlay: {local_toml}")

    if "targets" in overlay:
        registry["targets"] = registry.get("targets", {}) | overlay["targets"]

    if "agents" in overlay:
        agents = registry.setdefault("agents", {})
        for agent_name, agent_over in overlay["agents"].items():
            agents[agent_name] = agents.get(agent_name, {}) | agent_over

    if "source_overrides" in overlay:
        by_name = {s["name"]: s for s in registry.get("source", [])}
        for src_name, src_over in overlay["source_overrides"].items():
            if src_name in by_name:
                by_name[src_name].update(src_over)

    if "source" in overlay:
        registry.setdefault("source", []).extend(overlay["source"])

    if "skill" in overlay:
        skills_over = registry.setdefault("skill", {})
        for sk_name, sk_over in overlay["skill"].items():
            skills_over[sk_name] = skills_over.get(sk_name, {}) | sk_over

    return registry


def matches(rel: str, patterns: list[str]) -> bool:
    for pat in patterns:
        if fnmatch.fnmatch(rel, pat) or fnmatch.fnmatch(rel, pat.rstrip("/") + "/*"):
            return True
        if rel == pat.rstrip("/"):
            return True
    return False


def clone_missing(source: dict) -> None:
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
    tier = source.get("tier", PUBLIC_TIER)
    candidate_roots = [norm_path(source["path"])]
    for fb in source.get("fallback_paths", []):
        candidate_roots.append(norm_path(fb))

    existing_roots = [r for r in candidate_roots if r.is_dir()]
    if not existing_roots:
        verbose(
            f"skip source (path missing on this machine): {source['name']} @ {candidate_roots[0]}"
        )
        return []

    primary_root = candidate_roots[0]
    include = source.get("include", ["**"])
    exclude = source.get("exclude", [])
    seen_dirs: set[str] = set()
    skills: list[dict] = []

    for root in existing_roots:
        is_fallback = root != primary_root
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

            if skill_dir.name in seen_dirs:
                verbose(f"skip (already resolved from primary root): {skill_dir.name}")
                continue

            fm = parse_frontmatter(skill_md)
            name = fm.get("name") or skill_dir.name
            if str(fm.get("disable-model-invocation", "")).lower() == "true":
                verbose(f"note (disable-model-invocation=true): {name}")

            over = overrides.get(name, {}) | overrides.get(skill_dir.name, {})
            if over.get("active") is False:
                seen_dirs.add(skill_dir.name)
                verbose(f"skip (inactive): {name}")
                continue

            seen_dirs.add(skill_dir.name)
            agents_restriction = over.get("agents", source.get("agents"))
            skills.append({
                "name": name,
                "dir_name": skill_dir.name,
                "description": fm.get("description", ""),
                "path": skill_dir,
                "rel": rel,
                "tier": tier,
                "is_fallback": is_fallback,
                "source": source,
                "agents_restriction": agents_restriction,
                "tags": over.get("tags", []),
                "audience": source.get("audience", "personal"),
            })
            origin_note = " (fallback)" if is_fallback else ""
            log(f"resolved [{tier}]: {source['name']}/{rel}{origin_note}")
    return skills


# ---------------------------------------------------------------------------
# Per-Agent Tier Filtering & Sync
# ---------------------------------------------------------------------------

def default_agents_config(targets: dict) -> dict[str, dict]:
    return {
        "jetski": {
            "enabled": True,
            "kind": "jetski",
            "tiers": ["zeroasterisk", "opm", "work"],
            "skills_dir": targets["gemini_skills_dir"],
            "plugins_dir": targets["gemini_plugins_dir"],
            "native_piper_skills_dir": "",
        },
        "cloudcode": {
            "enabled": True,
            "kind": "cloudcode",
            "tiers": ["zeroasterisk", "opm"],
            "config": targets["cloudcode_config"],
        },
    }


def skill_matches_agent_restriction(restriction: list[str] | None, agent_name: str) -> bool:
    if not restriction or "*" in restriction:
        return True
    expanded: set[str] = set(restriction)
    if "gemini" in expanded:
        expanded.update({"jetski", "gemini-cli"})
    return agent_name in expanded


def filter_skills_for_agent(
    skills: list[dict], agent_name: str, allowed_tiers: list[str]
) -> list[dict]:
    tier_set = set(allowed_tiers)
    return [
        s for s in skills
        if s["tier"] in tier_set
        and skill_matches_agent_restriction(s["agents_restriction"], agent_name)
    ]


def sync_cloudcode(agent_name: str, agent_cfg: dict, skills: list[dict]) -> None:
    allowed_tiers = agent_cfg.get("tiers", ["zeroasterisk", "opm"])
    matched = filter_skills_for_agent(skills, agent_name, allowed_tiers)
    paths = [str(s["path"]) for s in matched]
    cfg_path = find_cloudcode_config(agent_cfg.get("config", ""))
    if cfg_path is None or not cfg_path.is_file():
        log(
            f"{agent_name}: no cloudcode.json found "
            f"(looked in {', '.join(CLOUDCODE_CANDIDATES)}), skipping"
        )
        return
    config = json.loads(cfg_path.read_text(encoding="utf-8"))
    config.setdefault("skills", {})["paths"] = paths
    tiers_label = ",".join(allowed_tiers)
    if DRY_RUN:
        dry(f"{agent_name} [{tiers_label}]: would write {cfg_path} skills.paths ({len(paths)} paths)")
        for p in paths:
            dry(f"  {p}")
    else:
        cfg_path.write_text(json.dumps(config, indent=2) + "\n", encoding="utf-8")
        log(f"{agent_name} [{tiers_label}]: updated skills.paths ({len(paths)} skill(s))")


def sync_symlink_dir(
    label: str,
    target_dir: Path,
    wanted: dict[str, Path],
    extra_managed_roots: list[str] | None = None,
) -> None:
    if DRY_RUN:
        dry(f"{label}: would ensure dir: {target_dir}")
    else:
        target_dir.mkdir(parents=True, exist_ok=True)

    if target_dir.is_dir():
        for link in sorted(target_dir.iterdir()):
            if not link.is_symlink():
                continue
            if not is_managed_link(link, extra_managed_roots):
                verbose(f"{label}: skip unmanaged symlink: {link.name}")
                continue
            target_ok = link.exists() and link.is_dir()
            desired = wanted.get(link.name)
            current_raw = os.readlink(link)
            if desired is None or not target_ok or current_raw != str(desired):
                if DRY_RUN:
                    if desired is None or not target_ok:
                        dry(f"{label}: would remove stale symlink: {link.name}")
                else:
                    link.unlink()
                    if desired is None or not target_ok:
                        log(f"{label}: removed stale symlink: {link.name}")

    for name, path in sorted(wanted.items()):
        link = target_dir / name
        if DRY_RUN:
            dry(f"{label}: would symlink {link} -> {path}")
            continue
        if link.is_symlink():
            if os.readlink(link) == str(path):
                verbose(f"{label}: unchanged {name}")
                continue
            link.unlink()
        elif link.exists():
            verbose(f"{label}: skip existing non-symlink: {link.name}")
            continue
        link.symlink_to(path)
        log(f"{label}: linked {name} -> {path}")


def sync_jetski(agent_name: str, agent_cfg: dict, skills: list[dict]) -> None:
    allowed_tiers = agent_cfg.get("tiers", ["zeroasterisk", "opm", "work"])
    skills_dir = Path(agent_cfg.get("skills_dir", "~/.gemini/config/skills")).expanduser()
    plugins_dir = Path(agent_cfg.get("plugins_dir", "~/.gemini/config/plugins")).expanduser()
    native_piper_raw = agent_cfg.get("native_piper_skills_dir", "")
    native_piper_dir = norm_path(native_piper_raw) if native_piper_raw else None

    # 1. Sync zeroasterisk plugins into plugins_dir (if subscribed to zeroasterisk)
    wanted_plugins: dict[str, Path] = {}
    plugin_covered_skill_dirs: set[Path] = set()
    if PUBLIC_TIER in allowed_tiers:
        plugins_root = REGISTRY_DIR / "plugins"
        if plugins_root.is_dir():
            for p in sorted(plugins_root.iterdir()):
                if p.is_dir() and (p / "plugin.json").is_file():
                    wanted_plugins[p.name] = p
                    for sk_md in p.rglob("SKILL.md"):
                        plugin_covered_skill_dirs.add(sk_md.parent.resolve())

    sync_symlink_dir(f"{agent_name} plugins", plugins_dir, wanted_plugins)

    # 2. Build non-duplicating skills_dir map across subscribed tiers:
    #    - Skip skills already mounted via plugins_dir (zero split-brain duplicates)
    #    - Skip "work" skills already live at native_piper_skills_dir (Jetski auto-mounts Piper HEAD)
    #    - Symlink "opm" skills + pre-submit fallback "work" skills not yet at Piper HEAD
    matched = filter_skills_for_agent(skills, agent_name, allowed_tiers)
    wanted_skills: dict[str, Path] = {}
    extra_roots = [str(native_piper_dir)] if native_piper_dir else []

    for s in matched:
        s_path: Path = s["path"]
        if not ((s_path / "SKILL.md").is_file() or (s_path / "GEMINI.md").is_file()):
            continue
        try:
            if s_path.resolve() in plugin_covered_skill_dirs:
                verbose(f"{agent_name} skills: skip {s['dir_name']} (mounted via plugin)")
                continue
        except OSError:
            pass

        if (
            s["tier"] == "work"
            and native_piper_dir is not None
            and (native_piper_dir / s["dir_name"] / "SKILL.md").is_file()
        ):
            verbose(
                f"{agent_name} skills: skip {s['dir_name']} "
                f"(natively auto-mounted by Jetski from {native_piper_dir})"
            )
            continue

        wanted_skills[s["dir_name"]] = s_path

    tiers_label = ",".join(allowed_tiers)
    sync_symlink_dir(
        f"{agent_name} skills [{tiers_label}]",
        skills_dir,
        wanted_skills,
        extra_managed_roots=extra_roots,
    )


def sync_generic_agent(agent_name: str, agent_cfg: dict, skills: list[dict]) -> None:
    allowed_tiers = agent_cfg.get("tiers", [PUBLIC_TIER])
    skills_dir = Path(agent_cfg["skills_dir"]).expanduser()
    matched = filter_skills_for_agent(skills, agent_name, allowed_tiers)
    wanted = {
        s["dir_name"]: s["path"]
        for s in matched
        if (s["path"] / "SKILL.md").is_file()
    }
    tiers_label = ",".join(allowed_tiers)
    sync_symlink_dir(f"{agent_name} [{tiers_label}]", skills_dir, wanted)


# ---------------------------------------------------------------------------
# ARD ai-catalog.json (strict public vs local isolation)
# ---------------------------------------------------------------------------

def safe_urn_part(text: str) -> str:
    return re.sub(r"[^a-zA-Z0-9._-]", "-", text)


def catalog_entry(s: dict) -> dict:
    src = s["source"]
    urn = ":".join([
        "urn",
        "air",
        safe_urn_part(src.get("publisher", "local")),
        safe_urn_part(src.get("namespace", src["name"])),
        safe_urn_part(s["dir_name"]),
    ])
    agents_meta = (
        ",".join(s["agents_restriction"]) if s["agents_restriction"] else f"tier:{s['tier']}"
    )
    entry = {
        "identifier": urn,
        "displayName": s["name"],
        "type": SKILL_MEDIA_TYPE,
        "description": s["description"],
        "tags": s["tags"],
        "metadata": {
            "source": src["name"],
            "tier": s["tier"],
            "audience": s["audience"],
            "agents": agents_meta,
            "relativePath": s["rel"],
        },
    }
    if src.get("url_base"):
        entry["url"] = f"{src['url_base'].rstrip('/')}/{s['rel']}"
    return entry


def make_catalog(host: dict, entries: list[dict]) -> dict:
    return {
        "specVersion": ARD_SPEC_VERSION,
        "host": host,
        "entries": entries,
    }


def write_json_catalog(out: Path, catalog: dict, label: str) -> None:
    count = len(catalog["entries"])
    if DRY_RUN:
        dry(f"would write {label}: {out} ({count} skill(s))")
    else:
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(catalog, indent=2) + "\n", encoding="utf-8")
        log(f"catalog: wrote {out} ({count} skill(s))")


def write_catalogs(
    host: dict,
    all_sources: list[dict],
    skills: list[dict],
    local_catalog_dir: Path,
) -> None:
    by_source: dict[str, list[dict]] = {}
    by_tier: dict[str, list[dict]] = {}
    for s in skills:
        by_source.setdefault(s["source"]["name"], []).append(s)
        by_tier.setdefault(s["tier"], []).append(s)

    # 1. Public ("zeroasterisk") catalogs -> REGISTRY_DIR (safe to commit to GitHub)
    public_entries: list[dict] = []
    for src in all_sources:
        tier = src.get("tier", PUBLIC_TIER)
        slug = safe_urn_part(src["name"].replace("/", "-"))
        repo_bundle_file = REGISTRY_DIR / f"ai-catalog.{slug}.json"

        if tier != PUBLIC_TIER:
            # Clean up any historically leaked non-public catalog from REGISTRY_DIR
            if repo_bundle_file.is_file():
                if DRY_RUN:
                    dry(f"would remove leaked non-public catalog from repo: {repo_bundle_file}")
                else:
                    repo_bundle_file.unlink()
                    log(f"catalog: removed non-public catalog from repo: {repo_bundle_file.name}")
            continue

        group = by_source.get(src["name"], [])
        if not group:
            continue
        entries = [catalog_entry(s) for s in group]
        public_entries.extend(entries)
        write_json_catalog(repo_bundle_file, make_catalog(host, entries), f"public bundle ({src['name']})")

    write_json_catalog(PUBLIC_CATALOG_FILE, make_catalog(host, public_entries), "public aggregate")

    # 2. Non-public ("opm", "work") + federated catalogs -> ~/.config/skills-sync/ ONLY
    federated_entries: list[dict] = list(public_entries)
    for tier, group in sorted(by_tier.items()):
        if tier == PUBLIC_TIER:
            continue
        entries = [catalog_entry(s) for s in group]
        federated_entries.extend(entries)
        tier_host = {"displayName": f"{host.get('displayName', 'Skills')} ({tier})", "identifier": f"local/{tier}"}
        write_json_catalog(
            local_catalog_dir / f"ai-catalog.{safe_urn_part(tier)}.json",
            make_catalog(tier_host, entries),
            f"local {tier} catalog",
        )

    fed_host = {"displayName": f"{host.get('displayName', 'Skills')} (Federated)", "identifier": "local/federated"}
    write_json_catalog(
        local_catalog_dir / "ai-catalog.federated.json",
        make_catalog(fed_host, federated_entries),
        "local federated catalog",
    )


def print_tier_report(skills: list[dict], agents_cfg: dict[str, dict]) -> None:
    print("\n=== Skill Tiers Resolved ===")
    for tier in KNOWN_TIERS:
        tier_skills = [s for s in skills if s["tier"] == tier]
        sources = sorted({s["source"]["name"] for s in tier_skills})
        print(f"  - {tier:<14} : {len(tier_skills):>2} skill(s)  sources={sources}")
    other_tiers = sorted({s["tier"] for s in skills if s["tier"] not in KNOWN_TIERS})
    for tier in other_tiers:
        tier_skills = [s for s in skills if s["tier"] == tier]
        print(f"  - {tier:<14} : {len(tier_skills):>2} skill(s)")

    print("\n=== Agent Tier Subscriptions ===")
    for agent_name, cfg in agents_cfg.items():
        status = "ENABLED " if cfg.get("enabled", False) else "opt-in  "
        tiers = cfg.get("tiers", [])
        matched = filter_skills_for_agent(skills, agent_name, tiers)
        print(
            f"  - {agent_name:<12} [{status}] tiers={tiers} -> {len(matched)} skill(s)"
        )
    print()


# ---------------------------------------------------------------------------

def main() -> int:
    global DRY_RUN, VERBOSE
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--verbose", action="store_true")
    ap.add_argument(
        "--clone-missing",
        action="store_true",
        help="git clone any [[source]] with repo+clone_to that is absent",
    )
    ap.add_argument(
        "--list-tiers",
        action="store_true",
        help="print resolved 3-tier inventory and per-agent subscriptions, then exit",
    )
    ap.add_argument(
        "--agents",
        default="",
        help="comma-separated agent names to sync (e.g. jetski,cloudcode,claude); runs even if opt-in",
    )
    ap.add_argument(
        "--tiers",
        default="",
        help="comma-separated tier override for this run (subset of zeroasterisk,opm,work)",
    )
    args = ap.parse_args()
    DRY_RUN, VERBOSE = args.dry_run, args.verbose

    if not REGISTRY_FILE.is_file():
        log(f"ERROR: {REGISTRY_FILE} not found")
        return 1
    registry = load_registry()

    targets = DEFAULT_TARGETS | registry.get("targets", {})
    local_catalog_dir = Path(targets["local_catalog_dir"]).expanduser()
    host = registry.get("host", {"displayName": "Skills Registry"})
    overrides = registry.get("skill", {})
    sources = registry.get("source", [])

    skills: list[dict] = []
    for source in sources:
        if args.clone_missing:
            clone_missing(source)
        skills.extend(discover(source, overrides))

    agents_cfg = default_agents_config(targets)
    for name, cfg in registry.get("agents", {}).items():
        agents_cfg[name] = agents_cfg.get(name, {}) | cfg
    register_managed_roots(sources, agents_cfg)

    log(f"{len(skills)} active skill(s) resolved across {len({s['tier'] for s in skills})} tier(s)")

    if args.list_tiers:
        print_tier_report(skills, agents_cfg)
        return 0

    selected_agents = (
        [a.strip() for a in args.agents.split(",") if a.strip()]
        if args.agents
        else [name for name, cfg in agents_cfg.items() if cfg.get("enabled", False)]
    )
    tier_override = [t.strip() for t in args.tiers.split(",") if t.strip()] if args.tiers else None

    for agent_name in selected_agents:
        if agent_name not in agents_cfg:
            log(f"ERROR: unknown agent {agent_name!r} (known: {', '.join(agents_cfg)})")
            return 1
        cfg = dict(agents_cfg[agent_name])
        if tier_override is not None:
            cfg["tiers"] = tier_override

        kind = cfg.get("kind", "symlink-dir")
        if kind == "jetski":
            sync_jetski(agent_name, cfg, skills)
        elif kind == "cloudcode":
            sync_cloudcode(agent_name, cfg, skills)
        elif kind == "symlink-dir":
            sync_generic_agent(agent_name, cfg, skills)
        else:
            log(f"ERROR: unsupported agent kind {kind!r} for {agent_name}")
            return 1

    # Write catalogs on full runs (skip rewriting repo catalogs when --agents/--tiers scoped)
    if not args.agents and tier_override is None:
        write_catalogs(host, sources, skills, local_catalog_dir)

    log("done")
    return 0


if __name__ == "__main__":
    sys.exit(main())
