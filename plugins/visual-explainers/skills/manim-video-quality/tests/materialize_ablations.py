#!/usr/bin/env python3
"""Materialize the runtime-switched ablation scene into 9 static fixtures.

``scripts/ablation_scene.py`` picks its single injected defect at RUNTIME from
the ``ABLATION`` environment variable, so every variant shares one source file.
A static-analysis linter reading that file sees all defect branches at once: it
cannot tell the variants apart and it fires false positives on the clean
baseline.

This generator resolves the switch at BUILD time. For each of the 9 values it
emits ``tests/fixtures/abl_<value>.py`` where

  * the constants the switch controls (BG, FG_TEXT, FONT, FILL_OP, STROKE_W,
    RUSH, the node colour) are literals for that variant,
  * every branch belonging to another variant is deleted outright,
  * no reference to the environment variable survives.

Re-run after editing the source::

    python3 tests/materialize_ablations.py

The anchors below are asserted, so a source edit that moves them fails loudly
instead of silently emitting a wrong fixture.
"""

from __future__ import annotations

import ast
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "scripts" / "ablation_scene.py"
OUT_DIR = ROOT / "tests" / "fixtures"

ABLATIONS = [
    "none",
    "font_ttc_bug",
    "rushed_pacing",
    "card_itis",
    "color_spray",
    "text_flood",
    "light_bg",
    "cut_not_morph",
    "overlap_nodes",
]


class AnchorError(RuntimeError):
    """The source no longer matches an anchor this generator relies on."""


# --------------------------------------------------------------------------
# line helpers
# --------------------------------------------------------------------------


def indent_of(line: str) -> int:
    return len(line) - len(line.lstrip())


def find(lines: list[str], pattern: str, what: str, start: int = 0) -> int:
    rx = re.compile(pattern)
    for i in range(start, len(lines)):
        if rx.search(lines[i]):
            return i
    raise AnchorError(f"anchor not found ({what}): /{pattern}/")


def suite_end(lines: list[str], header: int) -> int:
    """Exclusive end of the suite introduced by ``lines[header]``.

    Trailing blank lines are not part of the suite.
    """
    base = indent_of(lines[header])
    last = header
    j = header + 1
    while j < len(lines):
        if lines[j].strip() == "":
            j += 1
            continue
        if indent_of(lines[j]) <= base:
            break
        last = j
        j += 1
    return last + 1


def dedent(body: list[str], header_indent: int) -> list[str]:
    solid = [l for l in body if l.strip()]
    if not solid:
        return []
    amount = min(indent_of(l) for l in solid) - header_indent
    out = []
    for line in body:
        out.append("" if not line.strip() else line[amount:])
    return out


def splice(lines: list[str], start: int, end: int, repl: list[str]) -> list[str]:
    """Replace ``lines[start:end]`` with ``repl``, avoiding blank-line pileups."""
    head, tail = lines[:start], lines[end:]
    if not repl:
        while head and tail and head[-1].strip() == "" and tail[0].strip() == "":
            tail = tail[1:]
    return head + repl + tail


def drop_region(lines: list[str], start: int, end: int) -> list[str]:
    return splice(lines, start, end, [])


def resolve_if(lines: list[str], header: int, keep_if: bool) -> list[str]:
    """Collapse an ``if``/optional-``else`` construct to the surviving branch."""
    base = indent_of(lines[header])
    if_end = suite_end(lines, header)

    k = if_end
    while k < len(lines) and lines[k].strip() == "":
        k += 1
    has_else = (
        k < len(lines) and lines[k].strip() == "else:" and indent_of(lines[k]) == base
    )

    if has_else:
        end = suite_end(lines, k)
        else_body = lines[k + 1 : end]
    else:
        end = if_end
        else_body = []

    body = lines[header + 1 : if_end] if keep_if else else_body
    return splice(lines, header, end, dedent(body, base))


# A comment mentioning "violates" names the very rule the fixture is meant to
# test, so it would hand the linter the answer. The quote guard keeps the
# pattern from biting into "#RRGGBB" colour literals.
LEAK_RX = re.compile(r"""\s*\#[^"']*\bviolates\b.*$""", re.IGNORECASE)

NEUTRALIZED = {
    "# Compound words — the exact strings that expose the .ttc shaping bug.": (
        "# Compound words, used as node labels."
    ),
}


def strip_leaky_comments(lines: list[str]) -> list[str]:
    """Drop ground-truth hints so a fixture does not label its own defect."""
    out = []
    for line in lines:
        stripped = line.strip()
        if stripped in NEUTRALIZED:
            out.append(line.replace(stripped, NEUTRALIZED[stripped]))
            continue
        cleaned = LEAK_RX.sub("", line)
        if cleaned.strip() == "" and stripped != "":
            continue  # whole-line comment
        out.append(cleaned)
    return out


def tidy(lines: list[str]) -> list[str]:
    out: list[str] = []
    blanks = 0
    for line in lines:
        line = line.rstrip()
        if line == "":
            blanks += 1
            if blanks > 2:
                continue
        else:
            blanks = 0
        out.append(line)
    while out and out[-1] == "":
        out.pop()
    return out


# --------------------------------------------------------------------------
# per-variant constants (mirrors the runtime overrides in the source)
# --------------------------------------------------------------------------


def constants(ablation: str) -> dict[str, str]:
    bg, fg = "#0E0E10", "#FFFFFF"
    font = "Roboto"
    fill_op, stroke_w = "0.12", "2.5"
    rush = "1.0"
    if ablation == "light_bg":
        bg, fg = "#F8F9FA", "#3C4043"
    if ablation == "font_ttc_bug":
        font = "Helvetica Neue"
    if ablation == "card_itis":
        fill_op, stroke_w = "0.95", "5.0"
    if ablation == "rushed_pacing":
        rush = "0.25"
    return {
        "BG": bg,
        "FG_TEXT": fg,
        "FONT": font,
        "FILL_OP": fill_op,
        "STROKE_W": stroke_w,
        "RUSH": rush,
    }


def prune_imports(text: str) -> str:
    """Drop manim names left unused after the dead branches were removed.

    Matters for fixture fidelity: a ``Transform`` import surviving in the
    cut_not_morph file would let a grep-level check still see a morph.
    """
    tree = ast.parse(text)
    used = {n.id for n in ast.walk(tree) if isinstance(n, ast.Name)}

    node = None
    for stmt in tree.body:
        if isinstance(stmt, ast.ImportFrom) and stmt.module == "manim":
            node = stmt
            break
    if node is None:
        raise AnchorError("no `from manim import ...` statement")

    keep = [a.name for a in node.names if (a.asname or a.name) in used]
    if len(keep) == len(node.names):
        return text

    block = ["from manim import ("] + [f"    {n}," for n in keep] + [")"]
    lines = text.split("\n")
    lines[node.lineno - 1 : node.end_lineno] = block
    return "\n".join(lines)


DOCSTRING = '''"""Materialized fixture for the {name} variant of the ablation scene.

Generated by tests/materialize_ablations.py from scripts/ablation_scene.py.
Do not edit by hand -- re-run the generator instead.
"""'''


def materialize(src: str, ablation: str) -> str:
    lines = src.split("\n")
    c = constants(ablation)

    # 1. module docstring -> variant-specific, switch-free.
    if not lines[0].startswith('"""'):
        raise AnchorError("source does not start with a module docstring")
    doc_end = find(lines, r'^"""\s*$', "docstring close", start=1)
    lines = splice(
        lines,
        0,
        doc_end + 1,
        [f"# Ablation fixture: {ablation}"] + DOCSTRING.format(name=ablation).split("\n"),
    )

    # 2. `import os` is only there for the runtime switch.
    i = find(lines, r"^import os$", "import os")
    end = i + 1
    if end < len(lines) and lines[end].strip() == "":
        end += 1
    lines = drop_region(lines, i, end)

    # 3. the switch itself: read, validate, bail.
    i = find(lines, r"^ABLATION = os\.environ", "env read")
    end = find(lines, r"^\s*raise SystemExit", "switch validation", start=i) + 1
    lines = drop_region(lines, i, end)

    # 4. spec-conformant defaults -> variant literals.
    for name in ("BG", "FONT"):
        i = find(lines, rf'^{name} = "', f"{name} default")
        lines[i] = re.sub(r'"[^"]*"', f'"{c[name]}"', lines[i], count=1)
    i = find(lines, r'^FG_TEXT = "', "FG_TEXT default")
    lines[i] = re.sub(r'"[^"]*"', f'"{c["FG_TEXT"]}"', lines[i], count=1)
    for name in ("FILL_OP", "STROKE_W"):
        i = find(lines, rf"^{name} = ", f"{name} default")
        lines[i] = f"{name} = {c[name]}"

    # 5. the runtime override block is now folded into step 4.
    i = find(lines, r"^# --- per-ablation overrides", "overrides header")
    end = find(lines, r"^# 8 unreserved hues", "spray header", start=i)
    while end > i and lines[end - 1].strip() == "":
        end -= 1
    lines = drop_region(lines, i, end)

    # 6. the spray palette only exists for color_spray.
    i = find(lines, r"^# 8 unreserved hues", "spray header")
    spray = find(lines, r"^SPRAY = \[", "spray list", start=i)
    spray_end = spray
    while not lines[spray_end].rstrip().endswith("]"):
        spray_end += 1
    spray_end += 1
    if ablation == "color_spray":
        lines = drop_region(lines, i, spray)  # drop the leaky comment only
    else:
        end = spray_end
        if end < len(lines) and lines[end].strip() == "":
            end += 1
        lines = drop_region(lines, i, end)

    # 7. pacing multiplier.
    i = find(lines, r"^RUSH = ", "RUSH")
    lines[i] = f"RUSH = {c['RUSH']}"

    # 8. node colour.
    i = find(lines, r"^\s*return SPRAY\[", "node_color body")
    lines[i] = (
        "    return SPRAY[i % len(SPRAY)]"
        if ablation == "color_spray"
        else "    return BLUE"
    )

    # 9. overlap injection.
    i = find(lines, r'^\s*if ABLATION == "overlap_nodes":', "overlap block")
    lines = resolve_if(lines, i, keep_if=(ablation == "overlap_nodes"))

    # 10. text flood: for every other variant Beat 3 produces nothing at all,
    #     so the beat header goes with it.
    i = find(lines, r'^\s*if ABLATION == "text_flood":', "text_flood block")
    if ablation == "text_flood":
        lines = resolve_if(lines, i, keep_if=True)
    else:
        header = i
        if lines[header - 1].lstrip().startswith("# --- Beat 3"):
            header -= 1
        end = suite_end(lines, i)
        k = end
        while k < len(lines) and lines[k].strip() == "":
            k += 1
        if lines[k].strip() == "else:":
            end = suite_end(lines, k)
        lines = drop_region(lines, header, end)

    # 11. cut instead of morph.
    i = find(lines, r'^\s*if ABLATION == "cut_not_morph":', "cut_not_morph block")
    lines = resolve_if(lines, i, keep_if=(ablation == "cut_not_morph"))

    # 12. Beat 5 branches on `flood`, which is now statically known.
    i = find(lines, r"^\s*if flood is None:", "beat 5 branch")
    lines = resolve_if(lines, i, keep_if=(ablation != "text_flood"))
    if ablation == "text_flood":
        # No caption beat survives; its header would describe code that is gone.
        h = find(lines, r"^\s*# --- Beat 5", "beat 5 header")
        lines = drop_region(lines, h, h + 1)

    lines = tidy(strip_leaky_comments(lines))
    return prune_imports("\n".join(lines)) + "\n"


def main() -> int:
    src = SRC.read_text()
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    failures = []
    for ablation in ABLATIONS:
        out = materialize(src, ablation)
        path = OUT_DIR / f"abl_{ablation}.py"

        try:
            ast.parse(out, filename=str(path))
        except SyntaxError as exc:  # pragma: no cover - generator bug
            failures.append(f"{path.name}: syntax error: {exc}")
            continue
        bad = False
        for banned in ("ABLATION", "os.environ"):
            if banned in out:
                failures.append(f"{path.name}: still references {banned}")
                bad = True
        if "AblationScene" not in out:
            failures.append(f"{path.name}: lost the AblationScene class")
            bad = True
        if bad:
            # Never write a fixture that failed validation: a corrupt fixture
            # on disk silently poisons every later linter run, and the
            # non-zero exit alone does not undo it.
            continue

        path.write_text(out)
        print(f"wrote {path.relative_to(ROOT)}")

    for f in failures:
        print(f"FAIL {f}", file=sys.stderr)
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
