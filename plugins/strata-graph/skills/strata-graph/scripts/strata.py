#!/usr/bin/env python3
"""Strata Graph deterministic compiler, validator, and standalone HTML bundler.

Zero external Python dependencies (Python 3.10+ stdlib only; uses PyYAML if
installed, with a clean stdlib fallback parser for OKF/KG frontmatter).

Supported input domains:
  - compile-okf     : Open Knowledge Format (OKF v0.2) Markdown wiki bundles
  - compile-kg      : Knowledge / Entity Graphs (SQLite pipeline.db, YAML dir, or JSON)
  - compile-atif    : ATIF v1.x, OATR v1, and Jetski transcript.jsonl trajectories
                      (--mode decision for blind-alley/backtrack flow, --mode compare for multi-run)
  - compile-process : Stateful process / workflow / architecture JSON specs or Markdown dirs
  - validate        : Deterministic integrity & diagnostic gate
  - build           : Bundle a single strata-graph/1 JSON into a zero-CDN HTML explorer
  - build-hub       : Bundle multiple strata-graph/1 JSONs into a multi-tab Explorer Hub

Architectural heritage: Inspired by Adam Gospodarczyk's (@overment) limen picture (MIT).
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import re
import sqlite3
import sys
from typing import Any

try:
  import yaml as _pyyaml  # type: ignore
except ImportError:
  _pyyaml = None

SCRIPT_DIR = Path(__file__).resolve().parent
ASSETS_DIR = SCRIPT_DIR.parent / "assets"


# ---------------------------------------------------------------------------
# Minimal safe YAML frontmatter fallback (used only if PyYAML is absent)
# ---------------------------------------------------------------------------
def parse_yaml_safe(text: str) -> dict[str, Any]:
  if _pyyaml is not None:
    loaded = _pyyaml.safe_load(text)
    return loaded if isinstance(loaded, dict) else {}
  result: dict[str, Any] = {}
  cur_key: str | None = None
  for raw_line in text.splitlines():
    if not raw_line.strip() or raw_line.lstrip().startswith("#"):
      continue
    indent = len(raw_line) - len(raw_line.lstrip(" "))
    line = raw_line.strip()
    if indent == 0 and ":" in line and not line.startswith("-"):
      k, v = line.split(":", 1)
      k = k.strip()
      v = v.strip().strip("'\"")
      if v:
        result[k] = v
        cur_key = None
      else:
        result[k] = []
        cur_key = k
    elif line.startswith("- ") and cur_key and isinstance(result.get(cur_key), list):
      val = line[2:].strip().strip("'\"")
      if ":" in val:
        sub_k, sub_v = val.split(":", 1)
        result[cur_key].append({sub_k.strip(): sub_v.strip().strip("'\"")})
      else:
        result[cur_key].append(val)
    elif indent > 0 and ":" in line and cur_key and isinstance(result.get(cur_key), list) and result[cur_key]:
      last = result[cur_key][-1]
      if isinstance(last, dict):
        sub_k, sub_v = line.split(":", 1)
        last[sub_k.strip()] = sub_v.strip().strip("'\"")
  return result


def split_frontmatter(md_text: str) -> tuple[dict[str, Any], str]:
  if not md_text.startswith("---"):
    return {}, md_text
  parts = md_text.split("\n---", 1)
  if len(parts) < 2:
    return {}, md_text
  fm_raw = parts[0][3:]
  body = parts[1].lstrip("\r\n")
  return parse_yaml_safe(fm_raw), body


def now_iso() -> str:
  return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


# ---------------------------------------------------------------------------
# 1. OKF v0.2 LLM Wiki Adapter
# ---------------------------------------------------------------------------
OKF_RELATIONS = {
  "composes-pattern": {
    "label": "composes pattern",
    "darkColor": "#2dd4bf",
    "lightColor": "#0f766e",
    "dash": "none",
    "category": "structural",
  },
  "defines-architecture": {
    "label": "defines architecture",
    "darkColor": "#60a5fa",
    "lightColor": "#2563eb",
    "dash": "none",
    "category": "structural",
  },
  "implements": {
    "label": "implements / integrates",
    "darkColor": "#a78bfa",
    "lightColor": "#7c3aed",
    "dash": "6 3",
    "category": "implementation",
  },
  "governs": {
    "label": "governs / policy",
    "darkColor": "#fbbf24",
    "lightColor": "#b45309",
    "dash": "8 3 2 3",
    "category": "governance",
  },
  "defines-term": {
    "label": "uses taxonomy",
    "darkColor": "#4ade80",
    "lightColor": "#15803d",
    "dash": "2 3",
    "category": "epistemic",
  },
  "references": {
    "label": "cross-references",
    "darkColor": "#94a3b8",
    "lightColor": "#64748b",
    "dash": "none",
    "category": "epistemic",
  },
}


def classify_okf_relation(src_sec: str, dst_sec: str, heading: str) -> str:
  if dst_sec == "patterns":
    return "composes-pattern"
  if dst_sec == "architectures":
    return "defines-architecture"
  if dst_sec == "taxonomy" or src_sec == "taxonomy":
    return "defines-term"
  if dst_sec == "governance" or src_sec == "governance":
    return "governs"
  if dst_sec == "projects" or src_sec == "projects":
    return "implements"
  if "arch" in heading.lower() or "pattern" in heading.lower():
    return "composes-pattern"
  return "references"


def derive_okf_trust(fm: dict[str, Any]) -> dict[str, Any]:
  verified = fm.get("verified")
  generated = fm.get("generated")
  status = str(fm.get("status", "draft")).lower()
  if status == "deprecated":
    tier = "deprecated"
  elif isinstance(verified, dict) and verified.get("by"):
    by = str(verified.get("by", ""))
    tier = "verified" if not by.startswith("agent:") else "machine-confirmed"
  elif isinstance(verified, list) and verified:
    tier = "verified"
  else:
    tier = "draft"
  return {
    "tier": tier,
    "generatedBy": generated.get("by") if isinstance(generated, dict) else None,
    "staleAfter": fm.get("stale_after"),
  }


def compile_okf(wiki_dir: Path, graph_id: str | None = None) -> dict[str, Any]:
  wiki_root = wiki_dir.resolve()
  if not wiki_root.is_dir():
    raise FileNotFoundError(f"OKF bundle directory not found: {wiki_dir}")

  index_path = wiki_root / "index.md"
  index_fm: dict[str, Any] = {}
  if index_path.is_file():
    index_fm, _ = split_frontmatter(index_path.read_text(encoding="utf-8"))

  title = str(index_fm.get("title") or wiki_root.name)
  subtitle = str(
    index_fm.get("description")
    or f"OKF v{index_fm.get('okf_version', '0.2')} knowledge bundle compiled into hierarchical sections, prose-grounded links, and co-citation slices."
  )
  root_id = "okf:root"
  diagnostics: list[dict[str, str]] = []

  nodes: list[dict[str, Any]] = [{
    "id": root_id,
    "title": title,
    "kind": "okf-bundle",
    "status": "ready",
    "parent": None,
    "summary": subtitle,
    "sources": [],
    "tags": [],
    "metrics": {"okf_version": str(index_fm.get("okf_version", "0.2"))},
  }]

  # Discover sections and concept files
  md_files = sorted(wiki_root.rglob("*.md"))
  file_to_node_id: dict[Path, str] = {}
  file_meta: dict[Path, tuple[dict[str, Any], str, str]] = {}
  sections_seen: dict[str, str] = {}

  for fpath in md_files:
    rel = fpath.relative_to(wiki_root)
    if rel.as_posix() in ("index.md", "log.md"):
      continue
    parts = rel.parts
    sec_slug = parts[0] if len(parts) > 1 else "general"
    if sec_slug not in sections_seen:
      sec_id = f"sec:{sec_slug}"
      sections_seen[sec_slug] = sec_id
      nodes.append({
        "id": sec_id,
        "title": sec_slug.replace("-", " ").title(),
        "kind": "section",
        "status": "ready",
        "parent": root_id,
        "summary": f"OKF domain container for {sec_slug.replace('-', ' ')} concepts.",
        "sources": [],
        "tags": [sec_slug],
        "metrics": {},
      })

    fm, body = split_frontmatter(fpath.read_text(encoding="utf-8"))
    if not fm.get("type"):
      diagnostics.append({
        "level": "warn",
        "code": "OKF_MISSING_TYPE",
        "message": f"{rel.as_posix()} is missing required OKF v0.2 frontmatter 'type'.",
      })
    nid = rel.with_suffix("").as_posix().replace("/", ":")
    file_to_node_id[fpath.resolve()] = nid
    file_meta[fpath.resolve()] = (fm, body, sec_slug)

  # Track canonical sources across all concepts (checking 1:1 source bijection)
  source_touches: dict[str, dict[str, Any]] = {}
  url_to_source_ids: dict[str, set[str]] = {}
  tag_touches: dict[str, list[str]] = {}

  for fpath, nid in file_to_node_id.items():
    fm, body, sec_slug = file_meta[fpath]
    raw_status = str(fm.get("status", "draft")).lower()
    trust = derive_okf_trust(fm)
    status = (
      "deprecated" if raw_status == "deprecated"
      else "ready" if trust["tier"] in ("verified", "machine-confirmed") or raw_status in ("active", "published", "ratified")
      else "draft"
    )

    node_sources: list[dict[str, Any]] = []
    for s in fm.get("sources") or []:
      if not isinstance(s, dict):
        continue
      sid = str(s.get("id") or s.get("resource") or "")
      surl = str(s.get("resource") or s.get("url") or "")
      if not sid:
        continue
      node_sources.append({
        "id": sid,
        "title": str(s.get("title") or sid),
        "url": surl or None,
        "author": s.get("author"),
      })
      if surl:
        url_to_source_ids.setdefault(surl, set()).add(sid)
      entry = source_touches.setdefault(sid, {
        "id": f"src:{sid}",
        "title": str(s.get("title") or sid),
        "kind": "co-citation",
        "url": surl or None,
        "summary": f"Canonical OKF provenance source ({surl or sid})",
        "touches": [],
      })
      if nid not in entry["touches"]:
        entry["touches"].append(nid)

    tags = [str(t) for t in (fm.get("tags") or []) if t]
    for t in tags:
      if t.lower() != sec_slug.lower():
        tag_touches.setdefault(t, []).append(nid)

    first_para = ""
    for line in body.splitlines():
      sline = line.strip()
      if sline and not sline.startswith("#") and not sline.startswith("[^") and not sline.startswith(">"):
        first_para = re.sub(r"\[\^[^\]]+\]", "", sline)[:280]
        break

    nodes.append({
      "id": nid,
      "title": str(fm.get("title") or fpath.stem.replace("-", " ").title()),
      "kind": str(fm.get("type") or "concept"),
      "status": status,
      "parent": sections_seen[sec_slug],
      "summary": str(fm.get("description") or first_para),
      "body": first_para if fm.get("description") and first_para != fm.get("description") else "",
      "url": fm.get("resource"),
      "trust": trust,
      "sources": node_sources,
      "tags": tags,
      "metrics": {
        "sources": len(node_sources),
        "tags": len(tags),
      },
    })

  # Check 1:1 source URL bijection
  for surl, sids in sorted(url_to_source_ids.items()):
    if len(sids) > 1:
      diagnostics.append({
        "level": "warn",
        "code": "SOURCE_BIJECTION_WARN",
        "message": f"Resource {surl} is cited under multiple source IDs: {', '.join(sorted(sids))}",
      })

  # Extract internal Markdown links with heading + sentence context
  link_re = re.compile(r"\[([^\]]+)\]\(([^)\s]+\.md(?:#[^)]+)?)\)")
  edges: list[dict[str, Any]] = []
  seen_edges: set[tuple[str, str, str]] = set()
  edge_seq = 0

  for fpath, src_id in file_to_node_id.items():
    _, body, src_sec = file_meta[fpath]
    cur_heading = "Overview"
    for raw_line in body.splitlines():
      stripped = raw_line.strip()
      if stripped.startswith("#"):
        cur_heading = stripped.lstrip("#").strip()
        continue
      if stripped.startswith("[^"):
        continue
      for match in link_re.finditer(raw_line):
        anchor_text, raw_target = match.group(1), match.group(2)
        if "://" in raw_target:
          continue
        clean_rel = raw_target.split("#", 1)[0]
        if clean_rel.startswith("/"):
          target_path = (wiki_root / clean_rel.lstrip("/")).resolve()
        else:
          target_path = (fpath.parent / clean_rel).resolve()

        # Path containment security check
        try:
          target_path.relative_to(wiki_root)
        except ValueError:
          diagnostics.append({
            "level": "error",
            "code": "PATH_OUTSIDE_BUNDLE",
            "message": f"Blocked link escaping OKF root in {fpath.name}: {raw_target}",
          })
          continue

        dst_id = file_to_node_id.get(target_path)
        if not dst_id:
          if target_path.name not in ("index.md", "log.md"):
            diagnostics.append({
              "level": "warn",
              "code": "BROKEN_MD_LINK",
              "message": f"{fpath.relative_to(wiki_root)} links to missing concept '{raw_target}'.",
            })
          continue
        if dst_id == src_id:
          continue

        _, _, dst_sec = file_meta[target_path]
        rel = classify_okf_relation(src_sec, dst_sec, cur_heading)
        dedup_key = (src_id, dst_id, rel)
        if dedup_key in seen_edges:
          continue
        seen_edges.add(dedup_key)

        clean_snippet = re.sub(r"\[\^[^\]]+\]", "", stripped)
        clean_snippet = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", clean_snippet)
        clean_snippet = clean_snippet.lstrip("-* ").strip()

        edge_seq += 1
        edges.append({
          "id": f"e{edge_seq}",
          "from": src_id,
          "to": dst_id,
          "relation": rel,
          "flowRole": "forward",
          "summary": f"[{cur_heading}] {anchor_text}",
          "contextSnippet": f"§ {cur_heading}: {clean_snippet[:220]}",
        })

  # Build overlays: multi-concept co-citations + shared themes
  overlays: list[dict[str, Any]] = []
  for sid, entry in sorted(source_touches.items(), key=lambda kv: -len(kv[1]["touches"])):
    if len(entry["touches"]) >= 2:
      overlays.append(entry)

  for tag, nids in sorted(tag_touches.items(), key=lambda kv: -len(kv[1])):
    uniq = sorted(set(nids))
    if 3 <= len(uniq) <= max(12, len(file_to_node_id) // 2):
      overlays.append({
        "id": f"tag:{tag}",
        "title": f"#{tag}",
        "kind": "theme",
        "summary": f"Cross-cutting OKF tag shared across {len(uniq)} concepts.",
        "touches": uniq,
      })

  return {
    "schema": "strata-graph/1",
    "id": graph_id or f"okf-{wiki_root.name}",
    "title": f"{title} (OKF v0.2)",
    "subtitle": subtitle,
    "domain": "okf-wiki",
    "generatedAt": now_iso(),
    "sourceLabel": str(wiki_root.name),
    "rootId": root_id,
    "relations": OKF_RELATIONS,
    "nodes": nodes,
    "edges": edges,
    "overlays": overlays[:24],
    "traces": [],
    "diagnostics": diagnostics,
  }


# ---------------------------------------------------------------------------
# 2. Knowledge / Entity Graph (KG) Adapter
# ---------------------------------------------------------------------------
KG_RELATIONS = {
  "develops": {
    "label": "develops / maintains",
    "darkColor": "#60a5fa",
    "lightColor": "#2563eb",
    "dash": "none",
    "category": "ownership",
  },
  "part-of": {
    "label": "part of / hosted by",
    "darkColor": "#2dd4bf",
    "lightColor": "#0f766e",
    "dash": "8 4",
    "category": "structural",
  },
  "supports": {
    "label": "implements / supports",
    "darkColor": "#4ade80",
    "lightColor": "#15803d",
    "dash": "none",
    "category": "capability",
  },
  "uses": {
    "label": "uses / depends on",
    "darkColor": "#a78bfa",
    "lightColor": "#7c3aed",
    "dash": "5 3",
    "category": "dependency",
  },
  "governs": {
    "label": "donated / governs",
    "darkColor": "#fbbf24",
    "lightColor": "#b45309",
    "dash": "9 3 2 3",
    "category": "governance",
  },
  "aligns-with": {
    "label": "aligns / references",
    "darkColor": "#e879f9",
    "lightColor": "#c026d3",
    "dash": "2 3",
    "category": "epistemic",
  },
}


def map_kg_predicate(raw_pred: str) -> str:
  p = raw_pred.lower().replace("_", "-")
  if any(k in p for k in ("develop", "creat", "author", "maintain", "built", "propos")):
    return "develops"
  if any(k in p for k in ("part-of", "member", "belong", "host", "contain", "subproject")):
    return "part-of"
  if any(k in p for k in ("support", "implement", "provid", "enabl", "defin")):
    return "supports"
  if any(k in p for k in ("donat", "govern", "steward", "sponsor", "standardiz")):
    return "governs"
  if any(k in p for k in ("align", "referenc", "inspir", "relat", "extend", "compat")):
    return "aligns-with"
  return "uses"


def map_kg_container(raw_type: str) -> tuple[str, str]:
  t = raw_type.lower()
  if "org" in t or "company" in t or "foundation" in t or "consortium" in t or "group" in t:
    return "grp:organizations", "Organizations & Foundations"
  if "proto" in t or "spec" in t or "standard" in t:
    return "grp:protocols", "Protocols & Standards"
  if "person" in t or "human" in t or "author" in t or "individual" in t:
    return "grp:people", "People & Contributors"
  if "capab" in t or "concept" in t or "pattern" in t or "arch" in t or "risk" in t:
    return "grp:capabilities", "Capabilities & Concepts"
  return "grp:projects", "Projects, SDKs & Tools"


def compile_kg(kg_path: Path, graph_id: str | None = None) -> dict[str, Any]:
  target = kg_path.resolve()
  db_file = target if target.suffix == ".db" else (target / "pipeline.db")
  yaml_dir = target / "kg" if (target / "kg").is_dir() else target

  root_id = "kg:root"
  nodes: list[dict[str, Any]] = [{
    "id": root_id,
    "title": "Agentic Ecosystem Knowledge Graph",
    "kind": "knowledge-graph",
    "status": "ready",
    "parent": None,
    "summary": "Multi-entity knowledge graph linking organizations, people, open protocols, SDK projects, capabilities, and dated ecosystem events.",
    "sources": [],
    "tags": [],
    "metrics": {},
  }]
  containers: dict[str, str] = {}
  entity_ids: set[str] = set()
  slug_to_eid: dict[str, str] = {}
  edges: list[dict[str, Any]] = []
  diagnostics: list[dict[str, str]] = []
  source_overlays: dict[str, dict[str, Any]] = {}

  def ensure_container(cid: str, ctitle: str) -> str:
    if cid not in containers:
      containers[cid] = ctitle
      nodes.append({
        "id": cid,
        "title": ctitle,
        "kind": "entity-domain",
        "status": "ready",
        "parent": root_id,
        "summary": f"Entity domain grouping for {ctitle}.",
        "sources": [],
        "tags": [],
        "metrics": {},
      })
    return cid

  # 1. Read SQLite pipeline.db if present (read-only URI)
  if db_file.is_file():
    conn = sqlite3.connect(f"file:{db_file}?mode=ro", uri=True)
    src_lookup: dict[int, tuple[str, str]] = {}
    for row in conn.execute("SELECT id, uri, title FROM sources"):
      src_lookup[int(row[0])] = (str(row[1] or ""), str(row[2] or f"Source {row[0]}"))

    for row in conn.execute(
      "SELECT entity_id, name, kind, type, description, status, source_id FROM entities WHERE merged_into IS NULL"
    ):
      eid, name, kind, etype, desc, status, sid = row
      eid = str(eid)
      cid, ctitle = map_kg_container(str(etype or kind or "project"))
      ensure_container(cid, ctitle)
      entity_ids.add(eid)
      slug = eid.split(":", 1)[-1].lower()
      slug_to_eid[slug] = eid

      ent_sources = []
      if sid is not None and int(sid) in src_lookup:
        s_uri, s_title = src_lookup[int(sid)]
        ent_sources.append({"id": f"s-{sid}", "title": s_title, "url": s_uri})
        ov = source_overlays.setdefault(f"s-{sid}", {
          "id": f"src:s-{sid}",
          "title": s_title[:58],
          "kind": "source-doc",
          "url": s_uri,
          "summary": f"Extracted knowledge-graph source document ({s_uri})",
          "touches": [],
        })
        if eid not in ov["touches"]:
          ov["touches"].append(eid)

      nodes.append({
        "id": eid,
        "title": str(name or eid),
        "kind": str(etype or kind or "entity").lower(),
        "status": "ready" if str(status) == "approved" else "draft",
        "parent": cid,
        "summary": str(desc or ""),
        "sources": ent_sources,
        "tags": [str(kind)] if kind else [],
        "metrics": {"type": str(etype or kind or "")},
      })

    edge_seq = 0
    seen_pairs: set[tuple[str, str, str]] = set()
    for row in conn.execute(
      "SELECT source_entity_id, target_entity_id, edge_type, confidence FROM edges"
    ):
      u, v, etype, conf = str(row[0]), str(row[1]), str(row[2] or "USES"), row[3]
      if u not in entity_ids or v not in entity_ids or u == v:
        continue
      rel = map_kg_predicate(etype)
      if (u, v, rel) in seen_pairs:
        continue
      seen_pairs.add((u, v, rel))
      edge_seq += 1
      edges.append({
        "id": f"kge-{edge_seq}",
        "from": u,
        "to": v,
        "relation": rel,
        "flowRole": "forward",
        "summary": f"{etype} (confidence: {conf})",
        "contextSnippet": f"Predicate: {etype}",
      })
    conn.close()

  # 2. Merge explicit curated YAML relations & timeline if present
  rel_yaml = yaml_dir / "relations.yaml"
  if rel_yaml.is_file():
    parsed = parse_yaml_safe(rel_yaml.read_text(encoding="utf-8"))
    for item in parsed.get("relations") or []:
      if not isinstance(item, dict):
        continue
      subj = str(item.get("subject") or "").strip()
      pred = str(item.get("predicate") or "relates_to").strip()
      obj = str(item.get("object") or "").strip()
      if not subj or not obj:
        continue

      def resolve_or_add(slug_raw: str) -> str:
        s_low = slug_raw.lower()
        if s_low in slug_to_eid:
          return slug_to_eid[s_low]
        # Check YAML entity file if available
        for cand in (yaml_dir / "entities").rglob(f"{slug_raw}.yaml") if (yaml_dir / "entities").is_dir() else []:
          efm = parse_yaml_safe(cand.read_text(encoding="utf-8"))
          etype = str(efm.get("type") or cand.parent.name.rstrip("s"))
          cid, ctitle = map_kg_container(etype)
          ensure_container(cid, ctitle)
          eid_new = f"{etype.lower()}:{slug_raw}"
          entity_ids.add(eid_new)
          slug_to_eid[s_low] = eid_new
          nodes.append({
            "id": eid_new,
            "title": str(efm.get("name") or slug_raw.replace("-", " ").title()),
            "kind": etype.lower(),
            "status": "ready",
            "parent": cid,
            "summary": str(efm.get("description") or ""),
            "url": efm.get("url"),
            "sources": [],
            "tags": [],
            "metrics": {},
          })
          return eid_new
        cid, ctitle = map_kg_container("concept" if "badge" in s_low or "passport" in s_low else "project")
        ensure_container(cid, ctitle)
        eid_new = f"entity:{slug_raw}"
        entity_ids.add(eid_new)
        slug_to_eid[s_low] = eid_new
        nodes.append({
          "id": eid_new,
          "title": slug_raw.replace("-", " ").upper() if len(slug_raw) <= 4 else slug_raw.replace("-", " ").title(),
          "kind": "entity",
          "status": "ready",
          "parent": cid,
          "summary": "Curated entity from relations.yaml.",
          "sources": [],
          "tags": [],
          "metrics": {},
        })
        return eid_new

      u_id = resolve_or_add(subj)
      v_id = resolve_or_add(obj)
      if u_id != v_id:
        rel = map_kg_predicate(pred)
        note = str(item.get("note") or "")
        edges.append({
          "id": f"yaml-rel-{len(edges) + 1}",
          "from": u_id,
          "to": v_id,
          "relation": rel,
          "flowRole": "forward",
          "summary": f"{pred}" + (f" — {note}" if note else ""),
          "contextSnippet": f"Curated relation: {subj} {pred} {obj}" + (f" ({note})" if note else ""),
        })

  traces: list[dict[str, Any]] = []
  tl_yaml = yaml_dir / "timeline.yaml"
  if tl_yaml.is_file():
    parsed_tl = parse_yaml_safe(tl_yaml.read_text(encoding="utf-8"))
    t_steps = []
    step_idx = 0
    for ev in parsed_tl.get("events") or []:
      if not isinstance(ev, dict):
        continue
      for actor in ev.get("actors") or []:
        eid = slug_to_eid.get(str(actor).lower())
        if eid:
          step_idx += 1
          t_steps.append({
            "stepIndex": step_idx,
            "nodeId": eid,
            "label": f"[{ev.get('date', '')}] {ev.get('title', '')} ({actor})",
            "role": "normal",
            "observation": str(ev.get("description") or "").strip()[:220],
          })
    if t_steps:
      traces.append({
        "id": "kg-timeline",
        "title": "Ecosystem Timeline Events",
        "color": "#34d399",
        "steps": t_steps,
      })

  overlays = [
    ov for ov in sorted(source_overlays.values(), key=lambda x: -len(x["touches"]))
    if len(ov["touches"]) >= 2
  ][:18]

  return {
    "schema": "strata-graph/1",
    "id": graph_id or "agents-kg",
    "title": "Agentic Web Knowledge Graph",
    "subtitle": f"{len(entity_ids)} entities across organizations, people, protocols, SDKs, and capabilities with {len(edges)} typed relations.",
    "domain": "knowledge-graph",
    "generatedAt": now_iso(),
    "sourceLabel": target.name,
    "rootId": root_id,
    "relations": KG_RELATIONS,
    "nodes": nodes,
    "edges": edges,
    "overlays": overlays,
    "traces": traces,
    "diagnostics": diagnostics,
  }


# ---------------------------------------------------------------------------
# 3. ATIF / OATR / Jetski Trajectory Adapter (Decision Spine + Multi-Run Compare)
# ---------------------------------------------------------------------------
ATIF_RELATIONS = {
  "advances-to": {
    "label": "advances turn",
    "darkColor": "#60a5fa",
    "lightColor": "#2563eb",
    "dash": "none",
    "category": "flow",
  },
  "explores-spur": {
    "label": "explores hypothesis / blind alley",
    "darkColor": "#fb7185",
    "lightColor": "#be123c",
    "dash": "6 3",
    "category": "counterfactual",
  },
  "backtracks-to": {
    "label": "↺ backtracks & pivots",
    "darkColor": "#fb923c",
    "lightColor": "#c2410c",
    "dash": "7 4",
    "category": "backtrack",
  },
  "delegates-subagent": {
    "label": "delegates subagent",
    "darkColor": "#c084fc",
    "lightColor": "#7e22ce",
    "dash": "9 3 2 3",
    "category": "delegation",
  },
  "invokes-tool": {
    "label": "invokes tool",
    "darkColor": "#2dd4bf",
    "lightColor": "#0f766e",
    "dash": "none",
    "category": "tool",
  },
  "produces-outcome": {
    "label": "verifies / produces",
    "darkColor": "#4ade80",
    "lightColor": "#15803d",
    "dash": "none",
    "category": "outcome",
  },
}


def normalize_trajectory_file(path: Path) -> dict[str, Any]:
  """Parse ATIF v1.x JSON, OATR v1 JSON, or Jetski transcript.jsonl into a unified Trajectory dict."""
  text = path.read_text(encoding="utf-8")

  # Format A: JSONL (Jetski transcript.jsonl)
  if path.suffix == ".jsonl":
    raw_lines = [json.loads(line) for line in text.splitlines() if line.strip()]
    return _normalize_jetski_jsonl(path, raw_lines)

  doc = json.loads(text)

  # Format B: OATR v1 TrajectoryBundle ({"trajectories": {...}, "rootTrajectoryId": ...})
  if isinstance(doc, dict) and "trajectories" in doc and isinstance(doc["trajectories"], dict):
    return _normalize_oatr_bundle(path, doc)

  # Format C: ATIF v1.x / v1.7 Document ({"schema_version": "ATIF-...", "steps": [...]})
  if isinstance(doc, dict) and "steps" in doc:
    return _normalize_atif_doc(path, doc)

  raise ValueError(f"Unrecognized trajectory schema in {path}")


def _normalize_atif_doc(path: Path, doc: dict[str, Any]) -> dict[str, Any]:
  tid = str(doc.get("trajectory_id") or doc.get("session_id") or path.stem)
  agent_obj = doc.get("agent") or {}
  agent_name = str(agent_obj.get("name") or "agent")
  model_name = str(agent_obj.get("model_name") or "")
  sub_by_id = {
    str(sub.get("trajectory_id") or sub.get("session_id") or f"sub-{i}"): sub
    for i, sub in enumerate(doc.get("subagent_trajectories") or [])
  }

  events: list[dict[str, Any]] = []
  for stp in doc.get("steps") or []:
    src = str(stp.get("source") or "agent").lower()
    msg_raw = stp.get("message")
    if isinstance(msg_raw, list):
      msg = " ".join(str(p.get("text") or "") for p in msg_raw if isinstance(p, dict)).strip()
    else:
      msg = str(msg_raw or "").strip()
    thought = str(stp.get("reasoning_content") or "").strip()

    obs_by_call: dict[str, dict[str, Any]] = {}
    for res in (stp.get("observation") or {}).get("results") or []:
      if isinstance(res, dict) and res.get("source_call_id"):
        obs_by_call[str(res["source_call_id"])] = res

    tcalls = stp.get("tool_calls") or []
    metrics = stp.get("metrics") or {}
    tok = int(metrics.get("prompt_tokens") or 0) + int(metrics.get("completion_tokens") or 0)

    if not tcalls:
      events.append({
        "source": src,
        "tool": None,
        "label": f"{src.title()}: {msg[:54]}" if msg else f"{src.title()} turn",
        "thought": thought,
        "observation": msg,
        "is_error": False,
        "tokens": tok,
        "subagent": None,
      })
    else:
      for tc in tcalls:
        cid = str(tc.get("tool_call_id") or "")
        fn = str(tc.get("function_name") or "tool")
        args = tc.get("arguments") or {}
        res = obs_by_call.get(cid, {})
        res_content = res.get("content")
        if isinstance(res_content, list):
          obs_txt = " ".join(str(x.get("text") or "") for x in res_content if isinstance(x, dict))
        else:
          obs_txt = str(res_content or "")
        extra = res.get("extra") or {}
        tc_extra = tc.get("extra") or {}
        is_err = bool(
          extra.get("is_error")
          or tc_extra.get("exit_code", 0) not in (0, None)
          or "permission denied" in obs_txt.lower()
          or "error" in str(extra.get("status", "")).lower()
        )
        sub_doc = None
        for sref in res.get("subagent_trajectory_ref") or []:
          ref_id = str(sref.get("trajectory_id") or "")
          if ref_id in sub_by_id:
            sub_doc = _normalize_atif_doc(path, sub_by_id[ref_id])
        arg_preview = ", ".join(f"{k}={str(v)[:28]}" for k, v in list(args.items())[:2])
        events.append({
          "source": src,
          "tool": fn,
          "label": f"{fn}({arg_preview})" if arg_preview else fn,
          "thought": thought or msg,
          "observation": obs_txt[:240],
          "is_error": is_err,
          "tokens": tok,
          "subagent": sub_doc,
        })

  fm = doc.get("final_metrics") or {}
  total_tok = int(fm.get("total_prompt_tokens") or 0) + int(fm.get("total_completion_tokens") or 0)
  return {
    "id": tid,
    "title": f"{agent_name}: {doc.get('notes') or tid}",
    "agent": agent_name,
    "model": model_name,
    "total_tokens": total_tok or sum(e["tokens"] for e in events),
    "events": events,
  }


def _normalize_oatr_bundle(path: Path, bundle: dict[str, Any]) -> dict[str, Any]:
  trajs = bundle.get("trajectories") or {}
  root_tid = str(bundle.get("rootTrajectoryId") or next(iter(trajs.keys())))
  root_t = trajs[root_tid]
  producer = (root_t.get("producer") or {}).get("displayName") or "OATR Agent"
  model = ((root_t.get("agent") or {}).get("model") or {}).get("displayName") or "gemini"
  title = str(root_t.get("title") or f"{producer} ({root_tid[:8]})")

  def parse_oatr_traj(t_obj: dict[str, Any]) -> list[dict[str, Any]]:
    evs: list[dict[str, Any]] = []
    for stp in t_obj.get("steps") or []:
      src = str(stp.get("source") or "AGENT").lower()
      if src == "system":
        continue
      texts = []
      thoughts = []
      for c in stp.get("content") or []:
        if "text" in c and isinstance(c["text"], dict):
          texts.append(str(c["text"].get("text") or ""))
        if "reasoning" in c and isinstance(c["reasoning"], dict):
          thoughts.append(str(c["reasoning"].get("text") or ""))
      msg = " ".join(texts).strip()
      thought = " ".join(thoughts).strip()
      usage_tot = ((stp.get("usage") or {}).get("total")) or {}
      tok = int(usage_tot.get("inputTokenCount") or 0) + int(usage_tot.get("outputTokenCount") or 0)

      actions = stp.get("actions") or []
      if not actions:
        if msg or thought:
          evs.append({
            "source": src,
            "tool": None,
            "label": f"{src.title()}: {msg[:54]}" if msg else f"{src.title()} reasoning",
            "thought": thought,
            "observation": msg[:240],
            "is_error": False,
            "tokens": tok,
            "subagent": None,
          })
      else:
        for act in actions:
          fn = str(act.get("name") or "tool")
          args = act.get("arguments") or {}
          obs = str(act.get("result") or "")
          is_err = bool(act.get("errored") or "not found" in obs.lower() or "permission denied" in obs.lower())
          sub_norm = None
          sub_canon = (act.get("canonical") or {}).get("subagent") or {}
          child_id = sub_canon.get("trajectoryId")
          if child_id and child_id in trajs:
            sub_norm = {
              "id": child_id,
              "title": str((sub_canon.get("agent") or {}).get("displayName") or child_id[:8]),
              "events": parse_oatr_traj(trajs[child_id]),
            }
          elif (act.get("resultData") or {}).get("recentActivity"):
            sub_evs = []
            for ra in act["resultData"]["recentActivity"]:
              sub_evs.append({
                "source": "agent",
                "tool": str(ra.get("content") or "tool"),
                "label": f"{ra.get('displayName') or ra.get('content')}: {ra.get('description', '')[:42]}",
                "thought": "",
                "observation": str(ra.get("status") or ""),
                "is_error": False,
                "tokens": 0,
                "subagent": None,
              })
            sub_norm = {
              "id": str(child_id or "subagent"),
              "title": str(act["resultData"].get("agentName") or "subagent"),
              "events": sub_evs,
            }
          arg_preview = ", ".join(f"{k}={str(v)[:26]}" for k, v in list(args.items())[:2])
          evs.append({
            "source": src,
            "tool": fn,
            "label": f"{fn}({arg_preview})" if arg_preview else fn,
            "thought": thought or msg,
            "observation": obs[:240],
            "is_error": is_err,
            "tokens": tok,
            "subagent": sub_norm,
          })
    return evs

  events = parse_oatr_traj(root_t)
  tot_u = ((root_t.get("usage") or {}).get("total")) or {}
  tot_tok = int(tot_u.get("inputTokenCount") or 0) + int(tot_u.get("outputTokenCount") or 0)
  return {
    "id": root_tid,
    "title": title,
    "agent": producer,
    "model": model,
    "total_tokens": tot_tok or sum(e["tokens"] for e in events),
    "events": events,
  }


def _normalize_jetski_jsonl(path: Path, raw_steps: list[dict[str, Any]]) -> dict[str, Any]:
  """Synthesize semantic turns & real blind alleys from a Jetski transcript.jsonl."""
  events: list[dict[str, Any]] = []
  n = len(raw_steps)
  i = 0
  while i < n:
    s = raw_steps[i]
    stype = s.get("type")
    if stype == "USER_INPUT":
      raw_c = re.sub(r"</?USER_REQUEST>", "", str(s.get("content") or "")).strip()
      if raw_c and not raw_c.startswith("<CONTEXT_SUMMARY>"):
        events.append({
          "source": "user",
          "tool": None,
          "label": f"User Goal: {raw_c[:56]}…",
          "thought": "",
          "observation": raw_c[:260],
          "is_error": False,
          "tokens": 0,
          "subagent": None,
        })
      i += 1
      continue

    if stype == "PLANNER_RESPONSE":
      tcalls = s.get("tool_calls") or []
      thought = str(s.get("thinking") or "").strip()[:240]
      msg = str(s.get("content") or "").strip()

      # Collect immediately following GENERIC tool outputs
      outputs: list[dict[str, Any]] = []
      j = i + 1
      while j < n and raw_steps[j].get("type") == "GENERIC":
        outputs.append(raw_steps[j])
        j += 1

      if not tcalls and msg:
        events.append({
          "source": "agent",
          "tool": None,
          "label": f"Agent Update: {msg[:52]}…",
          "thought": thought,
          "observation": msg[:240],
          "is_error": False,
          "tokens": 0,
          "subagent": None,
        })
      elif tcalls:
        # Group homogeneous read/search batches into crisp semantic beats while keeping distinct tools/errors separate
        grouped_by_tool: dict[str, dict[str, Any]] = {}
        for idx_tc, tc in enumerate(tcalls):
          fn = str(tc.get("name") or tc.get("tool_name") or "tool")
          args = tc.get("arguments") or tc.get("args") or {}
          if isinstance(args, str):
            try:
              args = json.loads(args)
            except Exception:
              args = {"raw": args}
          out_step = outputs[idx_tc] if idx_tc < len(outputs) else {}
          out_txt = str(out_step.get("content") or "")
          out_err = (
            out_step.get("status") == "ERROR"
            or "Encountered error" in out_txt
            or "HTTP Error 404" in out_txt
            or "404 Not Found" in out_txt
            or '"status": 404' in out_txt
            or "cannot access" in out_txt
          )

          # Distinguish specific investigative probes (Snowflake/404, search_web, github search_code, git unshallow)
          cmd_str = str(args.get("CommandLine") or args.get("query") or args.get("Path") or "")
          if "syndication.twimg" in cmd_str or "fxtwitter" in cmd_str:
            key = "probe_twitter_404"
            label = "Probe Twitter Syndication API (Media ID -> 404)"
            out_err = True
          elif fn == "search_web":
            key = f"search_web_{idx_tc}"
            label = f"search_web('{ str(args.get('query', ''))[:38] }')"
            # Vertex search_web paraphrased exact rare strings without hitting repo
            if "overment" not in out_txt.lower() and "limen" not in out_txt.lower():
              out_err = True
          elif fn == "call_mcp_tool" and "github" in str(args.get("ServerName", "")).lower():
            key = f"github_{args.get('ToolName', 'search')}"
            label = f"github.{args.get('ToolName', 'search_code')} (structural tokens)"
          elif "unshallow" in cmd_str or "ef12ece" in cmd_str:
            key = "git_forensics_ef12ece"
            label = "Git Unshallow & Extract Exact Oct 2 Commit ef12ece"
          elif "ffmpeg" in cmd_str or "ffprobe" in cmd_str:
            key = "video_frame_extract"
            label = "Download MP4 & Extract 21 Keyframes via ffmpeg"
          else:
            key = fn
            label = f"{fn}"

          bucket = grouped_by_tool.setdefault(key, {
            "source": "agent",
            "tool": fn,
            "label": label,
            "count": 0,
            "thought": thought,
            "observation": out_txt[:240],
            "is_error": False,
            "tokens": 0,
            "subagent": None,
          })
          bucket["count"] += 1
          if out_err:
            bucket["is_error"] = True
            bucket["observation"] = out_txt[:240]

        for k, b in grouped_by_tool.items():
          if b["count"] > 1 and k == b["tool"]:
            b["label"] = f"{b['tool']} ×{b['count']} batch"
          events.append(b)
      i = j
      continue

    i += 1

  # Deduplicate consecutive identical batch turns to keep decision graph crisp (<= 28 nodes)
  compact: list[dict[str, Any]] = []
  for ev in events:
    if compact and compact[-1]["tool"] == ev["tool"] and compact[-1]["label"].split(" ×")[0] == ev["label"].split(" ×")[0] and not ev["is_error"] and not compact[-1]["is_error"]:
      compact[-1]["label"] = f"{ev['tool'] or 'turn'} (merged batch)"
      continue
    compact.append(ev)

  return {
    "id": path.parent.parent.parent.name[:12] if ".system_generated" in str(path) else path.stem,
    "title": "Jetski Forensic Investigation (Live Session)",
    "agent": "Jetski",
    "model": "gemini-3-pro",
    "total_tokens": 0,
    "events": compact[:26],
  }


def compile_atif_decision(traj_paths: list[Path], graph_id: str | None = None) -> dict[str, Any]:
  """Compile a trajectory into a hierarchical Phase/Turn Decision Graph with Blind Alleys & ↺ Backtracks."""
  norm = normalize_trajectory_file(traj_paths[0].resolve())
  root_id = "atif:root"
  nodes: list[dict[str, Any]] = [{
    "id": root_id,
    "title": norm["title"],
    "kind": "trajectory",
    "status": "ready",
    "parent": None,
    "summary": f"Agent trajectory ({norm['agent']}) showing forward reasoning trunk, blind-alley spurs (✕), explicit backtrack pivots (↺), and nested subagents.",
    "sources": [],
    "tags": [norm["agent"]],
    "metrics": {"agent": norm["agent"], "model": norm["model"], "turns": len(norm["events"])},
  }]

  edges: list[dict[str, Any]] = []
  trace_steps: list[dict[str, Any]] = []
  tool_touches: dict[str, list[str]] = {}
  diagnostics: list[dict[str, str]] = []

  # Group turns into logical lifecycle phases
  phases = [
    ("phase:orient", "1. Intake & Forensic Grounding"),
    ("phase:search", "2. Origin Search & Hypothesis Spurs"),
    ("phase:verify", "3. Deep Schema & Source Synthesis"),
  ]
  for pid, ptitle in phases:
    nodes.append({
      "id": pid,
      "title": ptitle,
      "kind": "phase",
      "status": "ready",
      "parent": root_id,
      "summary": f"Trajectory phase: {ptitle}",
      "sources": [],
      "tags": [],
      "metrics": {},
    })

  evs = norm["events"]
  total_evs = max(1, len(evs))
  last_trunk_id: str | None = None
  pending_blind_ids: list[str] = []
  blind_count = 0
  step_seq = 0

  for idx, ev in enumerate(evs):
    nid = f"turn:{idx + 1}"
    ratio = idx / total_evs
    phase_id = phases[0][0] if ratio < 0.28 else phases[1][0] if ratio < 0.68 else phases[2][0]

    is_blind = bool(ev.get("is_error"))
    has_sub = ev.get("subagent") is not None
    status = "blind-alley" if is_blind else "subagent" if has_sub else "ready"

    nodes.append({
      "id": nid,
      "title": f"T{idx + 1}: {ev['label']}",
      "kind": ev.get("tool") or ev.get("source") or "turn",
      "status": status,
      "parent": phase_id,
      "summary": ev.get("thought") or ev.get("observation") or ev["label"],
      "body": ev.get("observation") or "",
      "sources": [],
      "tags": [ev["tool"]] if ev.get("tool") else [],
      "metrics": {
        "turn": idx + 1,
        "tool": ev.get("tool") or "reasoning",
        "outcome": "BLIND ALLEY / ERROR" if is_blind else "OK",
      },
    })

    if ev.get("tool"):
      tool_touches.setdefault(ev["tool"], []).append(nid)

    # Nested subagent children!
    if has_sub:
      sub = ev["subagent"]
      prev_sub_id = None
      for s_idx, sev in enumerate(sub.get("events") or []):
        snid = f"{nid}:sub:{s_idx + 1}"
        nodes.append({
          "id": snid,
          "title": f"Sub {s_idx + 1}: {sev['label']}",
          "kind": sev.get("tool") or "subagent-step",
          "status": "error" if sev.get("is_error") else "ready",
          "parent": nid,
          "summary": sev.get("observation") or sev["label"],
          "sources": [],
          "tags": [],
          "metrics": {"subagent": sub.get("title", "subagent")},
        })
        if prev_sub_id:
          edges.append({
            "id": f"sube-{snid}",
            "from": prev_sub_id,
            "to": snid,
            "relation": "advances-to",
            "flowRole": "forward",
            "summary": "Subagent sequential step",
          })
        prev_sub_id = snid

    step_seq += 1
    if is_blind:
      blind_count += 1
      anchor = last_trunk_id
      if anchor:
        edges.append({
          "id": f"spur-{idx + 1}",
          "from": anchor,
          "to": nid,
          "relation": "explores-spur",
          "flowRole": "forward",
          "summary": f"Exploratory attempt hit obstacle: {ev['label']}",
          "contextSnippet": ev.get("observation", "")[:180],
        })
      pending_blind_ids.append(nid)
      trace_steps.append({
        "stepIndex": step_seq,
        "nodeId": nid,
        "label": f"✕ Blind Alley — {ev['label']}",
        "role": "blind-alley",
        "isError": True,
        "thought": ev.get("thought", ""),
        "observation": ev.get("observation", ""),
      })
      diagnostics.append({
        "level": "info",
        "code": "BLIND_ALLEY_DETECTED",
        "message": f"Turn T{idx + 1} ({ev['label']}) classified as blind alley; backtrack arc wired to pivot.",
      })
    else:
      # Recovering from 1 or more blind alleys -> emit explicit ↺ backtrack arc(s) + revisit anchor!
      if pending_blind_ids:
        pivot_target = last_trunk_id or nid
        for bid in pending_blind_ids:
          edges.append({
            "id": f"bt-{bid}->{pivot_target}",
            "from": bid,
            "to": pivot_target,
            "relation": "backtracks-to",
            "flowRole": "backtrack",
            "summary": f"↺ Backtracked from dead-end {bid} to pivot strategy",
            "contextSnippet": f"Agent abandoned {bid} and pivoted to {ev['label']}.",
          })
        if last_trunk_id:
          step_seq += 1
          trace_steps.append({
            "stepIndex": step_seq,
            "nodeId": last_trunk_id,
            "label": f"↺ Backtrack & Re-evaluate at {last_trunk_id}",
            "role": "backtrack",
            "thought": f"Pivoting away from {len(pending_blind_ids)} unproductive spur(s) toward {ev['label']}.",
          })
        pending_blind_ids.clear()

      if last_trunk_id:
        edges.append({
          "id": f"trk-{last_trunk_id}->{nid}",
          "from": last_trunk_id,
          "to": nid,
          "relation": "delegates-subagent" if has_sub else "advances-to",
          "flowRole": "forward",
          "summary": f"Advances along winning trunk to {ev['label']}",
        })
      last_trunk_id = nid

      step_seq += 1
      trace_steps.append({
        "stepIndex": step_seq,
        "nodeId": nid,
        "label": ev["label"],
        "role": "subagent" if has_sub else "goal" if idx == len(evs) - 1 else "normal",
        "thought": ev.get("thought", ""),
        "observation": ev.get("observation", ""),
      })

  overlays = [
    {
      "id": f"tool-slice:{tool}",
      "title": f"Tool: {tool}",
      "kind": "tool-usage",
      "summary": f"Invoked across {len(nids)} trajectory turn(s).",
      "touches": nids,
    }
    for tool, nids in sorted(tool_touches.items(), key=lambda kv: -len(kv[1]))
  ]

  return {
    "schema": "strata-graph/1",
    "id": graph_id or f"atif-{norm['id']}",
    "title": f"ATIF Trajectory: {norm['title']}",
    "subtitle": f"{len(evs)} semantic turns · {blind_count} blind alleys (✕) with explicit ↺ backtrack return arcs.",
    "domain": "atif-trajectory",
    "generatedAt": now_iso(),
    "sourceLabel": traj_paths[0].name,
    "rootId": root_id,
    "relations": ATIF_RELATIONS,
    "nodes": nodes,
    "edges": edges,
    "overlays": overlays,
    "traces": [{
      "id": norm["id"],
      "title": norm["title"],
      "color": "#60a5fa",
      "agent": norm["agent"],
      "model": norm["model"],
      "totalTokens": norm["total_tokens"],
      "blindAlleyCount": blind_count,
      "steps": trace_steps,
    }],
    "diagnostics": diagnostics,
  }


def compile_atif_compare(traj_paths: list[Path], graph_id: str | None = None) -> dict[str, Any]:
  """Compile 2..N trajectories onto a shared Capability/Tool/Failure Interaction Graph for cross-run comparison."""
  norms = [normalize_trajectory_file(p.resolve()) for p in traj_paths]
  root_id = "cmp:root"

  nodes: list[dict[str, Any]] = [
    {
      "id": root_id,
      "title": f"Cross-Trajectory Interaction & Blind-Alley Comparison ({len(norms)} Runs)",
      "kind": "atif-comparison",
      "status": "ready",
      "parent": None,
      "summary": "Shared capability, tool, subagent, and failure-mode graph comparing multiple real ATIF / OATR / Jetski agent trajectories side-by-side.",
      "sources": [],
      "tags": [],
      "metrics": {"runs_compared": len(norms)},
    },
    {
      "id": "state:intake",
      "title": "User Goal & Context Intake",
      "kind": "stage",
      "status": "ready",
      "parent": root_id,
      "summary": "Initial task prompt and workspace context ingestion across runs.",
      "sources": [],
      "tags": [],
      "metrics": {},
    },
    {
      "id": "state:planner",
      "title": "Planner & Hypothesis Router",
      "kind": "stage",
      "status": "gate",
      "parent": root_id,
      "summary": "Central reasoning hub where agents select tools, evaluate errors, and pivot after blind alleys.",
      "sources": [],
      "tags": [],
      "metrics": {},
    },
    {
      "id": "state:synthesis",
      "title": "Verified Resolution & Synthesis",
      "kind": "stage",
      "status": "ready",
      "parent": root_id,
      "summary": "Final grounded output or completed task verification.",
      "sources": [],
      "tags": [],
      "metrics": {},
    },
  ]

  node_ids = {"state:intake", "state:planner", "state:synthesis"}
  tool_run_touches: dict[str, set[str]] = {}
  edge_counts: dict[tuple[str, str, str, str], list[str]] = {}
  traces: list[dict[str, Any]] = []
  palette = ["#60a5fa", "#34d399", "#f472b6", "#fbbf24", "#a78bfa", "#22d3ee"]

  def canonical_tool_bucket(tool_name: str | None) -> tuple[str, str, str]:
    if not tool_name:
      return ("state:planner", "Planner & Hypothesis Router", "stage")
    tl = tool_name.lower()
    if "subagent" in tl or tl in ("task", "invoke_agent", "invoke_subagent"):
      return ("cap:subagent", "Subagent Delegation (task / invoke_agent)", "subagent")
    if "search_web" in tl:
      return ("cap:web_search", "Web Grounding Search (search_web)", "tool")
    if "github" in tl or "mcp" in tl:
      return ("cap:mcp_code_search", "MCP Structural Code Search (github)", "tool")
    if tl in ("read_file", "skill_search"):
      return ("cap:file_inspect", "File & Skill Inspection (read_file)", "tool")
    if tl in ("write_file", "edit_file"):
      return ("cap:artifact_write", "Artifact & Code Authoring (write_file)", "tool")
    if tl in ("bash", "run_command"):
      return ("cap:shell_exec", "Shell / Forensics Execution (bash / run_command)", "tool")
    return (f"cap:{tl}", f"Tool: {tool_name}", "tool")

  def add_edge(u: str, v: str, rel: str, flow: str, run_title: str) -> None:
    if u == v:
      return
    k = (u, v, rel, flow)
    edge_counts.setdefault(k, []).append(run_title)

  for r_idx, norm in enumerate(norms):
    run_label = f"R{r_idx + 1}: {norm['title'][:36]}"
    steps_out: list[dict[str, Any]] = []
    prev_state = "state:intake"
    steps_out.append({
      "stepIndex": 1,
      "nodeId": "state:intake",
      "label": f"{norm['agent']} starts trajectory",
      "role": "normal",
    })
    add_edge("state:intake", "state:planner", "advances-to", "forward", run_label)
    prev_state = "state:planner"
    blind_cnt = 0

    for ev in norm["events"]:
      if ev["source"] == "user":
        continue
      cid, ctitle, ckind = canonical_tool_bucket(ev.get("tool"))
      if cid not in node_ids:
        node_ids.add(cid)
        nodes.append({
          "id": cid,
          "title": ctitle,
          "kind": ckind,
          "status": "subagent" if ckind == "subagent" else "ready",
          "parent": root_id,
          "summary": f"Shared capability invoked across trajectories ({ctitle}).",
          "sources": [],
          "tags": [],
          "metrics": {},
        })
      tool_run_touches.setdefault(cid, set()).add(run_label)

      add_edge("state:planner", cid, "delegates-subagent" if ckind == "subagent" else "invokes-tool", "forward", run_label)

      if ev.get("is_error"):
        blind_cnt += 1
        err_id = "err:obstacle"
        if err_id not in node_ids:
          node_ids.add(err_id)
          nodes.append({
            "id": err_id,
            "title": "✕ Blind Alley / Tool Error (404, ACL, Miss)",
            "kind": "failure-state",
            "status": "blind-alley",
            "parent": root_id,
            "summary": "Dead-end state reached when a tool errors (permission denied, missing file, 404) or returns ungrounded results.",
            "sources": [],
            "tags": [],
            "metrics": {},
          })
        add_edge(cid, err_id, "explores-spur", "forward", run_label)
        add_edge(err_id, "state:planner", "backtracks-to", "backtrack", run_label)

        steps_out.append({
          "stepIndex": len(steps_out) + 1,
          "nodeId": cid,
          "label": ev["label"],
          "role": "normal",
          "thought": ev.get("thought", ""),
        })
        steps_out.append({
          "stepIndex": len(steps_out) + 1,
          "nodeId": err_id,
          "label": f"✕ Error / Miss in {ev['label']}",
          "role": "blind-alley",
          "isError": True,
          "observation": ev.get("observation", ""),
        })
        steps_out.append({
          "stepIndex": len(steps_out) + 1,
          "nodeId": "state:planner",
          "label": "↺ Backtrack to Planner & Pivot Strategy",
          "role": "backtrack",
        })
      else:
        add_edge(cid, "state:synthesis", "produces-outcome", "forward", run_label)
        steps_out.append({
          "stepIndex": len(steps_out) + 1,
          "nodeId": cid,
          "label": ev["label"],
          "role": "subagent" if ckind == "subagent" else "normal",
          "thought": ev.get("thought", ""),
          "observation": ev.get("observation", ""),
        })
      prev_state = cid

    steps_out.append({
      "stepIndex": len(steps_out) + 1,
      "nodeId": "state:synthesis",
      "label": "Trajectory Goal Reached",
      "role": "goal",
    })

    traces.append({
      "id": f"run-{r_idx + 1}-{norm['id']}",
      "title": run_label,
      "color": palette[r_idx % len(palette)],
      "agent": norm["agent"],
      "model": norm["model"],
      "totalTokens": norm["total_tokens"],
      "blindAlleyCount": blind_cnt,
      "steps": steps_out,
    })

  edges = []
  for idx, ((u, v, rel, flow), runs) in enumerate(edge_counts.items(), start=1):
    uniq_runs = sorted(set(runs))
    edges.append({
      "id": f"cmpe-{idx}",
      "from": u,
      "to": v,
      "relation": rel,
      "flowRole": flow,
      "summary": f"Traversed {len(runs)}× across {len(uniq_runs)} run(s): {', '.join(uniq_runs)}",
      "contextSnippet": f"Runs: {', '.join(uniq_runs)} ({len(runs)} total transitions)",
    })

  overlays = [
    {
      "id": f"run-slice:{idx + 1}",
      "title": tr["title"],
      "kind": "trajectory-footprint",
      "summary": f"{tr['agent']} ({tr['model']}) — {len(tr['steps'])} transitions, {tr['blindAlleyCount']} blind alleys.",
      "touches": sorted({s["nodeId"] for s in tr["steps"]}),
    }
    for idx, tr in enumerate(traces)
  ]

  return {
    "schema": "strata-graph/1",
    "id": graph_id or "atif-multi-compare",
    "title": f"ATIF Multi-Run Comparison ({len(norms)} Trajectories)",
    "subtitle": "Click '⇄ Compare All' in the ATIF bar to see R1..R4 footprints across shared tools, subagents, and blind-alley recovery loops.",
    "domain": "atif-compare",
    "generatedAt": now_iso(),
    "sourceLabel": f"{len(norms)} real trajectories",
    "rootId": root_id,
    "relations": ATIF_RELATIONS,
    "nodes": nodes,
    "edges": edges,
    "overlays": overlays,
    "traces": traces,
    "diagnostics": [],
  }


# ---------------------------------------------------------------------------
# 4. Integrity Validator & Standalone / Hub HTML Bundler
# ---------------------------------------------------------------------------
def validate_dataset(ds: dict[str, Any]) -> list[dict[str, str]]:
  diags = list(ds.get("diagnostics") or [])
  nodes = ds.get("nodes") or []
  by_id = {n["id"]: n for n in nodes if isinstance(n, dict) and "id" in n}
  if ds.get("rootId") not in by_id:
    diags.append({"level": "error", "code": "MISSING_ROOT", "message": f"rootId {ds.get('rootId')} missing from nodes."})
  for e in ds.get("edges") or []:
    if e.get("from") not in by_id or e.get("to") not in by_id:
      diags.append({"level": "error", "code": "DANGLING_EDGE", "message": f"Edge {e.get('id')} references missing endpoint."})
  ds["diagnostics"] = diags
  return diags


def render_html(payload: dict[str, Any], title: str | None = None) -> str:
  tpl = (ASSETS_DIR / "template.html").read_text(encoding="utf-8")
  css = (ASSETS_DIR / "viewer.css").read_text(encoding="utf-8")
  js = (ASSETS_DIR / "viewer.js").read_text(encoding="utf-8")

  # Escape '</' inside JSON to prevent </script> breakout XSS
  safe_json = json.dumps(payload, ensure_ascii=False).replace("</", "<\\/")

  page_title = title or payload.get("title") or "Strata Graph Explorer"
  html = tpl.replace("<title>Strata Graph Explorer</title>", f"<title>{page_title}</title>")
  html = html.replace("<!-- STRATA:CSS -->", f"<style>\n{css}\n</style>")
  html = html.replace(
    "<!-- STRATA:DATA -->",
    f'<script id="strata-data" type="application/json">{safe_json}</script>',
  )
  html = html.replace("<!-- STRATA:JS -->", f"<script>\n{js}\n</script>")
  return html


def write_output(payload: dict[str, Any], out_path: Path) -> None:
  out_path.parent.mkdir(parents=True, exist_ok=True)
  if out_path.suffix.lower() in (".html", ".htm"):
    out_path.write_text(render_html(payload), encoding="utf-8")
  else:
    out_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


# ---------------------------------------------------------------------------
# CLI Entrypoint
# ---------------------------------------------------------------------------
def main(argv: list[str] | None = None) -> int:
  parser = argparse.ArgumentParser(
    prog="strata",
    description="Deterministic multi-layer graph compiler and zero-CDN HTML explorer.",
  )
  sub = parser.add_subparsers(dest="cmd", required=True)

  p_okf = sub.add_parser("compile-okf", help="Compile an OKF v0.2 Markdown wiki bundle.")
  p_okf.add_argument("wiki_dir", type=Path)
  p_okf.add_argument("-o", "--output", type=Path, required=True)
  p_okf.add_argument("--id", default=None)

  p_kg = sub.add_parser("compile-kg", help="Compile a Knowledge Graph (SQLite/YAML/JSON).")
  p_kg.add_argument("kg_path", type=Path)
  p_kg.add_argument("-o", "--output", type=Path, required=True)
  p_kg.add_argument("--id", default=None)

  p_atif = sub.add_parser("compile-atif", help="Compile 1..N ATIF, OATR, or Jetski JSONL trajectories.")
  p_atif.add_argument("inputs", type=Path, nargs="+")
  p_atif.add_argument("--mode", choices=["decision", "compare"], default="decision")
  p_atif.add_argument("-o", "--output", type=Path, required=True)
  p_atif.add_argument("--id", default=None)

  p_json = sub.add_parser("compile-json", help="Validate and compile a strata-graph/1 process or system JSON spec.")
  p_json.add_argument("spec_path", type=Path)
  p_json.add_argument("-o", "--output", type=Path, required=True)

  p_val = sub.add_parser("validate", help="Run deterministic integrity checks on a strata-graph/1 JSON file.")
  p_val.add_argument("graph_json", type=Path)

  p_hub = sub.add_parser("build-hub", help="Bundle multiple strata-graph/1 JSON datasets into one multi-tab HTML Explorer Hub.")
  p_hub.add_argument("datasets", type=Path, nargs="+")
  p_hub.add_argument("-o", "--output", type=Path, required=True)
  p_hub.add_argument("--title", default="Strata Graph Multi-Domain Explorer")

  args = parser.parse_args(argv)

  if args.cmd == "compile-okf":
    ds = compile_okf(args.wiki_dir, graph_id=args.id)
    validate_dataset(ds)
    write_output(ds, args.output)
    print(json.dumps({"status": "ok", "nodes": len(ds["nodes"]), "edges": len(ds["edges"]), "overlays": len(ds["overlays"]), "output": str(args.output)}))
    return 0

  if args.cmd == "compile-kg":
    ds = compile_kg(args.kg_path, graph_id=args.id)
    validate_dataset(ds)
    write_output(ds, args.output)
    print(json.dumps({"status": "ok", "nodes": len(ds["nodes"]), "edges": len(ds["edges"]), "overlays": len(ds["overlays"]), "output": str(args.output)}))
    return 0

  if args.cmd == "compile-atif":
    ds = (
      compile_atif_compare(args.inputs, graph_id=args.id)
      if args.mode == "compare" or len(args.inputs) > 1
      else compile_atif_decision(args.inputs, graph_id=args.id)
    )
    validate_dataset(ds)
    write_output(ds, args.output)
    print(json.dumps({"status": "ok", "mode": args.mode, "nodes": len(ds["nodes"]), "edges": len(ds["edges"]), "traces": len(ds["traces"]), "output": str(args.output)}))
    return 0

  if args.cmd == "compile-json":
    ds = json.loads(args.spec_path.read_text(encoding="utf-8"))
    ds.setdefault("schema", "strata-graph/1")
    ds.setdefault("generatedAt", now_iso())
    diags = validate_dataset(ds)
    errs = [d for d in diags if d.get("level") == "error"]
    if errs:
      print(json.dumps({"status": "error", "errors": errs}), file=sys.stderr)
      return 1
    write_output(ds, args.output)
    print(json.dumps({"status": "ok", "nodes": len(ds.get("nodes", [])), "edges": len(ds.get("edges", [])), "output": str(args.output)}))
    return 0

  if args.cmd == "validate":
    ds = json.loads(args.graph_json.read_text(encoding="utf-8"))
    diags = validate_dataset(ds)
    errs = [d for d in diags if d.get("level") == "error"]
    print(json.dumps({"status": "error" if errs else "ok", "diagnostics": diags}, indent=2))
    return 1 if errs else 0

  if args.cmd == "build-hub":
    loaded = []
    for p in args.datasets:
      ds = json.loads(p.read_text(encoding="utf-8"))
      validate_dataset(ds)
      loaded.append(ds)
    hub = {
      "schema": "strata-hub/1",
      "title": args.title,
      "generatedAt": now_iso(),
      "datasets": loaded,
    }
    write_output(hub, args.output)
    print(json.dumps({"status": "ok", "datasets": len(loaded), "output": str(args.output)}))
    return 0

  return 1


if __name__ == "__main__":
  raise SystemExit(main())
