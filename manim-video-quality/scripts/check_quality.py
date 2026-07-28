#!/usr/bin/env python3
# /// script
# requires-python = ">=3.9"
# dependencies = ["numpy", "pillow"]
# ///
"""Deterministic quality checker — the ~80% of the rubric that is not an LLM question.

Font, fill opacity, stroke width, run_times, palette conformance, negative
space, colours per frame, text overlap and phantom word gaps are all exact
computations over the scene source and the rendered frames. Asking a model to
eyeball them is slower, costs money, varies run to run, and — measured — gets
them wrong: a holistic LLM rubric scored `text_readability: 9/10` on a render
containing four mis-rendered words.

So: compute what can be computed. Reserve the model for narrative judgment.

Emits `reward.json` (Harbor-compatible: flat float metrics) plus a human
readable report. Exit code is non-zero if any BLOCK rule fails.

    python3 check_quality.py --scene scene.py --video render.mp4
    python3 check_quality.py --scene scene.py            # SRC checks only

Rule IDs match ../reference/quality-spec.md.
"""

from __future__ import annotations

import argparse
import ast
import json
import re
import shutil
import subprocess
import sys
import tempfile
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path

# --- policy ---------------------------------------------------------------
# There is no such thing as a banned font, only a broken (font, size, weight)
# combination. Measured: Helvetica Neue at 15/BOLD scores 1.03 (renders
# "LangChain" as "Lang Chain") but at 20/BOLD scores 0.42 and is fine, while
# Roboto at 20/NORMAL scores 0.78 and is worse. So test what the scene
# actually uses rather than maintaining a blocklist.
GAP_FAIL = 0.75    # max intra-word gap / width of a real space
GAP_WARN = 0.60
PALETTE = {
    "#0E0E10", "#000000", "#FFFFFF", "#BBBBBB", "#888888", "#444444",
    "#58C4DD", "#F0AC5F", "#83C167", "#FC6255", "#9A72AC",
    "#4285F4", "#EA4335", "#FBBC04", "#34A853", "#5C6BC0",
}
MAX_FILL_OPACITY = 0.20
STROKE_RANGE = (1.0, 4.0)
MIN_RUN_TIME = 0.5
MAX_TEXT_WORDS = 12
MIN_LAG_RATIO = 0.25
ALLOWED_RATE_FUNCS = {"smooth", "linear", "ease_in_sine", "ease_out_sine",
                      "ease_in_out_sine", "rush_into", "rush_from",
                      "ease_in_quad", "ease_out_quad", "there_and_back"}
MIN_NEGATIVE_SPACE = 0.60
MAX_HUES_PER_FRAME = 3

HEX = re.compile(r"#[0-9A-Fa-f]{6}")
WORDISH = re.compile(r"[A-Za-z][A-Za-z'\-]+")


@dataclass
class Finding:
    rule: str
    severity: str          # BLOCK | WARN | INFO
    message: str
    where: str = ""


@dataclass
class Report:
    findings: list[Finding] = field(default_factory=list)
    metrics: dict = field(default_factory=dict)
    checked: set = field(default_factory=set)

    def add(self, rule, sev, msg, where=""):
        self.findings.append(Finding(rule, sev, msg, where))

    def ran(self, *rules):
        self.checked.update(rules)


# =========================================================================
# SRC — static analysis of the scene source
# =========================================================================

def _kw(node, name):
    for k in node.keywords or []:
        if k.arg == name:
            return k.value
    return None


def _num(node):
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
        return float(node.value)
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.USub):
        v = _num(node.operand)
        return -v if v is not None else None
    return None


def _str(node):
    return node.value if isinstance(node, ast.Constant) and isinstance(node.value, str) else None


def check_source(path: Path, rep: Report) -> None:
    src = path.read_text()
    tree = ast.parse(src)
    rep.ran("A1", "A2", "A3", "B1", "C1", "C6", "D2", "D4", "D5", "D7")

    # resolve simple module-level string constants so FONT = "Roboto" works
    consts: dict[str, str] = {}
    literal_pool: list[str] = []      # strings that may reach a Text() indirectly
    for n in tree.body:
        if isinstance(n, ast.Assign) and len(n.targets) == 1 and isinstance(n.targets[0], ast.Name):
            v = _str(n.value)
            if v:
                consts[n.targets[0].id] = v
            # module-level list/tuple of labels, e.g. NODE_LABELS = [...]
            elif isinstance(n.value, (ast.List, ast.Tuple)):
                for el in n.value.elts:
                    s = _str(el)
                    if s:
                        literal_pool.append(s)
                    elif isinstance(el, (ast.Tuple, ast.List)) and el.elts:
                        s0 = _str(el.elts[0])
                        if s0:
                            literal_pool.append(s0)

    # manim exports these weights as bare names (BOLD == "BOLD"), so a scene
    # writing weight=BOLD must resolve, or every bold string is mis-measured
    # as NORMAL — which silently hides the worst shaping failures.
    MANIM_CONSTS = {"BOLD": "BOLD", "NORMAL": "NORMAL", "LIGHT": "LIGHT",
                    "THIN": "THIN", "MEDIUM": "MEDIUM", "SEMIBOLD": "SEMIBOLD",
                    "HEAVY": "HEAVY", "ULTRABOLD": "ULTRABOLD",
                    "ULTRALIGHT": "ULTRALIGHT", "BOOK": "BOOK"}

    def resolve(node):
        if isinstance(node, ast.Name):
            return consts.get(node.id) or MANIM_CONSTS.get(node.id)
        return _str(node)

    fonts, fills, strokes, run_times = Counter(), [], [], []
    type_specs: list[tuple] = []
    text_words, rate_funcs, lag_ratios = [], [], []
    n_transform = n_fadeout = n_fadein = 0

    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        fn = node.func
        name = fn.attr if isinstance(fn, ast.Attribute) else getattr(fn, "id", "")

        if name in ("Text", "MarkupText", "Tex", "MathTex"):
            f = resolve(_kw(node, "font"))
            if f:
                fonts[f] += 1
            sz = _num(_kw(node, "font_size")) or 24.0
            wt = resolve(_kw(node, "weight")) or "NORMAL"
            if node.args:
                s = _str(node.args[0])
                if s:
                    text_words.append((len(s.split()), s))
                    if f:
                        type_specs.append((s, f, sz, wt))

        if name in ("Transform", "ReplacementTransform", "TransformMatchingShapes"):
            n_transform += 1
        if name == "FadeOut":
            n_fadeout += 1
        if name == "FadeIn":
            n_fadein += 1

        fo = _num(_kw(node, "fill_opacity"))
        if fo is not None:
            fills.append((fo, name))
        sw = _num(_kw(node, "stroke_width"))
        if sw is not None:
            strokes.append((sw, name))
        rt = _num(_kw(node, "run_time"))
        if rt is not None:
            run_times.append(rt)
        lr = _num(_kw(node, "lag_ratio"))
        if lr is not None:
            lag_ratios.append(lr)
        rf = _kw(node, "rate_func")
        if rf is not None:
            rn = rf.attr if isinstance(rf, ast.Attribute) else getattr(rf, "id", None)
            if rn:
                rate_funcs.append(rn)

    # C1/C2 handled by the measured typography pass (needs manim at runtime)
    rep.metrics["fonts_used"] = float(len(fonts))

    # A1 background
    bg = None
    m = re.search(r'config\.background_color\s*=\s*["\'](#[0-9A-Fa-f]{6})', src)
    if not m:
        m2 = re.search(r'BG\s*=\s*["\'](#[0-9A-Fa-f]{6})', src)
        bg = m2.group(1).upper() if m2 else None
    else:
        bg = m.group(1).upper()
    if bg and bg not in {"#0E0E10", "#000000"}:
        rep.add("A1", "BLOCK", f"background {bg} is not the dark canvas", str(path.name))
    rep.metrics["background_ok"] = 1.0 if (bg in {"#0E0E10", "#000000"}) else 0.0

    # A2 card-itis
    over = [(v, n) for v, n in fills if v > MAX_FILL_OPACITY]
    for v, n in over[:6]:
        rep.add("A2", "BLOCK", f"fill_opacity={v} on {n} exceeds {MAX_FILL_OPACITY} (card-itis)")
    rep.metrics["fill_opacity_violations"] = float(len(over))
    rep.metrics["fill_opacity_max"] = max((v for v, _ in fills), default=0.0)

    # A3 stroke width
    bad_sw = [(v, n) for v, n in strokes if not (STROKE_RANGE[0] <= v <= STROKE_RANGE[1])]
    for v, n in bad_sw[:5]:
        rep.add("A3", "WARN", f"stroke_width={v} on {n} outside {STROKE_RANGE}")
    rep.metrics["stroke_violations"] = float(len(bad_sw))

    # B1 palette
    used = {h.upper() for h in HEX.findall(src)}
    off = sorted(used - {p.upper() for p in PALETTE})
    for h in off[:8]:
        rep.add("B1", "WARN", f"colour {h} not in approved palette")
    rep.metrics["palette_violations"] = float(len(off))

    # C6 text length
    long_text = [(w, s) for w, s in text_words if w > MAX_TEXT_WORDS]
    for w, s in long_text[:4]:
        rep.add("C6", "WARN", f"{w}-word string (max {MAX_TEXT_WORDS}): {s[:58]!r}")
    rep.metrics["long_text_count"] = float(len(long_text))

    # D2 sub-second
    fast = [r for r in run_times if r < MIN_RUN_TIME]
    if fast:
        rep.add("D2", "WARN",
                f"{len(fast)} run_time(s) below {MIN_RUN_TIME}s "
                f"(min {min(fast)}) — invisible at 1 FPS grading, reads as frantic")
    rep.metrics["subsecond_run_times"] = float(len(fast))

    # D4 morph vs cut
    cuts = min(n_fadeout, n_fadein)
    ratio = (n_transform / cuts) if cuts else (float("inf") if n_transform else 0.0)
    if cuts and ratio < 1.0:
        rep.add("D4", "WARN",
                f"morph:cut ratio {ratio:.2f} ({n_transform} Transform vs "
                f"{cuts} FadeOut+FadeIn pairs) — prefer morphs for continuity")
    rep.metrics["morph_cut_ratio"] = 99.0 if ratio == float("inf") else round(ratio, 3)

    # D5 easing
    bad_rf = [r for r in rate_funcs if r not in ALLOWED_RATE_FUNCS]
    for r in set(bad_rf):
        rep.add("D5", "WARN", f"rate_func {r!r} not in the smooth-easing allowlist")
    rep.metrics["easing_violations"] = float(len(bad_rf))

    # D7 stagger
    tight = [l for l in lag_ratios if l < MIN_LAG_RATIO]
    if tight:
        rep.add("D7", "INFO", f"{len(tight)} lag_ratio(s) below {MIN_LAG_RATIO}")
    rep.metrics["tight_lag_ratios"] = float(len(tight))

    # expected on-screen strings, for the OCR pass
    # Strings that could appear on screen: direct Text() literals plus
    # module-level label lists that get passed into Text() indirectly.
    rep.metrics["_expected_strings"] = [s for _, s in text_words] + literal_pool
    # Label lists reach Text() indirectly, e.g.
    #     NODE_LABELS = ["LangChain", ...]
    #     def make_node(label): return Text(label, font=FONT, font_size=15, ...)
    # Attributing those to the scene's "most common" style guesses wrong (it
    # checked Antigravity at 22/NORMAL, missing the real 15/BOLD failure), so
    # resolve properly: find helper functions that pass a parameter straight
    # into Text(), and attribute pool labels to THOSE styles.
    helper_styles: list[tuple] = []
    for fn in ast.walk(tree):
        if not isinstance(fn, ast.FunctionDef):
            continue
        params = {a.arg for a in fn.args.args}
        for c in ast.walk(fn):
            if (isinstance(c, ast.Call)
                    and getattr(c.func, "id", getattr(c.func, "attr", "")) in
                        ("Text", "MarkupText")
                    and c.args and isinstance(c.args[0], ast.Name)
                    and c.args[0].id in params):
                f = resolve(_kw(c, "font"))
                if f:
                    helper_styles.append(
                        (f, _num(_kw(c, "font_size")) or 24.0,
                         resolve(_kw(c, "weight")) or "NORMAL"))
    if literal_pool:
        styles = helper_styles or (
            [Counter((f, sz, wt) for _, f, sz, wt in type_specs).most_common(1)[0][0]]
            if type_specs else [])
        for s in literal_pool:
            for st in styles:
                type_specs.append((s, *st))
    rep.metrics["_type_specs"] = type_specs


# =========================================================================
# TYPOGRAPHY — measured glyph geometry (no OCR, no video)
# =========================================================================

def check_typography(specs: list[tuple], rep: Report) -> None:
    """C2 — detect phantom word gaps by measuring rendered glyph geometry.

    A shaping bug shows up as one abnormally wide gap *inside* a word. We
    measure every inter-glyph gap and compare the largest to the width of a
    real space in the same font/size/weight. At >=0.75 of a space the word
    visually reads as two words.

    This replaced an OCR approach that did not work: tesseract returned
    nothing on light-on-dark frames, and after inverting still produced
    false splits on clean renders and missed real ones, because it is
    guessing glyph boundaries from pixels rather than measuring them.
    """
    try:
        from manim import Text
    except ImportError:
        rep.add("C2", "INFO", "manim unavailable — typography check skipped")
        return
    import numpy as np

    rep.ran("C2")
    space_cache: dict[tuple, float] = {}
    worst = 0.0
    n_fail = n_warn = 0
    seen: set[tuple] = set()

    for s, font, size, weight in specs:
        for word in WORDISH.findall(s):
            if len(word) < 6:
                continue                      # too short to split visibly
            key = (word, font, size, weight)
            if key in seen:
                continue
            seen.add(key)
            try:
                t = Text(word, font=font, font_size=size, weight=weight)
                if len(t) != len(word):
                    continue                  # ligatures etc; not comparable
                gaps = np.array([t[i + 1].get_left()[0] - t[i].get_right()[0]
                                 for i in range(len(t) - 1)])
                sk = (font, size, weight)
                if sk not in space_cache:
                    sp = Text("a a", font=font, font_size=size, weight=weight)
                    space_cache[sk] = float(
                        sp[1].get_left()[0] - sp[0].get_right()[0])
                space = space_cache[sk]
                if space <= 0:
                    continue
                frac = float(gaps.max()) / space
            except Exception:
                continue

            worst = max(worst, frac)
            if frac >= GAP_FAIL:
                n_fail += 1
                i = int(gaps.argmax()) + 1
                rep.add("C2", "BLOCK",
                        f"{word!r} in {font} {size:g}/{weight} splits as "
                        f"{word[:i]!r} + {word[i:]!r} "
                        f"(gap {frac:.2f} of a space)")
            elif frac >= GAP_WARN:
                n_warn += 1
                rep.add("C2", "WARN",
                        f"{word!r} in {font} {size:g}/{weight} has a loose "
                        f"intra-word gap ({frac:.2f} of a space)")

    rep.metrics["typography_words_checked"] = float(len(seen))
    rep.metrics["typography_worst_gap"] = round(worst, 3)
    rep.metrics["typography_failures"] = float(n_fail)
    rep.metrics["typography_warnings"] = float(n_warn)


# =========================================================================
# FRAME / OCR — analysis of the render
# =========================================================================

def sample_frames(video: Path, workdir: Path, every: float) -> list[Path]:
    subprocess.run(["ffmpeg", "-v", "error", "-i", str(video),
                    "-vf", f"fps=1/{every},scale=1280:-1",
                    str(workdir / "f_%04d.png")],
                   check=False, capture_output=True)
    return sorted(workdir.glob("f_*.png"))


def check_frames(video: Path, rep: Report, every: float, expected: list[str]) -> None:
    import numpy as np
    from PIL import Image

    with tempfile.TemporaryDirectory() as td:
        frames = sample_frames(video, Path(td), every)
        if not frames:
            rep.add("D8", "WARN", "no frames extracted from video")
            return
        rep.ran("A5", "B2")

        neg_space, hue_counts = [], []
        for fp in frames:
            arr = np.asarray(Image.open(fp).convert("RGB"))
            flat = arr.reshape(-1, 3)
            # background = the single most common colour in the frame
            q = (flat // 24 * 24)
            uniq, cnt = np.unique(q, axis=0, return_counts=True)
            bg = uniq[cnt.argmax()]
            neg_space.append(float(cnt.max() / len(flat)))

            # distinct saturated hues, ignoring greys and near-background
            fg = q[(np.abs(q.astype(int) - bg.astype(int)).sum(1) > 40)]
            if len(fg):
                mx, mn = fg.max(1).astype(int), fg.min(1).astype(int)
                sat = fg[(mx - mn) > 40]
                if len(sat):
                    hu, hc = np.unique(sat // 48 * 48, axis=0, return_counts=True)
                    hue_counts.append(int((hc > len(flat) * 0.0004).sum()))
                else:
                    hue_counts.append(0)
            else:
                hue_counts.append(0)

        med_neg = float(np.median(neg_space))
        med_hue = float(np.median(hue_counts)) if hue_counts else 0.0
        rep.metrics["negative_space_median"] = round(med_neg, 3)
        rep.metrics["hues_per_frame_median"] = med_hue

        if med_neg < MIN_NEGATIVE_SPACE:
            rep.add("A5", "WARN",
                    f"negative space {med_neg:.0%} below {MIN_NEGATIVE_SPACE:.0%} "
                    f"— frame is crowded")
        if med_hue > MAX_HUES_PER_FRAME:
            rep.add("B2", "WARN",
                    f"{med_hue:.0f} distinct hues per frame (max {MAX_HUES_PER_FRAME})")

        # typography is measured from glyph geometry, not OCR — see
        # check_typography(). OCR on frames proved unreliable here.


def check_ocr(frames: list[Path], rep: Report, expected: list[str]) -> None:
    """C2 — phantom word gaps.

    Compound labels are the tell: a font with broken shaping renders
    "LangChain" as "Lang Chain". We look for each expected compound word in
    the OCR text and, when absent, check whether a split version is present.
    """
    rep.ran("C2")
    seen: set[str] = set()
    for fp in frames[: min(len(frames), 40)]:
        r = subprocess.run(["tesseract", str(fp), "stdout", "--psm", "11"],
                           capture_output=True, text=True)
        seen.update(WORDISH.findall(r.stdout))

    # only compound-looking tokens can exhibit the bug
    targets = set()
    for s in expected:
        for tok in WORDISH.findall(s):
            if len(tok) >= 7 and re.search(r"[a-z][A-Z]", tok):
                targets.add(tok)
            elif len(tok) >= 9:
                targets.add(tok)
    if not targets:
        rep.metrics["ocr_compound_words_checked"] = 0.0
        return

    broken = []
    for tok in sorted(targets):
        if tok in seen:
            continue
        # is a prefix+suffix split of it present instead?
        for i in range(3, len(tok) - 2):
            a, b = tok[:i], tok[i:]
            if a in seen and b in seen:
                broken.append((tok, f"{a} {b}"))
                break
    rep.metrics["ocr_compound_words_checked"] = float(len(targets))
    rep.metrics["ocr_phantom_gaps"] = float(len(broken))
    for tok, split in broken:
        rep.add("C2", "BLOCK",
                f"phantom word gap: {tok!r} rendered as {split!r}")


# =========================================================================

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--scene", type=Path, help="Manim scene .py")
    ap.add_argument("--video", type=Path, help="rendered mp4")
    ap.add_argument("--every", type=float, default=2.0)
    ap.add_argument("--reward", type=Path, default=None,
                    help="write Harbor-compatible reward.json here")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    if not args.scene and not args.video:
        sys.exit("need --scene and/or --video")

    rep = Report()
    if args.scene:
        check_source(args.scene, rep)
    expected = rep.metrics.pop("_expected_strings", [])
    specs = rep.metrics.pop("_type_specs", [])
    if specs:
        check_typography(specs, rep)
    if args.video:
        check_frames(args.video, rep, args.every, expected)

    blocks = [f for f in rep.findings if f.severity == "BLOCK"]
    warns = [f for f in rep.findings if f.severity == "WARN"]
    infos = [f for f in rep.findings if f.severity == "INFO"]

    # reward: 1.0 clean, 0 if any BLOCK, else degraded by warnings
    reward = 0.0 if blocks else max(0.0, 1.0 - 0.1 * len(warns))
    rep.metrics["blocks"] = float(len(blocks))
    rep.metrics["warns"] = float(len(warns))
    rep.metrics["reward"] = round(reward, 3)

    if args.json:
        print(json.dumps({
            "reward": reward,
            "metrics": rep.metrics,
            "findings": [vars(f) for f in rep.findings],
        }, indent=2))
    else:
        print()
        for f in blocks + warns + infos:
            tag = {"BLOCK": "BLOCK", "WARN": " WARN", "INFO": " info"}[f.severity]
            print(f"  [{tag}] {f.rule:<4} {f.message}")
        if not rep.findings:
            print("  no findings")
        print(f"\n  rules checked: {len(rep.checked)}  "
              f"blocks: {len(blocks)}  warns: {len(warns)}  "
              f"reward: {reward:.2f}\n")

    if args.reward:
        args.reward.parent.mkdir(parents=True, exist_ok=True)
        args.reward.write_text(json.dumps(
            {k: v for k, v in rep.metrics.items()
             if isinstance(v, (int, float))}, indent=2))

    return 1 if blocks else 0


if __name__ == "__main__":
    sys.exit(main())
