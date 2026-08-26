"""Dataset B generator — one scene, one injectable defect per flag.

Baseline (no flags) is a spec-conformant clip per ../reference/quality-spec.md.
Each ablation flips exactly ONE variable, so any grader preference between
baseline and ablation is attributable to that variable alone. Ground truth
is known by construction.

Usage:
    export PATH="/opt/homebrew/bin:$HOME/.local/bin:$PATH"
    MANIM=~/Workspaces/open-source/OpenMontage/.venv/bin/manim

    # baseline
    ABLATION=none $MANIM -qh --fps 60 ablation_scene.py AblationScene

    # each defect
    for d in font_ttc_bug rushed_pacing card_itis color_spray \
             text_flood light_bg cut_not_morph overlap_nodes; do
      ABLATION=$d $MANIM -qh --fps 60 ablation_scene.py AblationScene
    done

Renders land in media/videos/ablation_scene/1080p60/. Rename to opaque IDs
and normalize encodes before grading (see ../datasets/B_ablation_pairs.md).
"""

from __future__ import annotations

import os

from manim import (
    DOWN,
    LEFT,
    RIGHT,
    UP,
    Circle,
    Create,
    FadeIn,
    FadeOut,
    RegularPolygon,
    RoundedRectangle,
    Scene,
    Text,
    Transform,
    VGroup,
    config,
    smooth,
)

ABLATION = os.environ.get("ABLATION", "none").strip()

VALID = {
    "none", "font_ttc_bug", "rushed_pacing", "card_itis", "color_spray",
    "text_flood", "light_bg", "cut_not_morph", "overlap_nodes",
}
if ABLATION not in VALID:
    raise SystemExit(f"ABLATION={ABLATION!r} invalid. Choose from: {sorted(VALID)}")

# --- spec-conformant defaults (../reference/quality-spec.md) -------------------------
BG = "#0E0E10"
FG_TEXT = "#FFFFFF"
BLUE = "#58C4DD"       # generic explanatory accent
GOLD = "#F0AC5F"       # secondary emphasis
GREEN = "#34A853"      # RESERVED: confirmed/success only
FONT = "Roboto"
FILL_OP = 0.12
STROKE_W = 2.5

# --- per-ablation overrides ------------------------------------------------
if ABLATION == "light_bg":            # violates A1
    BG, FG_TEXT = "#F8F9FA", "#3C4043"
if ABLATION == "font_ttc_bug":        # violates C1/C2 (phantom word gaps)
    FONT = "Helvetica Neue"
if ABLATION == "card_itis":           # violates A2/A3
    FILL_OP, STROKE_W = 0.95, 5.0

# 8 unreserved hues + decorative use of a reserved color; violates B1/B2/B3
SPRAY = ["#FF00AA", "#00FFCC", "#FFD400", "#7B2FF7",
         "#FF6B00", "#00A3FF", "#34A853", "#EA4335"]

RUSH = 0.25 if ABLATION == "rushed_pacing" else 1.0   # violates D1/D2/D3

config.background_color = BG

# Compound words — the exact strings that expose the .ttc shaping bug.
NODE_LABELS = ["LangChain", "Pydantic", "OpenClaw", "Antigravity"]


def rt(x: float) -> float:
    """run_time, scaled by the pacing ablation."""
    return max(0.05, x * RUSH)


def node_color(i: int) -> str:
    return SPRAY[i % len(SPRAY)] if ABLATION == "color_spray" else BLUE


def make_node(label: str, color: str) -> VGroup:
    txt = Text(label, font=FONT, font_size=15, color=color, weight="BOLD")
    body = RoundedRectangle(
        corner_radius=0.22,
        width=max(1.5, txt.width + 0.5), height=0.6,
        fill_color=color, fill_opacity=FILL_OP,
        stroke_color=color, stroke_width=STROKE_W,
    )
    txt.move_to(body.get_center())
    return VGroup(body, txt)


class AblationScene(Scene):
    """~30s clip: nodes appear → travel to issuer → confirmed → caption."""

    def construct(self):
        self.wait(rt(0.8))

        # --- Beat 1: nodes appear -----------------------------------------
        nodes = VGroup(*[
            make_node(l, node_color(i)) for i, l in enumerate(NODE_LABELS)
        ])
        nodes.arrange(DOWN, buff=0.55).move_to(LEFT * 4.0)

        if ABLATION == "overlap_nodes":      # violates A7
            nodes[1].shift(UP * 0.42 + RIGHT * 0.30)
            nodes[2].shift(DOWN * 0.40 + RIGHT * 0.22)

        for n in nodes:
            self.play(FadeIn(n, run_time=rt(1.6)))
        self.wait(rt(2.0))

        # --- Beat 2: the issuer -------------------------------------------
        issuer = RegularPolygon(
            n=6, radius=1.15,
            stroke_color=GOLD, stroke_width=STROKE_W,
            fill_color=GOLD, fill_opacity=min(FILL_OP, 0.06),
        ).move_to(RIGHT * 3.6)
        self.play(Create(issuer, run_time=rt(2.0)))
        self.wait(rt(1.5))

        # --- Beat 3: text ---------------------------------------------------
        if ABLATION == "text_flood":         # violates C3/C4/C6
            flood = VGroup(*[
                Text(t, font=FONT, font_size=17, color=FG_TEXT)
                for t in [
                    "Workload identity is issued at process start",
                    "SPIFFE / mTLS attests the agent",
                    "Independent of the calling user",
                    "Enforced at the gateway boundary",
                    "Audited via OpenTelemetry spans",
                ]
            ]).arrange(DOWN, buff=0.22).move_to(DOWN * 2.2)
            # appears WITH the visual, not after — violates C4
            self.play(FadeIn(flood, run_time=rt(1.2)),
                      issuer.animate.set_stroke(GOLD), run_time=rt(1.2))
            self.wait(rt(1.2))
        else:
            flood = None

        # --- Beat 4: confirmed (reserved GREEN, licensed here only) -------
        badge = Circle(
            radius=0.34, stroke_color=GREEN, stroke_width=STROKE_W,
            fill_color=GREEN, fill_opacity=min(FILL_OP + 0.06, 0.95),
        ).move_to(issuer.get_center())

        if ABLATION == "cut_not_morph":      # violates D4
            self.play(FadeOut(issuer, run_time=rt(0.9)))
            self.play(FadeIn(badge, run_time=rt(0.9)))
        else:
            self.play(Transform(issuer, badge, run_time=rt(2.0),
                                rate_func=smooth))
        self.wait(rt(2.5))

        # --- Beat 5: single caption, AFTER the visual resolves ------------
        if flood is None:
            caption = Text("Identity, issued once, at first breath.",
                           font=FONT, font_size=24, color=FG_TEXT)
            caption.move_to(DOWN * 2.6)
            self.play(FadeIn(caption, run_time=rt(1.8)))
            self.wait(rt(3.0))
            tail = caption
        else:
            tail = flood

        self.play(FadeOut(VGroup(nodes, issuer, tail), run_time=rt(1.5)))
        self.wait(rt(0.8))
