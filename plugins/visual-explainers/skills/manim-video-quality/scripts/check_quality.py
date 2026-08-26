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
# Calibrated against 9 reference clips in the target style, measured with
# THESE metric definitions (borrowing constants from a differently-defined
# measurement is how you get thresholds that look rigorous and aren't):
#     ink coverage        median 0.111  range 0.036 - 0.289
#     saturated hues      median 1.0    range 0 - 4
#     static frame-pairs  median 58.9%  range 26.6 - 73.4
#     longest static run  median 5.0s   range 1.8 - 7.0
#
# The reference is overwhelmingly STILL. An earlier plan to flag static holds
# as "dead air" would have rejected the reference corpus itself. Stillness is
# only a defect when nothing is being said over it, so the static check is
# narration-aware and is skipped entirely when an audio track is present.
INK_MIN, INK_MAX = 0.02, 0.35          # too empty / too crowded
MAX_HUES_PER_FRAME = 4                 # reference max
SILENT_STATIC_RUN_MAX = 7.0            # reference max is 7.0s — but always narrated
# Fraction of pixels that must change for a frame-pair to count as moving.
# Mean-absolute-difference was tried first and is unusable here: it is
# confounded with ink density, so a sparse scene reads as 100% static even
# while elements visibly move. Counting *changed pixels* is density-neutral.
STATIC_PIXEL_DELTA = 8                 # per-pixel grey change that counts
STATIC_AREA_FRAC = 0.0015              # <0.15% of pixels changed => static

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


# Populated per-file by check_source(): module-level numeric constants and
# simple arithmetic helper functions. Without these, a scene written the
# normal way — `fill_opacity=FILL_OP`, `run_time=rt(1.6)` — is invisible to
# static analysis, which is how an injected card-itis defect (0.95 opacity)
# and a 4x speed-up both passed clean.
_CONSTS: dict = {}
_HELPERS: dict = {}


def _num(node, depth: int = 0):
    if depth > 6:
        return None
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
        return float(node.value)
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.USub):
        v = _num(node.operand, depth + 1)
        return -v if v is not None else None
    if isinstance(node, ast.Name):
        return _CONSTS.get(node.id)
    if isinstance(node, ast.BinOp):
        a, b = _num(node.left, depth + 1), _num(node.right, depth + 1)
        if a is None or b is None:
            return None
        try:
            if isinstance(node.op, ast.Add):  return a + b
            if isinstance(node.op, ast.Sub):  return a - b
            if isinstance(node.op, ast.Mult): return a * b
            if isinstance(node.op, ast.Div):  return a / b if b else None
        except (TypeError, ZeroDivisionError):
            return None
        return None
    if isinstance(node, ast.Call):
        fn = getattr(node.func, "id", None)
        args = [_num(a, depth + 1) for a in node.args]
        if fn in ("min", "max") and args and all(a is not None for a in args):
            return (min if fn == "min" else max)(args)
        # single-expression arithmetic helper, e.g. def rt(x): return max(.12, x*RUSH)
        h = _HELPERS.get(fn)
        if h and len(args) == len(h["params"]) and all(a is not None for a in args):
            saved = dict(_CONSTS)
            _CONSTS.update(dict(zip(h["params"], args)))
            try:
                return _num(h["expr"], depth + 1)
            finally:
                _CONSTS.clear()
                _CONSTS.update(saved)
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

    _CONSTS.clear(); _HELPERS.clear()
    for n in tree.body:
        if isinstance(n, ast.Assign) and len(n.targets) == 1 and isinstance(n.targets[0], ast.Name):
            v = _num(n.value)
            if v is not None:
                _CONSTS[n.targets[0].id] = v
        elif isinstance(n, ast.FunctionDef):
            # a docstring makes the body length 2, which previously caused
            # every documented helper to be skipped — and rt() is documented
            body = [b for b in n.body
                    if not (isinstance(b, ast.Expr)
                            and isinstance(b.value, ast.Constant)
                            and isinstance(b.value.value, str))]
            if len(body) == 1 and isinstance(body[0], ast.Return):
                _HELPERS[n.name] = {"params": [a.arg for a in n.args.args],
                                    "expr": body[0].value}

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

    # C3 simultaneous text — a group holding several Text() at once
    rep.ran("C3")
    worst_group = 0
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and getattr(node.func, "id", "") in ("VGroup", "Group"):
            def _texts(x):
                return sum(1 for s in ast.walk(x)
                           if isinstance(s, ast.Call)
                           and getattr(s.func, "id", getattr(s.func, "attr", ""))
                           in ("Text", "MarkupText", "Tex", "MathTex"))

            # A comprehension has ONE syntactic Text() but N runtime ones.
            # Counting syntax missed a 5-line text flood entirely.
            n_text, counted = 0, set()
            for sub in ast.walk(node):
                if isinstance(sub, (ast.ListComp, ast.GeneratorExp, ast.SetComp)):
                    inner = _texts(sub.elt)
                    if inner and sub.generators:
                        it = sub.generators[0].iter
                        n = len(it.elts) if isinstance(it, (ast.List, ast.Tuple)) else 1
                        n_text += inner * n
                        counted.update(id(s) for s in ast.walk(sub))
            n_text += sum(1 for s in ast.walk(node)
                          if id(s) not in counted and isinstance(s, ast.Call)
                          and getattr(s.func, "id", getattr(s.func, "attr", ""))
                          in ("Text", "MarkupText", "Tex", "MathTex"))
            worst_group = max(worst_group, n_text)
    rep.metrics["max_text_per_group"] = float(worst_group)
    if worst_group >= 3:
        rep.add("C3", "WARN",
                f"{worst_group} Text objects introduced together — with "
                f"narration the viewer can only read one line at a time")

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


def has_audio(video: Path) -> bool:
    r = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "a",
                        "-show_entries", "stream=codec_type", "-of", "csv=p=0",
                        str(video)], capture_output=True, text=True)
    return bool(r.stdout.strip())


def check_frames(video: Path, rep: Report, every: float, expected: list[str]) -> None:
    """Frame-level checks, calibrated against the reference corpus.

    Deliberately narrow. Earlier versions of this function measured
    "negative space" as the most-common-colour fraction and counted hues by
    clustering raw RGB; both returned near-identical values for every
    ablation including the clean baseline, i.e. they discriminated nothing.
    Anti-aliasing alone was inflating the hue count to ~9 against a reference
    median of 1.5. Those metrics were removed rather than tuned.
    """
    import numpy as np
    from PIL import Image

    rep.ran("A5", "B2")
    audio = has_audio(video)
    rep.metrics["has_audio"] = 1.0 if audio else 0.0

    with tempfile.TemporaryDirectory() as td:
        wd = Path(td)
        subprocess.run(["ffmpeg", "-v", "error", "-i", str(video), "-vf",
                        "fps=2,scale=640:-1", str(wd / "i_%04d.png")],
                       check=False, capture_output=True)
        ink_frames = sorted(wd.glob("i_*.png"))
        if not ink_frames:
            rep.add("D8", "WARN", "no frames extracted from video")
            return

        inks, hues = [], []
        for fp in ink_frames:
            arr = np.asarray(Image.open(fp).convert("RGB"))
            flat = arr.reshape(-1, 3)
            q = flat // 24 * 24
            uniq, cnt = np.unique(q, axis=0, return_counts=True)
            inks.append(1.0 - float(cnt.max()) / len(flat))

            hsv = np.asarray(Image.open(fp).convert("HSV")).reshape(-1, 3)
            sel = hsv[(hsv[:, 1] >= 64) & (hsv[:, 2] >= 38)]   # sat>=.25 val>=.15
            if len(sel):
                buckets = (sel[:, 0].astype(int) * 360 // 256) // 30
                _, bc = np.unique(buckets, return_counts=True)
                hues.append(int((bc > len(hsv) * 0.005).sum()))
            else:
                hues.append(0)

        med_ink = float(np.median(inks))
        med_hue = float(np.median(hues))
        rep.metrics["ink_coverage_median"] = round(med_ink, 4)
        rep.metrics["hues_per_frame_median"] = med_hue

        if med_ink < INK_MIN:
            rep.add("A5", "WARN",
                    f"ink coverage {med_ink:.1%} below {INK_MIN:.0%} — frame is "
                    f"nearly empty (reference median 11.6%)")
        elif med_ink > INK_MAX:
            rep.add("A5", "WARN",
                    f"ink coverage {med_ink:.1%} above {INK_MAX:.0%} — crowded "
                    f"(reference median 11.6%)")
        if med_hue > MAX_HUES_PER_FRAME:
            rep.add("B2", "WARN",
                    f"{med_hue:.0f} distinct saturated hues per frame "
                    f"(reference median 1.5, max 4)")

        # --- static holds, only meaningful without narration --------------
        subprocess.run(["ffmpeg", "-v", "error", "-i", str(video), "-vf",
                        "fps=5,scale=320:180,format=gray",
                        str(wd / "g_%04d.png")],
                       check=False, capture_output=True)
        gs = sorted(wd.glob("g_*.png"))
        if len(gs) > 2:
            prev = np.asarray(Image.open(gs[0]), dtype=np.int16)
            static, run, longest = 0, 0, 0
            for fp in gs[1:]:
                cur = np.asarray(Image.open(fp), dtype=np.int16)
                changed = float((np.abs(cur - prev) > STATIC_PIXEL_DELTA).mean())
                if changed < STATIC_AREA_FRAC:
                    static += 1
                    run += 1
                    longest = max(longest, run)
                else:
                    run = 0
                prev = cur
            pairs = len(gs) - 1
            rep.metrics["static_pair_pct"] = round(100 * static / pairs, 1)
            rep.metrics["longest_static_run_s"] = round(longest / 5.0, 2)
            rep.ran("D3")
            if not audio and longest / 5.0 > SILENT_STATIC_RUN_MAX:
                rep.add("D3", "WARN",
                        f"{longest/5.0:.1f}s of unchanging frame with no audio "
                        f"track — reads as dead air. The reference holds "
                        f"stills this long, but always under narration.")


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
