#!/usr/bin/env python3
"""Strata Graph deterministic compiler, validator, and standalone HTML bundler.

Python 3.10+ standard library only. PyYAML is used when installed; otherwise a
small built-in parser reads OKF and KG frontmatter.

Subcommands:
  compile-okf  : OKF v0.2 Markdown wiki bundle -> graph
  compile-kg   : knowledge / entity graph from a SQLite pipeline.db or a YAML kg/ directory
  compile-atif : ATIF v1.x or Jetski transcript.jsonl trajectories
                 (--mode decision for one run, --mode compare for several)
  compile-json : validate and compile a hand-written strata-graph/1 JSON spec
  validate     : integrity checks on a strata-graph/1 JSON file
  build-hub    : bundle several strata-graph/1 JSON files into one multi-tab HTML explorer

An output path ending in .html or .htm writes the standalone explorer. A .json
path writes the strata-graph/1 JSON. Any other suffix is an error.

Independent implementation inspired by Adam Gospodarczyk's (@overment) limen picture (MIT).
"""

from __future__ import annotations

import argparse
import datetime
import importlib.util
import json
import math
import os
import re
import sqlite3
import sys
import time
from html import escape as html_escape
from pathlib import Path
from types import ModuleType
from typing import Any

_pyyaml: ModuleType | None = (
    importlib.import_module("yaml") if importlib.util.find_spec("yaml") else None
)

SCRIPT_DIR = Path(__file__).resolve().parent
ASSETS_DIR = SCRIPT_DIR.parent / "assets"


# ---------------------------------------------------------------------------
# YAML frontmatter parsing (PyYAML when installed, a small fallback otherwise)
# ---------------------------------------------------------------------------
def _json_safe(value: Any) -> Any:
    """Convert YAML-only scalars (dates, sets, bytes, NaN) so json.dumps accepts them."""
    if isinstance(value, dict):
        return {str(_json_safe(k)): _json_safe(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_safe(v) for v in value]
    if isinstance(value, (set, frozenset)):
        return sorted((_json_safe(v) for v in value), key=str)
    if isinstance(value, (datetime.datetime, datetime.date)):
        return value.isoformat().replace("+00:00", "Z")
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")
    if isinstance(value, float) and not math.isfinite(value):
        return str(value)
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    return str(value)


def _unquote(text: str) -> str:
    """Remove one matching pair of outer quotes."""
    text = text.strip()
    if len(text) >= 2 and text[0] == text[-1] and text[0] in ("'", '"'):
        return text[1:-1]
    return text


def _strip_comment(text: str) -> str:
    text = text.strip()
    if text[:1] in ("'", '"'):
        end = text.find(text[0], 1)
        if end > 0:
            return text[: end + 1] + re.sub(r"\s+#.*$", "", text[end + 1 :])
        return text
    return re.sub(r"(?:^|\s+)#.*$", "", text)


def _split_flow(inner: str) -> list[str]:
    """Split on commas that are outside quotes and nested brackets."""
    parts: list[str] = []
    depth = 0
    quote = ""
    cur = ""
    for ch in inner:
        if quote:
            quote = "" if ch == quote else quote
        elif ch in "'\"":
            quote = ch
        elif ch in "[{":
            depth += 1
        elif ch in "]}":
            depth -= 1
        elif ch == "," and depth == 0:
            parts.append(cur)
            cur = ""
            continue
        cur += ch
    parts.append(cur)
    return [p.strip() for p in parts if p.strip()]


def _flow_value(text: str) -> Any:
    parsed = _parse_flow(text)
    return parsed if parsed is not None else _unquote(text)


def _parse_flow(text: str) -> list[Any] | dict[str, Any] | None:
    """Parse a one-line [a, b] list or {k: v} mapping. Returns None for other text."""
    text = text.strip()
    if text.startswith("[") and text.endswith("]"):
        return [_flow_value(p) for p in _split_flow(text[1:-1])]
    if text.startswith("{") and text.endswith("}"):
        mapping: dict[str, Any] = {}
        for part in _split_flow(text[1:-1]):
            key, _, val = part.partition(":")
            mapping[_unquote(key)] = _flow_value(val)
        return mapping
    return None


_BLOCK_SCALAR_RE = re.compile(r"^[|>][+-]?$")
_MAP_ITEM_RE = re.compile(r"""^([^\s:#'"\[{][^:]*?):(?:\s+(.*))?$""")


def _indent_of(line: str) -> int:
    return len(line) - len(line.lstrip(" "))


def _skip_blank(lines: list[str], i: int) -> int:
    while i < len(lines) and (
        not lines[i].strip() or lines[i].lstrip().startswith("#")
    ):
        i += 1
    return i


def _parse_block_scalar(
    lines: list[str], i: int, parent_indent: int, indicator: str
) -> tuple[str, int]:
    """Read a `|` literal or `>` folded scalar whose body follows lines[i - 1]."""
    body: list[str] = []
    while i < len(lines) and (
        not lines[i].strip() or _indent_of(lines[i]) > parent_indent
    ):
        body.append(lines[i])
        i += 1
    while body and not body[-1].strip():
        body.pop()
    indents = [_indent_of(line) for line in body if line.strip()]
    margin = min(indents) if indents else 0
    content = [line[margin:].rstrip() for line in body]
    if indicator[0] == "|":
        text = "\n".join(content)
    else:
        paragraphs = "\n".join(content).split("\n\n")
        text = "\n".join(" ".join(p.split("\n")).strip() for p in paragraphs)
    return (text if indicator.endswith("-") else text + "\n"), i


def _parse_block(lines: list[str], i: int) -> tuple[Any, int]:
    text = lines[i].strip()
    if text == "-" or text.startswith("- "):
        return _parse_block_seq(lines, i, _indent_of(lines[i]))
    return _parse_block_map(lines, i, _indent_of(lines[i]))


def _parse_block_map(lines: list[str], i: int, indent: int) -> tuple[Any, int]:
    result: dict[str, Any] = {}
    while True:
        i = _skip_blank(lines, i)
        if i >= len(lines) or _indent_of(lines[i]) != indent:
            break
        m = _MAP_ITEM_RE.match(lines[i].strip())
        if not m:
            break
        key = _unquote(m.group(1))
        rest = _strip_comment(m.group(2) or "")
        i += 1
        if _BLOCK_SCALAR_RE.match(rest):
            value, i = _parse_block_scalar(lines, i, indent, rest)
        elif rest:
            value = _flow_value(rest)
        else:
            j = _skip_blank(lines, i)
            if j < len(lines) and (
                _indent_of(lines[j]) > indent
                or (_indent_of(lines[j]) == indent and lines[j].strip()[:2] == "- ")
            ):
                value, i = _parse_block(lines, j)
            else:
                value = None
        result[key] = value
    return result, i


def _parse_block_seq(lines: list[str], i: int, indent: int) -> tuple[Any, int]:
    items: list[Any] = []
    while True:
        i = _skip_blank(lines, i)
        if i >= len(lines) or _indent_of(lines[i]) != indent:
            break
        text = lines[i].strip()
        if text != "-" and not text.startswith("- "):
            break
        rest_raw = text[1:].strip()
        rest = _strip_comment(rest_raw)
        i += 1
        if not rest:
            j = _skip_blank(lines, i)
            if j < len(lines) and _indent_of(lines[j]) > indent:
                value, i = _parse_block(lines, j)
            else:
                value = None
        elif _BLOCK_SCALAR_RE.match(rest):
            value, i = _parse_block_scalar(lines, i, indent, rest)
        elif _MAP_ITEM_RE.match(rest_raw):
            # Treat "- k: v" as a mapping whose keys start after the dash.
            column = indent + (len(text) - len(text[1:].lstrip()))
            lines[i - 1] = " " * column + rest_raw
            value, i = _parse_block_map(lines, i - 1, column)
        else:
            value = _flow_value(rest)
        items.append(value)
    return items, i


class YamlParseError(ValueError):
    """PyYAML could not parse the text."""


def parse_yaml_safe(text: str) -> dict[str, Any]:
    """Parse frontmatter into JSON-safe values (dates become ISO strings).

    Without PyYAML a small indentation-based parser is used. It supports block
    mappings and sequences, one-line [a, b] and {k: v} collections, and | and >
    block scalars. Scalars other than quoted or plain text stay strings.
    """
    if _pyyaml is not None:
        try:
            loaded = _pyyaml.safe_load(text)
        except _pyyaml.YAMLError as exc:
            raise YamlParseError(" ".join(str(exc).split())) from exc
        return _json_safe(loaded) if isinstance(loaded, dict) else {}
    lines = text.splitlines()
    i = _skip_blank(lines, 0)
    if i >= len(lines) or lines[i].strip()[:2] == "- ":
        return {}
    parsed, _ = _parse_block_map(lines, i, _indent_of(lines[i]))
    return parsed if isinstance(parsed, dict) else {}


def split_frontmatter(
    md_text: str, errors: list[str] | None = None
) -> tuple[dict[str, Any], str]:
    """Split YAML frontmatter from the body.

    A YAML error is raised, or appended to `errors` when given (the frontmatter
    is then treated as empty and the body is still returned).
    """
    if not md_text.startswith("---"):
        return {}, md_text
    parts = md_text.split("\n---", 1)
    if len(parts) < 2:
        return {}, md_text
    fm_raw = parts[0][3:]
    body = parts[1].lstrip("\r\n")
    try:
        return parse_yaml_safe(fm_raw), body
    except YamlParseError as exc:
        if errors is None:
            raise
        errors.append(str(exc))
        return {}, body


def now_iso() -> str:
    """Current UTC time, or SOURCE_DATE_EPOCH when set to an integer."""
    epoch = os.environ.get("SOURCE_DATE_EPOCH", "")
    stamp = time.gmtime(int(epoch)) if epoch.isdigit() else time.gmtime()
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", stamp)


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


_FENCE_RE = re.compile(r"^ {0,3}(`{3,}|~{3,})")
_LIST_ITEM_RE = re.compile(r"^(?:[-*+]|\d+[.)])\s")


def _markdown_chunks(body: str) -> list[tuple[str, str]]:
    """Split a Markdown body into (heading, text) paragraphs and list items.

    Fenced code blocks are dropped, line breaks inside a paragraph are collapsed
    to spaces, and footnote definitions are skipped.
    """
    chunks: list[tuple[str, str]] = []
    heading = "Overview"
    lines: list[str] = []
    fence = ""

    def flush() -> None:
        text = " ".join(lines).strip()
        lines.clear()
        if text and not text.startswith("[^"):
            chunks.append((heading, text))

    for raw in body.splitlines():
        stripped = raw.strip()
        m = _FENCE_RE.match(raw)
        if fence:
            if m and m.group(1)[0] == fence[0] and len(m.group(1)) >= len(fence):
                fence = ""
            continue
        if m:
            flush()
            fence = m.group(1)
            continue
        if stripped.startswith("#"):
            flush()
            heading = stripped.lstrip("#").strip()
        elif not stripped:
            flush()
        else:
            if _LIST_ITEM_RE.match(stripped):
                flush()
            lines.append(stripped)
    flush()
    return chunks


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
    if re.search(r"\b(arch\w*|pattern\w*)\b", heading, re.IGNORECASE):
        return "composes-pattern"
    return "references"


def derive_okf_trust(fm: dict[str, Any]) -> dict[str, Any]:
    """Derive the OKF v0.2 trust tier (section 5.3) from `verified` only.

    unverified: no verifier. machine-confirmed: verifiers, none with a `human:`
    actor. human-reviewed: at least one `human:` verifier.
    """
    verified = fm.get("verified")
    if isinstance(verified, dict):
        verified = [verified]
    actors = [
        str(v["by"])
        for v in (verified if isinstance(verified, list) else [])
        if isinstance(v, dict) and v.get("by")
    ]
    if any(a.startswith("human:") for a in actors):
        tier = "human-reviewed"
    elif actors:
        tier = "machine-confirmed"
    else:
        tier = "unverified"
    generated = fm.get("generated")
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
    index_errors: list[str] = []
    if index_path.is_file():
        index_fm, _ = split_frontmatter(
            index_path.read_text(encoding="utf-8"), index_errors
        )

    title = str(index_fm.get("title") or wiki_root.name)
    subtitle = str(
        index_fm.get("description")
        or f"OKF v{index_fm.get('okf_version', '0.2')} knowledge bundle compiled into hierarchical sections, prose-grounded links, and co-citation slices."
    )
    root_id = (
        "okf/root"  # "/" never occurs in concept ids, so containers cannot collide
    )
    diagnostics: list[dict[str, str]] = []
    for err in index_errors:
        diagnostics.append(
            {
                "level": "warn",
                "code": "OKF_BAD_FRONTMATTER",
                "message": f"index.md frontmatter was skipped: {err}",
            }
        )

    nodes: list[dict[str, Any]] = [
        {
            "id": root_id,
            "title": title,
            "kind": "okf-bundle",
            "status": "ready",
            "parent": None,
            "summary": subtitle,
            "sources": [],
            "tags": [],
            "metrics": {"okf_version": str(index_fm.get("okf_version", "0.2"))},
        }
    ]

    # Discover sections and concept files
    md_files = sorted(wiki_root.rglob("*.md"))
    file_to_node_id: dict[Path, str] = {}
    file_meta: dict[Path, tuple[dict[str, Any], str, str]] = {}
    sections_seen: dict[str, str] = {}

    for fpath in md_files:
        rel = fpath.relative_to(wiki_root)
        if fpath.name in ("index.md", "log.md"):
            continue
        parts = rel.parts
        sec_slug = parts[0] if len(parts) > 1 else "general"
        if sec_slug not in sections_seen:
            sec_id = f"sec/{sec_slug}"
            sections_seen[sec_slug] = sec_id
            nodes.append(
                {
                    "id": sec_id,
                    "title": sec_slug.replace("-", " ").title(),
                    "kind": "section",
                    "status": "ready",
                    "parent": root_id,
                    "summary": f"OKF domain container for {sec_slug.replace('-', ' ')} concepts.",
                    "sources": [],
                    "tags": [sec_slug],
                    "metrics": {},
                }
            )

        fm_errors: list[str] = []
        fm, body = split_frontmatter(fpath.read_text(encoding="utf-8"), fm_errors)
        for err in fm_errors:
            diagnostics.append(
                {
                    "level": "warn",
                    "code": "OKF_BAD_FRONTMATTER",
                    "message": f"{rel.as_posix()} frontmatter was skipped: {err}",
                }
            )
        if not fm.get("type") and not fm_errors:
            diagnostics.append(
                {
                    "level": "warn",
                    "code": "OKF_MISSING_TYPE",
                    "message": f"{rel.as_posix()} is missing required OKF v0.2 frontmatter 'type'.",
                }
            )
        nid = rel.with_suffix("").as_posix().replace("/", ":")
        file_to_node_id[fpath.resolve()] = nid
        file_meta[fpath.resolve()] = (fm, body, sec_slug)

    # Track canonical sources across all concepts (checking 1:1 source bijection)
    source_touches: dict[str, dict[str, Any]] = {}
    url_to_source_ids: dict[str, set[str]] = {}
    tag_touches: dict[str, list[str]] = {}

    for fpath, nid in file_to_node_id.items():
        fm, body, sec_slug = file_meta[fpath]
        raw_status = str(fm.get("status") or "stable").lower()
        trust = derive_okf_trust(fm)
        status = (
            "deprecated"
            if raw_status == "deprecated"
            else "draft"
            if raw_status == "draft"
            else "ready"
        )

        node_sources: list[dict[str, Any]] = []
        for s in fm.get("sources") or []:
            if not isinstance(s, dict):
                continue
            sid = str(s.get("id") or s.get("resource") or "")
            surl = str(s.get("resource") or s.get("url") or "")
            if not sid:
                continue
            node_sources.append(
                {
                    "id": sid,
                    "title": str(s.get("title") or sid),
                    "url": surl or None,
                    "author": s.get("author"),
                }
            )
            if surl:
                url_to_source_ids.setdefault(surl, set()).add(sid)
            entry = source_touches.setdefault(
                sid,
                {
                    "id": f"src:{sid}",
                    "title": str(s.get("title") or sid),
                    "kind": "co-citation",
                    "url": surl or None,
                    "summary": f"Canonical OKF provenance source ({surl or sid})",
                    "touches": [],
                },
            )
            if nid not in entry["touches"]:
                entry["touches"].append(nid)

        raw_tags = fm.get("tags") or []
        if not isinstance(raw_tags, list):
            raw_tags = [raw_tags]
        tags = [str(t) for t in raw_tags if t]
        for t in tags:
            if t.lower() != sec_slug.lower():
                tag_touches.setdefault(t, []).append(nid)

        first_para = ""
        for line in body.splitlines():
            sline = line.strip()
            if (
                sline
                and not sline.startswith("#")
                and not sline.startswith("[^")
                and not sline.startswith(">")
            ):
                first_para = re.sub(r"\[\^[^\]]+\]", "", sline)[:280]
                break

        nodes.append(
            {
                "id": nid,
                "title": str(fm.get("title") or fpath.stem.replace("-", " ").title()),
                "kind": str(fm.get("type") or "concept"),
                "status": status,
                "parent": sections_seen[sec_slug],
                "summary": str(fm.get("description") or first_para),
                "body": first_para
                if fm.get("description") and first_para != fm.get("description")
                else "",
                "url": fm.get("resource"),
                "trust": trust,
                "sources": node_sources,
                "tags": tags,
                "metrics": {
                    "sources": len(node_sources),
                    "tags": len(tags),
                },
            }
        )

    # Check 1:1 source URL bijection
    for surl, sids in sorted(url_to_source_ids.items()):
        if len(sids) > 1:
            diagnostics.append(
                {
                    "level": "warn",
                    "code": "SOURCE_BIJECTION_WARN",
                    "message": f"Resource {surl} is cited under multiple source IDs: {', '.join(sorted(sids))}",
                }
            )

    # Extract internal Markdown links with heading + sentence context
    link_re = re.compile(r"\[([^\]]+)\]\(([^)\s]+\.md(?:#[^)]+)?)\)")
    edges: list[dict[str, Any]] = []
    seen_edges: set[tuple[str, str, str]] = set()
    edge_seq = 0

    for fpath, src_id in file_to_node_id.items():
        _, body, src_sec = file_meta[fpath]
        for cur_heading, chunk in _markdown_chunks(body):
            for match in link_re.finditer(chunk):
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
                    diagnostics.append(
                        {
                            "level": "warn",
                            "code": "PATH_OUTSIDE_BUNDLE",
                            "message": f"Blocked link escaping OKF root in {fpath.name}: {raw_target}",
                        }
                    )
                    continue

                dst_id = file_to_node_id.get(target_path)
                if not dst_id:
                    if target_path.name not in ("index.md", "log.md"):
                        diagnostics.append(
                            {
                                "level": "warn",
                                "code": "BROKEN_MD_LINK",
                                "message": f"{fpath.relative_to(wiki_root)} links to missing concept '{raw_target}'.",
                            }
                        )
                    continue
                if dst_id == src_id:
                    continue

                _, _, dst_sec = file_meta[target_path]
                rel = classify_okf_relation(src_sec, dst_sec, cur_heading)
                dedup_key = (src_id, dst_id, rel)
                if dedup_key in seen_edges:
                    continue
                seen_edges.add(dedup_key)

                clean_snippet = re.sub(r"\[\^[^\]]+\]", "", chunk)
                clean_snippet = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", clean_snippet)
                clean_snippet = clean_snippet.lstrip("-* ").strip()

                edge_seq += 1
                edges.append(
                    {
                        "id": f"e{edge_seq}",
                        "from": src_id,
                        "to": dst_id,
                        "relation": rel,
                        "flowRole": "forward",
                        "summary": f"[{cur_heading}] {anchor_text}",
                        "contextSnippet": f"§ {cur_heading}: {clean_snippet[:220]}",
                    }
                )

    # Build overlays: multi-concept co-citations + shared themes
    overlays: list[dict[str, Any]] = []
    for sid, entry in sorted(
        source_touches.items(), key=lambda kv: -len(kv[1]["touches"])
    ):
        if len(entry["touches"]) >= 2:
            overlays.append(entry)

    for tag, nids in sorted(tag_touches.items(), key=lambda kv: -len(kv[1])):
        uniq = sorted(set(nids))
        if 3 <= len(uniq) <= max(12, len(file_to_node_id) // 2):
            overlays.append(
                {
                    "id": f"tag:{tag}",
                    "title": f"#{tag}",
                    "kind": "theme",
                    "summary": f"Cross-cutting OKF tag shared across {len(uniq)} concepts.",
                    "touches": uniq,
                }
            )

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
    if any(
        k in p for k in ("develop", "creat", "author", "maintain", "built", "propos")
    ):
        return "develops"
    if any(
        k in p for k in ("part-of", "member", "belong", "host", "contain", "subproject")
    ):
        return "part-of"
    if any(k in p for k in ("support", "implement", "provid", "enabl", "defin")):
        return "supports"
    if any(k in p for k in ("donat", "govern", "steward", "sponsor", "standardiz")):
        return "governs"
    if any(
        k in p for k in ("align", "referenc", "inspir", "relat", "extend", "compat")
    ):
        return "aligns-with"
    return "uses"


def map_kg_container(raw_type: str) -> tuple[str, str]:
    t = raw_type.lower()
    if (
        "org" in t
        or "company" in t
        or "foundation" in t
        or "consortium" in t
        or "group" in t
    ):
        return "grp:organizations", "Organizations & Foundations"
    if "proto" in t or "spec" in t or "standard" in t:
        return "grp:protocols", "Protocols & Standards"
    if "person" in t or "human" in t or "author" in t or "individual" in t:
        return "grp:people", "People & Contributors"
    if "capab" in t or "concept" in t or "pattern" in t or "arch" in t or "risk" in t:
        return "grp:capabilities", "Capabilities & Concepts"
    return "grp:projects", "Projects, SDKs & Tools"


def _singular(name: str) -> str:
    """Singular form of a directory name such as entities, companies, or people."""
    if name.endswith("ies"):
        return name[:-3] + "y"
    if name.endswith("sses"):
        return name[:-2]
    if name.endswith("s") and not name.endswith("ss"):
        return name[:-1]
    return name


KG_SQLITE_SCHEMA = (
    "tables sources(id, uri, title), "
    "entities(entity_id, name, kind, type, description, status, source_id, merged_into), "
    "edges(source_entity_id, target_entity_id, edge_type, confidence)"
)


class KGSchemaError(ValueError):
    """The input is missing, empty, or not in a layout compile_kg can read."""


def compile_kg(kg_path: Path, graph_id: str | None = None) -> dict[str, Any]:
    target = kg_path.resolve()
    if not target.exists():
        raise KGSchemaError(f"{kg_path} does not exist.")
    db_file = target if target.is_file() else (target / "pipeline.db")
    yaml_dir = target / "kg" if (target / "kg").is_dir() else target
    if not (
        db_file.is_file()
        or (yaml_dir / "relations.yaml").is_file()
        or (yaml_dir / "timeline.yaml").is_file()
    ):
        raise KGSchemaError(
            f"{kg_path} has no pipeline.db, relations.yaml, or timeline.yaml."
        )

    kg_name = target.stem if target.is_file() else target.name
    root_id = "kg:root"
    nodes: list[dict[str, Any]] = [
        {
            "id": root_id,
            "title": f"Knowledge graph: {kg_name}",
            "kind": "knowledge-graph",
            "status": "ready",
            "parent": None,
            "summary": "Knowledge graph of typed entities and the relations between them.",
            "sources": [],
            "tags": [],
            "metrics": {},
        }
    ]
    containers: dict[str, str] = {}
    entity_ids: set[str] = set()
    slug_to_eid: dict[str, str] = {}
    edges: list[dict[str, Any]] = []
    diagnostics: list[dict[str, str]] = []
    source_overlays: dict[str, dict[str, Any]] = {}

    def ensure_container(cid: str, ctitle: str) -> str:
        if cid not in containers:
            containers[cid] = ctitle
            nodes.append(
                {
                    "id": cid,
                    "title": ctitle,
                    "kind": "entity-domain",
                    "status": "ready",
                    "parent": root_id,
                    "summary": f"Entity domain grouping for {ctitle}.",
                    "sources": [],
                    "tags": [],
                    "metrics": {},
                }
            )
        return cid

    # 1. Read SQLite pipeline.db if present (read-only URI)
    if db_file.is_file():
        conn = sqlite3.connect(f"{db_file.resolve().as_uri()}?mode=ro", uri=True)
        try:
            src_lookup: dict[str, tuple[str, str]] = {}
            for row in conn.execute("SELECT id, uri, title FROM sources"):
                if row[0] is None:
                    continue
                src_lookup[str(row[0])] = (
                    str(row[1] or ""),
                    str(row[2] or f"Source {row[0]}"),
                )

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
                if sid is not None and str(sid) in src_lookup:
                    s_uri, s_title = src_lookup[str(sid)]
                    ent_sources.append(
                        {"id": f"s-{sid}", "title": s_title, "url": s_uri}
                    )
                    ov = source_overlays.setdefault(
                        f"s-{sid}",
                        {
                            "id": f"src:s-{sid}",
                            "title": s_title[:58],
                            "kind": "source-doc",
                            "url": s_uri,
                            "summary": f"Extracted knowledge-graph source document ({s_uri})",
                            "touches": [],
                        },
                    )
                    if eid not in ov["touches"]:
                        ov["touches"].append(eid)

                nodes.append(
                    {
                        "id": eid,
                        "title": str(name or eid),
                        "kind": str(etype or kind or "entity").lower(),
                        "status": "ready" if str(status) == "approved" else "draft",
                        "parent": cid,
                        "summary": str(desc or ""),
                        "sources": ent_sources,
                        "tags": [str(kind)] if kind else [],
                        "metrics": {"type": str(etype or kind or "")},
                    }
                )

            edge_seq = 0
            seen_pairs: set[tuple[str, str, str]] = set()
            for row in conn.execute(
                "SELECT source_entity_id, target_entity_id, edge_type, confidence FROM edges"
            ):
                u, v, etype, conf = (
                    str(row[0]),
                    str(row[1]),
                    str(row[2] or "USES"),
                    row[3],
                )
                if u not in entity_ids or v not in entity_ids or u == v:
                    continue
                rel = map_kg_predicate(etype)
                if (u, v, rel) in seen_pairs:
                    continue
                seen_pairs.add((u, v, rel))
                edge_seq += 1
                edges.append(
                    {
                        "id": f"kge-{edge_seq}",
                        "from": u,
                        "to": v,
                        "relation": rel,
                        "flowRole": "forward",
                        "summary": f"{etype} (confidence: {conf})",
                        "contextSnippet": f"Predicate: {etype}",
                    }
                )
        except sqlite3.Error as exc:
            raise KGSchemaError(
                f"{db_file} is not a compatible knowledge-graph database ({exc}). "
                f"Expected {KG_SQLITE_SCHEMA}. See references/schema.md."
            ) from exc
        finally:
            conn.close()

    def resolve_or_add(slug_raw: str) -> str:
        s_low = slug_raw.lower()
        if s_low in slug_to_eid:
            return slug_to_eid[s_low]
        # Check YAML entity file if available. A slug is only a file name when it
        # has no path separators, "..", or glob characters, and the match must
        # stay inside entities/.
        entities_dir = yaml_dir / "entities"
        lookup_ok = entities_dir.is_dir() and not (
            re.search(r"[/\\*?\[\]]", slug_raw) or ".." in slug_raw
        )
        for cand in (
            [
                c
                for c in entities_dir.rglob(f"{slug_raw}.yaml")
                if c.resolve().is_relative_to(entities_dir.resolve())
            ]
            if lookup_ok
            else []
        ):
            efm = parse_yaml_safe(cand.read_text(encoding="utf-8"))
            etype = str(efm.get("type") or _singular(cand.parent.name))
            cid, ctitle = map_kg_container(etype)
            ensure_container(cid, ctitle)
            eid_new = f"{etype.lower()}:{slug_raw}"
            entity_ids.add(eid_new)
            slug_to_eid[s_low] = eid_new
            nodes.append(
                {
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
                }
            )
            return eid_new
        cid, ctitle = map_kg_container("project")
        ensure_container(cid, ctitle)
        eid_new = f"entity:{slug_raw}"
        entity_ids.add(eid_new)
        slug_to_eid[s_low] = eid_new
        nodes.append(
            {
                "id": eid_new,
                "title": slug_raw.replace("-", " ").upper()
                if len(slug_raw) <= 4
                else slug_raw.replace("-", " ").title(),
                "kind": "entity",
                "status": "ready",
                "parent": cid,
                "summary": "Curated entity from the YAML files.",
                "sources": [],
                "tags": [],
                "metrics": {},
            }
        )
        return eid_new

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

            u_id = resolve_or_add(subj)
            v_id = resolve_or_add(obj)
            if u_id != v_id:
                rel = map_kg_predicate(pred)
                note = str(item.get("note") or "")
                edges.append(
                    {
                        "id": f"yaml-rel-{len(edges) + 1}",
                        "from": u_id,
                        "to": v_id,
                        "relation": rel,
                        "flowRole": "forward",
                        "summary": f"{pred}" + (f" — {note}" if note else ""),
                        "contextSnippet": f"Curated relation: {subj} {pred} {obj}"
                        + (f" ({note})" if note else ""),
                    }
                )

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
                actor_slug = str(actor).strip()
                eid = resolve_or_add(actor_slug) if actor_slug else None
                if eid:
                    step_idx += 1
                    t_steps.append(
                        {
                            "stepIndex": step_idx,
                            "nodeId": eid,
                            "label": f"[{ev.get('date', '')}] {ev.get('title', '')} ({actor})",
                            "role": "normal",
                            "observation": str(ev.get("description") or "").strip()[
                                :220
                            ],
                        }
                    )
        if t_steps:
            traces.append(
                {
                    "id": "kg-timeline",
                    "title": "Timeline events",
                    "color": "#34d399",
                    "steps": t_steps,
                }
            )

    if not entity_ids:
        raise KGSchemaError(
            f"{kg_path} contains no entities. Check the database rows, "
            "relations.yaml subjects and objects, or timeline.yaml actors."
        )

    overlays = [
        ov
        for ov in sorted(source_overlays.values(), key=lambda x: -len(x["touches"]))
        if len(ov["touches"]) >= 2
    ][:18]

    return {
        "schema": "strata-graph/1",
        "id": graph_id or f"kg-{kg_name}",
        "title": f"Knowledge graph: {kg_name}",
        "subtitle": f"{len(entity_ids)} entities with {len(edges)} typed relations.",
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
# 3. ATIF / Jetski Trajectory Adapter (Decision Spine + Multi-Run Compare)
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
    """Parse ATIF v1.x JSON or Jetski transcript.jsonl into a unified Trajectory dict."""
    text = path.read_text(encoding="utf-8")

    # Format A: JSONL (Jetski transcript.jsonl)
    if path.suffix == ".jsonl":
        raw_lines = [
            row
            for row in (json.loads(line) for line in text.splitlines() if line.strip())
            if isinstance(row, dict)
        ]
        return _normalize_jetski_jsonl(path, raw_lines)

    doc = json.loads(text)

    # Format B: ATIF v1.x / v1.7 Document ({"schema_version": "ATIF-...", "steps": [...]})
    if isinstance(doc, dict) and "steps" in doc:
        return _normalize_atif_doc(path, doc)

    raise ValueError(f"Unrecognized trajectory schema in {path}")


def _dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _to_int(value: Any) -> int:
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return 0


def _tool_args(raw: Any) -> dict[str, Any]:
    """Tool arguments as a dict. JSON-encoded strings are decoded when possible."""
    if isinstance(raw, dict):
        return raw
    if isinstance(raw, str):
        try:
            decoded = json.loads(raw)
        except json.JSONDecodeError:
            decoded = None
        return decoded if isinstance(decoded, dict) else {"raw": raw}
    return {"raw": raw} if raw else {}


def _normalize_atif_doc(path: Path, doc: dict[str, Any]) -> dict[str, Any]:
    tid = str(doc.get("trajectory_id") or doc.get("session_id") or path.stem)
    agent_raw = doc.get("agent")
    agent_obj = _dict(agent_raw)
    agent_name = str(
        agent_obj.get("name")
        or (agent_raw if agent_raw and isinstance(agent_raw, str) else "agent")
    )
    model_name = str(agent_obj.get("model_name") or "")
    sub_by_id = {
        str(sub.get("trajectory_id") or sub.get("session_id") or f"sub-{i}"): sub
        for i, sub in enumerate(_as_list(doc.get("subagent_trajectories")))
        if isinstance(sub, dict)
    }

    events: list[dict[str, Any]] = []
    for stp in _as_list(doc.get("steps")):
        if not isinstance(stp, dict):
            continue
        src = str(stp.get("source") or "agent").lower()
        msg_raw = stp.get("message")
        if isinstance(msg_raw, list):
            msg = " ".join(
                str(p.get("text") or "") for p in msg_raw if isinstance(p, dict)
            ).strip()
        else:
            msg = str(msg_raw or "").strip()
        thought = str(stp.get("reasoning_content") or "").strip()

        obs_by_call: dict[str, dict[str, Any]] = {}
        for res in _as_list(_dict(stp.get("observation")).get("results")):
            if isinstance(res, dict) and res.get("source_call_id"):
                obs_by_call[str(res["source_call_id"])] = res

        tcalls = [tc for tc in _as_list(stp.get("tool_calls")) if isinstance(tc, dict)]
        metrics = _dict(stp.get("metrics"))
        tok = _to_int(metrics.get("prompt_tokens")) + _to_int(
            metrics.get("completion_tokens")
        )

        if not tcalls:
            events.append(
                {
                    "source": src,
                    "tool": None,
                    "label": f"{src.title()}: {msg[:54]}"
                    if msg
                    else f"{src.title()} turn",
                    "thought": thought,
                    "observation": msg,
                    "is_error": False,
                    "tokens": tok,
                    "subagent": None,
                }
            )
        else:
            for tc_idx, tc in enumerate(tcalls):
                cid = str(tc.get("tool_call_id") or "")
                fn = str(tc.get("function_name") or "tool")
                args = _tool_args(tc.get("arguments"))
                res = obs_by_call.get(cid, {})
                res_content = res.get("content")
                if isinstance(res_content, list):
                    obs_txt = " ".join(
                        str(x.get("text") or "")
                        for x in res_content
                        if isinstance(x, dict)
                    )
                else:
                    obs_txt = str(res_content or "")
                extra = _dict(res.get("extra"))
                tc_extra = _dict(tc.get("extra"))
                is_err = bool(
                    extra.get("is_error")
                    or tc_extra.get("exit_code", 0) not in (0, None, "0")
                    or "error" in str(extra.get("status", "")).lower()
                )
                sub_doc = None
                for sref in _as_list(res.get("subagent_trajectory_ref")):
                    ref_id = str(_dict(sref).get("trajectory_id") or "")
                    if ref_id in sub_by_id:
                        sub_doc = _normalize_atif_doc(path, sub_by_id[ref_id])
                arg_preview = ", ".join(
                    f"{k}={str(v)[:28]}" for k, v in list(args.items())[:2]
                )
                events.append(
                    {
                        "source": src,
                        "tool": fn,
                        "label": f"{fn}({arg_preview})" if arg_preview else fn,
                        "thought": thought or msg,
                        "observation": obs_txt[:240],
                        "is_error": is_err,
                        # The step's tokens are counted once, on its first call.
                        "tokens": tok if tc_idx == 0 else 0,
                        "subagent": sub_doc,
                    }
                )

    fm = _dict(doc.get("final_metrics"))
    total_tok = _to_int(fm.get("total_prompt_tokens")) + _to_int(
        fm.get("total_completion_tokens")
    )
    return {
        "id": tid,
        "title": f"{agent_name}: {doc.get('notes') or tid}",
        "agent": agent_name,
        "model": model_name,
        "total_tokens": total_tok or sum(e["tokens"] for e in events),
        "events": events,
    }


def _jetski_step_failed(step: dict[str, Any]) -> bool:
    """True only when the transcript step itself reports a failure."""
    if str(step.get("status") or "").upper() in ("ERROR", "FAILED"):
        return True
    if step.get("error"):
        return True
    exit_code = step.get("exit_code", step.get("exitCode"))
    return exit_code not in (0, None, "0")


def _normalize_jetski_jsonl(
    path: Path, raw_steps: list[dict[str, Any]]
) -> dict[str, Any]:
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
                events.append(
                    {
                        "source": "user",
                        "tool": None,
                        "label": f"User Goal: {raw_c[:56]}…",
                        "thought": "",
                        "observation": raw_c[:260],
                        "is_error": False,
                        "tokens": 0,
                        "subagent": None,
                    }
                )
            i += 1
            continue

        if stype == "PLANNER_RESPONSE":
            tcalls = [
                tc for tc in _as_list(s.get("tool_calls")) if isinstance(tc, dict)
            ]
            thought = str(s.get("thinking") or "").strip()[:240]
            msg = str(s.get("content") or "").strip()

            # Collect immediately following GENERIC tool outputs
            outputs: list[dict[str, Any]] = []
            j = i + 1
            while j < n and raw_steps[j].get("type") == "GENERIC":
                outputs.append(raw_steps[j])
                j += 1

            if not tcalls and msg:
                events.append(
                    {
                        "source": "agent",
                        "tool": None,
                        "label": f"Agent Update: {msg[:52]}…",
                        "thought": thought,
                        "observation": msg[:240],
                        "is_error": False,
                        "tokens": 0,
                        "subagent": None,
                    }
                )
            elif tcalls:
                # Group repeated calls to the same tool into one turn; failed calls stay separate
                grouped_by_tool: dict[str, dict[str, Any]] = {}
                for idx_tc, tc in enumerate(tcalls):
                    fn = str(tc.get("name") or tc.get("tool_name") or "tool")
                    args = _tool_args(tc.get("arguments") or tc.get("args"))
                    out_step = outputs[idx_tc] if idx_tc < len(outputs) else {}
                    out_txt = str(out_step.get("content") or "")
                    out_err = _jetski_step_failed(out_step)
                    arg_preview = ", ".join(
                        f"{k}={str(v)[:28]}" for k, v in list(args.items())[:1]
                    )
                    key = f"{fn}:error:{idx_tc}" if out_err else fn
                    label = f"{fn}({arg_preview})" if arg_preview else fn

                    bucket = grouped_by_tool.setdefault(
                        key,
                        {
                            "source": "agent",
                            "tool": fn,
                            "label": label,
                            "count": 0,
                            "thought": thought,
                            "observation": out_txt[:240],
                            "is_error": False,
                            "tokens": 0,
                            "subagent": None,
                        },
                    )
                    bucket["count"] += 1
                    if out_err:
                        bucket["is_error"] = True
                        bucket["observation"] = out_txt[:240]

                for b in grouped_by_tool.values():
                    if b["count"] > 1:
                        b["label"] = f"{b['tool']} ×{b['count']} batch"
                    events.append(b)
            i = j
            continue

        i += 1

    # Merge consecutive successful turns that use the same tool and label
    compact: list[dict[str, Any]] = []
    for ev in events:
        ev.setdefault("count", 1)
        ev["base_label"] = ev["label"].split(" ×")[0]
        prev = compact[-1] if compact else None
        if (
            prev
            and prev["tool"] == ev["tool"]
            and prev["base_label"] == ev["base_label"]
            and not ev["is_error"]
            and not prev["is_error"]
        ):
            prev["count"] += ev["count"]
            if prev["tool"]:
                prev["label"] = f"{prev['tool']} ×{prev['count']} batch"
            continue
        compact.append(ev)

    model = next((str(s["model"]) for s in raw_steps if s.get("model")), "")
    session_id = (
        path.parent.parent.parent.name[:12]
        if ".system_generated" in str(path)
        else path.stem
    )
    return {
        "id": session_id,
        "title": f"Jetski transcript {session_id}",
        "agent": "Jetski",
        "model": model,
        "total_tokens": 0,
        "events": compact,
    }


def compile_atif_decision(
    traj_paths: list[Path], graph_id: str | None = None
) -> dict[str, Any]:
    """Compile a trajectory into a hierarchical Phase/Turn Decision Graph with Blind Alleys & ↺ Backtracks."""
    norm = normalize_trajectory_file(traj_paths[0].resolve())
    root_id = "atif:root"
    nodes: list[dict[str, Any]] = [
        {
            "id": root_id,
            "title": norm["title"],
            "kind": "trajectory",
            "status": "ready",
            "parent": None,
            "summary": f"Agent trajectory ({norm['agent']}) showing forward reasoning trunk, blind-alley spurs (✕), explicit backtrack pivots (↺), and nested subagents.",
            "sources": [],
            "tags": [norm["agent"]],
            "metrics": {
                "agent": norm["agent"],
                "model": norm["model"],
                "turns": len(norm["events"]),
            },
        }
    ]

    edges: list[dict[str, Any]] = []
    trace_steps: list[dict[str, Any]] = []
    tool_touches: dict[str, list[str]] = {}
    diagnostics: list[dict[str, str]] = []

    # Group turns into logical lifecycle phases
    phases = [
        ("phase:orient", "1. Opening turns"),
        ("phase:search", "2. Middle turns"),
        ("phase:verify", "3. Closing turns"),
    ]
    for pid, ptitle in phases:
        nodes.append(
            {
                "id": pid,
                "title": ptitle,
                "kind": "phase",
                "status": "ready",
                "parent": root_id,
                "summary": f"Trajectory phase: {ptitle}",
                "sources": [],
                "tags": [],
                "metrics": {},
            }
        )

    evs = norm["events"]
    total_evs = max(1, len(evs))
    last_trunk_id: str | None = None
    pending_blind_ids: list[str] = []
    blind_count = 0
    backtrack_count = 0
    step_seq = 0

    for idx, ev in enumerate(evs):
        nid = f"turn:{idx + 1}"
        ratio = idx / total_evs
        phase_id = (
            phases[0][0]
            if ratio < 0.28
            else phases[1][0]
            if ratio < 0.68
            else phases[2][0]
        )

        is_blind = bool(ev.get("is_error"))
        has_sub = ev.get("subagent") is not None
        status = "blind-alley" if is_blind else "subagent" if has_sub else "ready"

        nodes.append(
            {
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
            }
        )

        if ev.get("tool"):
            tool_touches.setdefault(ev["tool"], []).append(nid)

        # Nested subagent children!
        if has_sub:
            sub = ev["subagent"]
            prev_sub_id = None
            for s_idx, sev in enumerate(sub.get("events") or []):
                snid = f"{nid}:sub:{s_idx + 1}"
                nodes.append(
                    {
                        "id": snid,
                        "title": f"Sub {s_idx + 1}: {sev['label']}",
                        "kind": sev.get("tool") or "subagent-step",
                        "status": "error" if sev.get("is_error") else "ready",
                        "parent": nid,
                        "summary": sev.get("observation") or sev["label"],
                        "sources": [],
                        "tags": [],
                        "metrics": {"subagent": sub.get("title", "subagent")},
                    }
                )
                if prev_sub_id:
                    edges.append(
                        {
                            "id": f"sube-{snid}",
                            "from": prev_sub_id,
                            "to": snid,
                            "relation": "advances-to",
                            "flowRole": "forward",
                            "summary": "Subagent sequential step",
                        }
                    )
                prev_sub_id = snid

        step_seq += 1
        if is_blind:
            blind_count += 1
            anchor = last_trunk_id
            if anchor:
                edges.append(
                    {
                        "id": f"spur-{idx + 1}",
                        "from": anchor,
                        "to": nid,
                        "relation": "explores-spur",
                        "flowRole": "forward",
                        "summary": f"Exploratory attempt hit obstacle: {ev['label']}",
                        "contextSnippet": ev.get("observation", "")[:180],
                    }
                )
            pending_blind_ids.append(nid)
            trace_steps.append(
                {
                    "stepIndex": step_seq,
                    "nodeId": nid,
                    "label": f"✕ Blind Alley — {ev['label']}",
                    "role": "blind-alley",
                    "isError": True,
                    "thought": ev.get("thought", ""),
                    "observation": ev.get("observation", ""),
                }
            )
            diagnostics.append(
                {
                    "level": "info",
                    "code": "BLIND_ALLEY_DETECTED",
                    "message": f"Turn T{idx + 1} ({ev['label']}) classified as blind alley.",
                }
            )
        else:
            # Recovering from 1 or more blind alleys -> emit explicit ↺ backtrack arc(s) + revisit anchor!
            if pending_blind_ids:
                pivot_target = last_trunk_id or nid
                for bid in pending_blind_ids:
                    backtrack_count += 1
                    edges.append(
                        {
                            "id": f"bt-{bid}->{pivot_target}",
                            "from": bid,
                            "to": pivot_target,
                            "relation": "backtracks-to",
                            "flowRole": "backtrack",
                            "summary": f"↺ Backtracked from dead-end {bid} to pivot strategy",
                            "contextSnippet": f"Agent abandoned {bid} and pivoted to {ev['label']}.",
                        }
                    )
                if last_trunk_id:
                    step_seq += 1
                    trace_steps.append(
                        {
                            "stepIndex": step_seq,
                            "nodeId": last_trunk_id,
                            "label": f"↺ Backtrack & Re-evaluate at {last_trunk_id}",
                            "role": "backtrack",
                            "thought": f"Pivoting away from {len(pending_blind_ids)} unproductive spur(s) toward {ev['label']}.",
                        }
                    )
                pending_blind_ids.clear()

            if last_trunk_id:
                edges.append(
                    {
                        "id": f"trk-{last_trunk_id}->{nid}",
                        "from": last_trunk_id,
                        "to": nid,
                        "relation": "delegates-subagent" if has_sub else "advances-to",
                        "flowRole": "forward",
                        "summary": f"Advances along winning trunk to {ev['label']}",
                    }
                )
            last_trunk_id = nid

            step_seq += 1
            trace_steps.append(
                {
                    "stepIndex": step_seq,
                    "nodeId": nid,
                    "label": ev["label"],
                    "role": "subagent"
                    if has_sub
                    else "goal"
                    if idx == len(evs) - 1
                    else "normal",
                    "thought": ev.get("thought", ""),
                    "observation": ev.get("observation", ""),
                }
            )

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
        "subtitle": f"{len(evs)} semantic turns · {blind_count} blind alleys (✕), {backtrack_count} ↺ backtrack return arcs.",
        "domain": "atif-trajectory",
        "generatedAt": now_iso(),
        "sourceLabel": traj_paths[0].name,
        "rootId": root_id,
        "relations": ATIF_RELATIONS,
        "nodes": nodes,
        "edges": edges,
        "overlays": overlays,
        "traces": [
            {
                "id": norm["id"],
                "title": norm["title"],
                "color": "#60a5fa",
                "agent": norm["agent"],
                "model": norm["model"],
                "totalTokens": norm["total_tokens"],
                "blindAlleyCount": blind_count,
                "steps": trace_steps,
            }
        ],
        "diagnostics": diagnostics,
    }


def compile_atif_compare(
    traj_paths: list[Path], graph_id: str | None = None
) -> dict[str, Any]:
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
            "summary": "Shared capability, tool, subagent, and failure-mode graph comparing multiple real ATIF / Jetski agent trajectories side-by-side.",
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
            "title": "Goal reached",
            "kind": "stage",
            "status": "ready",
            "parent": root_id,
            "summary": "Reached only by runs whose final step succeeded.",
            "sources": [],
            "tags": [],
            "metrics": {},
        },
    ]

    node_ids = {"state:intake", "state:planner", "state:synthesis"}
    edge_counts: dict[tuple[str, str, str, str], list[str]] = {}
    traces: list[dict[str, Any]] = []
    palette = ["#60a5fa", "#34d399", "#f472b6", "#fbbf24", "#a78bfa", "#22d3ee"]

    def canonical_tool_bucket(tool_name: str | None) -> tuple[str, str, str]:
        if not tool_name:
            return ("state:planner", "Planner & Hypothesis Router", "stage")
        tl = tool_name.lower()
        if "subagent" in tl or tl in ("task", "invoke_agent", "invoke_subagent"):
            return (
                "cap:subagent",
                "Subagent Delegation (task / invoke_agent)",
                "subagent",
            )
        if tl == "read_file":
            return ("cap:file_inspect", "File inspection (read_file)", "tool")
        if tl in ("write_file", "edit_file"):
            return (
                "cap:artifact_write",
                "File authoring (write_file / edit_file)",
                "tool",
            )
        if tl in ("bash", "run_command"):
            return ("cap:shell_exec", "Shell execution (bash / run_command)", "tool")
        return (f"cap:{tl}", f"Tool: {tool_name}", "tool")

    def add_edge(u: str, v: str, rel: str, flow: str, run_title: str) -> None:
        if u == v:
            return
        k = (u, v, rel, flow)
        edge_counts.setdefault(k, []).append(run_title)

    for r_idx, norm in enumerate(norms):
        run_label = f"R{r_idx + 1}: {norm['title'][:36]}"
        steps_out: list[dict[str, Any]] = []
        steps_out.append(
            {
                "stepIndex": 1,
                "nodeId": "state:intake",
                "label": f"{norm['agent']} starts trajectory",
                "role": "normal",
            }
        )
        add_edge("state:intake", "state:planner", "advances-to", "forward", run_label)
        blind_cnt = 0
        agent_events = [e for e in norm["events"] if e["source"] != "user"]
        final_ok = bool(agent_events) and not agent_events[-1].get("is_error")

        for ev in norm["events"]:
            if ev["source"] == "user":
                continue
            cid, ctitle, ckind = canonical_tool_bucket(ev.get("tool"))
            if cid not in node_ids:
                node_ids.add(cid)
                nodes.append(
                    {
                        "id": cid,
                        "title": ctitle,
                        "kind": ckind,
                        "status": "subagent" if ckind == "subagent" else "ready",
                        "parent": root_id,
                        "summary": f"Shared capability invoked across trajectories ({ctitle}).",
                        "sources": [],
                        "tags": [],
                        "metrics": {},
                    }
                )

            add_edge(
                "state:planner",
                cid,
                "delegates-subagent" if ckind == "subagent" else "invokes-tool",
                "forward",
                run_label,
            )

            if ev.get("is_error"):
                blind_cnt += 1
                err_id = "err:obstacle"
                if err_id not in node_ids:
                    node_ids.add(err_id)
                    nodes.append(
                        {
                            "id": err_id,
                            "title": "✕ Blind alley / tool error",
                            "kind": "failure-state",
                            "status": "blind-alley",
                            "parent": root_id,
                            "summary": "Dead-end state reached when a tool call reports an error.",
                            "sources": [],
                            "tags": [],
                            "metrics": {},
                        }
                    )
                add_edge(cid, err_id, "explores-spur", "forward", run_label)
                add_edge(
                    err_id, "state:planner", "backtracks-to", "backtrack", run_label
                )

                steps_out.append(
                    {
                        "stepIndex": len(steps_out) + 1,
                        "nodeId": cid,
                        "label": ev["label"],
                        "role": "normal",
                        "thought": ev.get("thought", ""),
                    }
                )
                steps_out.append(
                    {
                        "stepIndex": len(steps_out) + 1,
                        "nodeId": err_id,
                        "label": f"✕ Error / Miss in {ev['label']}",
                        "role": "blind-alley",
                        "isError": True,
                        "observation": ev.get("observation", ""),
                    }
                )
                steps_out.append(
                    {
                        "stepIndex": len(steps_out) + 1,
                        "nodeId": "state:planner",
                        "label": "↺ Backtrack to Planner & Pivot Strategy",
                        "role": "backtrack",
                    }
                )
            else:
                if final_ok:
                    add_edge(
                        cid, "state:synthesis", "produces-outcome", "forward", run_label
                    )
                steps_out.append(
                    {
                        "stepIndex": len(steps_out) + 1,
                        "nodeId": cid,
                        "label": ev["label"],
                        "role": "subagent" if ckind == "subagent" else "normal",
                        "thought": ev.get("thought", ""),
                        "observation": ev.get("observation", ""),
                    }
                )

        if final_ok:
            steps_out.append(
                {
                    "stepIndex": len(steps_out) + 1,
                    "nodeId": "state:synthesis",
                    "label": "Trajectory Goal Reached",
                    "role": "goal",
                }
            )

        traces.append(
            {
                "id": f"run-{r_idx + 1}-{norm['id']}",
                "title": run_label,
                "color": palette[r_idx % len(palette)],
                "agent": norm["agent"],
                "model": norm["model"],
                "totalTokens": norm["total_tokens"],
                "blindAlleyCount": blind_cnt,
                "steps": steps_out,
            }
        )

    edges = []
    for idx, ((u, v, rel, flow), runs) in enumerate(edge_counts.items(), start=1):
        uniq_runs = sorted(set(runs))
        edges.append(
            {
                "id": f"cmpe-{idx}",
                "from": u,
                "to": v,
                "relation": rel,
                "flowRole": flow,
                "summary": f"Traversed {len(runs)}× across {len(uniq_runs)} run(s): {', '.join(uniq_runs)}",
                "contextSnippet": f"Runs: {', '.join(uniq_runs)} ({len(runs)} total transitions)",
            }
        )

    overlays = [
        {
            "id": f"run-slice:{idx + 1}",
            "title": tr["title"],
            "kind": "trajectory-footprint",
            "summary": f"{tr['agent']}{' (' + tr['model'] + ')' if tr['model'] else ''}: {len(tr['steps'])} transitions, {tr['blindAlleyCount']} blind alleys.",
            "touches": sorted({s["nodeId"] for s in tr["steps"]}),
        }
        for idx, tr in enumerate(traces)
    ]

    return {
        "schema": "strata-graph/1",
        "id": graph_id or "atif-multi-compare",
        "title": f"ATIF Multi-Run Comparison ({len(norms)} Trajectories)",
        "subtitle": f"Click '⇄ Compare All' in the ATIF bar to see R1..R{len(norms)} footprints across shared tools, subagents, and blind-alley recovery loops.",
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
def _as_list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def error_diagnostics(diags: list[Any]) -> list[dict[str, Any]]:
    return [d for d in diags if isinstance(d, dict) and d.get("level") == "error"]


def validate_dataset(ds: dict[str, Any]) -> list[dict[str, str]]:
    """Check ids, parents, edges, and trace steps.

    Reports MISSING_ROOT, MALFORMED_NODE, BAD_ID, DUPLICATE_ID, MISSING_PARENT, PARENT_CYCLE,
    MALFORMED_EDGE, DANGLING_EDGE, MALFORMED_STEP, and DANGLING_TRACE_STEP.
    Findings are appended to ds["diagnostics"]; a finding already present is not
    added again, so repeated runs over the same dataset stay stable.
    """
    diags = list(_as_list(ds.get("diagnostics")))

    def report(code: str, message: str) -> None:
        diag = {"level": "error", "code": code, "message": message}
        if diag not in diags:
            diags.append(diag)

    for key, code in (
        ("nodes", "MALFORMED_NODE"),
        ("edges", "MALFORMED_EDGE"),
        ("traces", "MALFORMED_STEP"),
    ):
        if ds.get(key) is not None and not isinstance(ds[key], list):
            report(code, f"{key} must be a list, got {type(ds[key]).__name__}.")

    by_id: dict[str, dict[str, Any]] = {}
    for n in _as_list(ds.get("nodes")):
        if not isinstance(n, dict):
            report("MALFORMED_NODE", f"Node {n!r} is not an object.")
            continue
        if not isinstance(n.get("id"), str) or not n["id"]:
            report("BAD_ID", f"Node id {n.get('id')!r} must be a non-empty string.")
            continue
        if n["id"] in by_id:
            report("DUPLICATE_ID", f"Node id {n['id']} is defined more than once.")
        by_id[n["id"]] = n

    def known(node_id: Any) -> bool:
        return isinstance(node_id, str) and node_id in by_id

    if not known(ds.get("rootId")):
        report("MISSING_ROOT", f"rootId {ds.get('rootId')} missing from nodes.")
    for n in by_id.values():
        parent = n.get("parent")
        if parent is not None and not known(parent):
            report(
                "MISSING_PARENT", f"Node {n['id']} references missing parent {parent}."
            )
    for start in by_id:
        path: list[str] = []
        cur: Any = start
        while known(cur) and cur not in path:
            path.append(cur)
            cur = by_id[cur].get("parent")
        if known(cur):
            members = sorted(path[path.index(cur) :])
            report("PARENT_CYCLE", f"Parent cycle among nodes: {', '.join(members)}.")
    for e in _as_list(ds.get("edges")):
        if not isinstance(e, dict):
            report("MALFORMED_EDGE", f"Edge {e!r} is not an object.")
        elif not known(e.get("from")) or not known(e.get("to")):
            report("DANGLING_EDGE", f"Edge {e.get('id')} references missing endpoint.")
    for t in _as_list(ds.get("traces")):
        if not isinstance(t, dict):
            report("MALFORMED_STEP", f"Trace {t!r} is not an object.")
            continue
        trace = t
        if trace.get("steps") is not None and not isinstance(trace["steps"], list):
            report("MALFORMED_STEP", f"Trace {trace.get('id')} steps must be a list.")
        for step in _as_list(trace.get("steps")):
            if not isinstance(step, dict):
                report(
                    "MALFORMED_STEP",
                    f"Trace {trace.get('id')} has a step that is not an object: {step!r}.",
                )
            elif not known(step.get("nodeId")):
                report(
                    "DANGLING_TRACE_STEP",
                    f"Trace {trace.get('id')} step {step.get('stepIndex')} references missing node {step.get('nodeId')}.",
                )
    ds["diagnostics"] = diags
    return diags


def render_html(payload: dict[str, Any], title: str | None = None) -> str:
    tpl = (ASSETS_DIR / "template.html").read_text(encoding="utf-8")
    css = (ASSETS_DIR / "viewer.css").read_text(encoding="utf-8")
    js = (ASSETS_DIR / "viewer.js").read_text(encoding="utf-8")

    # "<" must never appear raw inside a script element: "</script>" ends it and
    # "<!--" followed by "<script" switches the HTML tokenizer's script state.
    safe_json = (
        json.dumps(payload, ensure_ascii=False)
        .replace("<", "\\u003c")
        .replace("\u2028", "\\u2028")
        .replace("\u2029", "\\u2029")
    )

    page_title = title or payload.get("title") or "Strata Graph Explorer"
    html = tpl.replace(
        "<title>Strata Graph Explorer</title>",
        f"<title>{html_escape(str(page_title))}</title>",
    )
    # One pass, so text inside an inserted block is never scanned for markers.
    blocks = {
        "CSS": f"<style>\n{css}\n</style>",
        "DATA": f'<script id="strata-data" type="application/json">{safe_json}</script>',
        "JS": f"<script>\n{js}\n</script>",
    }
    return re.sub(r"<!-- STRATA:(CSS|DATA|JS) -->", lambda m: blocks[m.group(1)], html)


OUTPUT_SUFFIXES = (".html", ".htm", ".json")


def check_output_path(out_path: Path) -> None:
    if out_path.suffix.lower() not in OUTPUT_SUFFIXES:
        raise ValueError(f"Output path {out_path} must end in .html, .htm, or .json.")


def write_output(payload: dict[str, Any], out_path: Path) -> None:
    check_output_path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    if out_path.suffix.lower() in (".html", ".htm"):
        out_path.write_text(render_html(payload), encoding="utf-8")
    else:
        out_path.write_text(
            json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8"
        )


# ---------------------------------------------------------------------------
# CLI Entrypoint
# ---------------------------------------------------------------------------
def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="strata",
        description="Deterministic multi-layer graph compiler and standalone HTML explorer.",
    )
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_okf = sub.add_parser(
        "compile-okf", help="Compile an OKF v0.2 Markdown wiki bundle."
    )
    p_okf.add_argument("wiki_dir", type=Path)
    p_okf.add_argument("-o", "--output", type=Path, required=True)
    p_okf.add_argument("--id", default=None)

    p_kg = sub.add_parser(
        "compile-kg",
        help="Compile a Knowledge Graph (SQLite pipeline.db or YAML kg/ directory).",
    )
    p_kg.add_argument("kg_path", type=Path)
    p_kg.add_argument("-o", "--output", type=Path, required=True)
    p_kg.add_argument("--id", default=None)

    p_atif = sub.add_parser(
        "compile-atif", help="Compile 1..N ATIF or Jetski JSONL trajectories."
    )
    p_atif.add_argument("inputs", type=Path, nargs="+")
    p_atif.add_argument(
        "--mode",
        choices=["decision", "compare"],
        default="decision",
        help="decision (one run) or compare. With several inputs the result is always "
        "a comparison, and the output reports mode compare.",
    )
    p_atif.add_argument("-o", "--output", type=Path, required=True)
    p_atif.add_argument("--id", default=None)

    p_json = sub.add_parser(
        "compile-json",
        help="Validate and compile a strata-graph/1 process or system JSON spec.",
    )
    p_json.add_argument("spec_path", type=Path)
    p_json.add_argument("-o", "--output", type=Path, required=True)

    p_val = sub.add_parser(
        "validate",
        help="Run deterministic integrity checks on a strata-graph/1 JSON file.",
    )
    p_val.add_argument("graph_json", type=Path)

    p_hub = sub.add_parser(
        "build-hub",
        help="Bundle multiple strata-graph/1 JSON datasets into one multi-tab HTML Explorer Hub.",
    )
    p_hub.add_argument("datasets", type=Path, nargs="+")
    p_hub.add_argument("-o", "--output", type=Path, required=True)
    p_hub.add_argument("--title", default="Strata Graph Multi-Domain Explorer")

    return parser


def _read_dataset(path: Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8")
    data = json.loads(text)
    if not isinstance(data, dict):
        raise json.JSONDecodeError(f"{path} is not a JSON object", text, 0)
    return data


def _run(args: argparse.Namespace) -> int:
    if getattr(args, "output", None) is not None:
        check_output_path(args.output)

    def finish(ds: dict[str, Any], output: Path, **extra: Any) -> int:
        """Validate, then write and report, or print the errors and return 1."""
        errs = error_diagnostics(validate_dataset(ds))
        if errs:
            print(json.dumps({"status": "error", "errors": errs}), file=sys.stderr)
            return 1
        write_output(ds, output)
        print(json.dumps({"status": "ok", **extra, "output": str(output)}))
        return 0

    if args.cmd == "compile-okf":
        ds = compile_okf(args.wiki_dir, graph_id=args.id)
        return finish(
            ds,
            args.output,
            nodes=len(ds["nodes"]),
            edges=len(ds["edges"]),
            overlays=len(ds["overlays"]),
        )

    if args.cmd == "compile-kg":
        ds = compile_kg(args.kg_path, graph_id=args.id)
        return finish(
            ds,
            args.output,
            nodes=len(ds["nodes"]),
            edges=len(ds["edges"]),
            overlays=len(ds["overlays"]),
        )

    if args.cmd == "compile-atif":
        mode = (
            "compare" if args.mode == "compare" or len(args.inputs) > 1 else "decision"
        )
        ds = (
            compile_atif_compare(args.inputs, graph_id=args.id)
            if mode == "compare"
            else compile_atif_decision(args.inputs, graph_id=args.id)
        )
        return finish(
            ds,
            args.output,
            mode=mode,
            nodes=len(ds["nodes"]),
            edges=len(ds["edges"]),
            traces=len(ds["traces"]),
        )

    if args.cmd == "compile-json":
        ds = _read_dataset(args.spec_path)
        ds.setdefault("schema", "strata-graph/1")
        ds.setdefault("generatedAt", now_iso())
        return finish(
            ds,
            args.output,
            nodes=len(_as_list(ds.get("nodes"))),
            edges=len(_as_list(ds.get("edges"))),
        )

    if args.cmd == "validate":
        ds = _read_dataset(args.graph_json)
        diags = validate_dataset(ds)
        errs = error_diagnostics(diags)
        print(
            json.dumps(
                {"status": "error" if errs else "ok", "diagnostics": diags}, indent=2
            )
        )
        return 1 if errs else 0

    if args.cmd == "build-hub":
        loaded = []
        errs = []
        for p in args.datasets:
            ds = _read_dataset(p)
            diags = validate_dataset(ds)
            errs += [{**d, "dataset": str(p)} for d in error_diagnostics(diags)]
            loaded.append(ds)
        if errs:
            print(json.dumps({"status": "error", "errors": errs}), file=sys.stderr)
            return 1
        hub = {
            "schema": "strata-hub/1",
            "title": args.title,
            "generatedAt": now_iso(),
            "datasets": loaded,
        }
        write_output(hub, args.output)
        print(
            json.dumps(
                {"status": "ok", "datasets": len(loaded), "output": str(args.output)}
            )
        )
        return 0

    return 1


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    try:
        return _run(args)
    except (OSError, ValueError) as exc:
        print(json.dumps({"status": "error", "error": str(exc)}), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
