#!/usr/bin/env python3
"""Calibration generator — narration-timed pacing x on-screen-text sweep.

Separate from ablation_scene.py on purpose. That file injects *defects* with
known-bad answers, to test whether a grader can see them. This file sweeps
*legitimate design choices* where the right answer is genuinely unknown and
only a human can settle it.

Why this exists
---------------
Copying 3Blue1Brown's very sparse, very patient grammar wholesale produced a
clip a human described as "not enough explainer text, and the animations are
too slow", while our older denser/faster work was "too verbose, too fast".
Both critiques are real, and they point at an interior optimum rather than a
monotone "more is better".

The resolution is that these videos are NARRATED. That changes two things:

  1. Beat duration is not a taste call. A beat should last about as long as
     it takes to SAY its line. So timing is derived from the narration script
     at a given speaking rate, not from hand-tuned run_time constants. This
     is why script-first is the correct order of work: write the narration,
     then animate to it.

  2. On-screen text does not have to carry the explanation, because the voice
     does. Its job is to anchor terms the ear cannot spell, and to keep the
     frame comprehensible when muted (a large share of viewers). That is a
     different job than "explain the concept", and it implies short anchors
     rather than full sentences — but not zero text.

Axes
    WPM   = 175 | 205 | 235        speaking rate; 205 = measured reference median
    TEXT  = none | anchor | caption
              none    - visual only; the voice carries all of it
              anchor  - a few words per beat: the term being introduced
              caption - the narration line rendered verbatim on screen

Content, layout, colors and animation order are identical across every
variant, so a pairwise preference is attributable to the axis alone.

Usage:
    WPM=150 TEXT=anchor manim -qh --fps 60 variant_scene.py VariantScene
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
    Flash,
    Group,
    RegularPolygon,
    Scene,
    Text,
    Transform,
    VGroup,
    config,
    smooth,
)

WPM = int(os.environ.get("WPM", "205"))
TEXT = os.environ.get("TEXT", "anchor").strip()

if WPM not in (175, 205, 235):
    raise SystemExit(f"WPM={WPM} must be 175|205|235  (reference median ~205)")
if TEXT not in {"none", "anchor", "caption"}:
    raise SystemExit(f"TEXT={TEXT!r} must be none|anchor|caption")

WPS = WPM / 60.0
TAIL = {175: 0.55, 205: 0.40, 235: 0.28}[WPM]  # ~10% silence, per reference

BG = "#0E0E10"
FG = "#FFFFFF"
DIM = "#BBBBBB"
BLUE = "#58C4DD"
GOLD = "#F0AC5F"
GREEN = "#34A853"          # RESERVED: confirmed/success only
FONT = "Roboto"

config.background_color = BG

# The narration script IS the timing source. Each beat: (line, anchor).
SCRIPT = {
    "start":  ("An agent process starts up, with no credentials of its own.",
               "Agent starts"),
    "issuer": ("The platform runs a workload certificate authority that can "
               "attest what that process actually is.",
               "Workload CA"),
    "issue":  ("It signs a short lived identity for the process itself, and "
               "this happens at startup, before any user request arrives.",
               "Identity issued"),
    "carry":  ("From then on the agent carries that identity into every call "
               "it makes.",
               "Every call, attested"),
}


def say(key: str) -> float:
    """Seconds this beat's narration takes at the current speaking rate."""
    words = len(SCRIPT[key][0].split())
    return words / WPS + TAIL


def label(txt: str, size: int = 15, color: str = BLUE) -> Text:
    return Text(txt, font=FONT, font_size=size, color=color)


def node(name: str, color: str = BLUE) -> VGroup:
    c = Circle(radius=0.34, stroke_color=color, stroke_width=2.5,
               fill_color=color, fill_opacity=0.12)
    t = label(name, 15, color)
    t.next_to(c, DOWN, buff=0.16)
    return VGroup(c, t)


class VariantScene(Scene):
    """Identical content and animation at every setting; only timing and
    on-screen text vary."""

    def construct(self):
        # ---- beat: agent starts -----------------------------------------
        budget = say("start")
        agent = node("ADK Agent").move_to(LEFT * 4.0 + UP * 0.3)
        anim = min(1.8, budget * 0.45)
        self.play(FadeIn(agent, run_time=anim))
        self.beat_text("start", budget - anim)

        # ---- beat: the issuer -------------------------------------------
        budget = say("issuer")
        issuer = RegularPolygon(
            n=6, radius=1.05, stroke_color=GOLD, stroke_width=2.5,
            fill_color=GOLD, fill_opacity=0.05,
        ).move_to(RIGHT * 3.6 + UP * 0.3)
        anim = min(2.0, budget * 0.45)
        self.play(Create(issuer, run_time=anim))
        self.beat_text("issuer", budget - anim)

        # ---- beat: issuance ---------------------------------------------
        budget = say("issue")
        move_t = min(2.2, budget * 0.30)
        self.play(agent.animate.move_to(RIGHT * 1.5 + UP * 0.3),
                  run_time=move_t, rate_func=smooth)
        self.play(Flash(issuer.get_center(), color=GREEN, flash_radius=0.85,
                        num_lines=10, run_time=min(1.1, budget * 0.16)))
        badge = Circle(radius=0.3, stroke_color=GREEN, stroke_width=2.5,
                       fill_color=GREEN, fill_opacity=0.18)
        badge.move_to(issuer.get_center())
        morph_t = min(1.6, budget * 0.22)
        self.play(Transform(issuer, badge, run_time=morph_t, rate_func=smooth))
        used = move_t + min(1.1, budget * 0.16) + morph_t
        self.beat_text("issue", budget - used)

        # ---- beat: carry it home -----------------------------------------
        budget = say("carry")
        home = LEFT * 4.0 + UP * 0.3
        anim = min(2.2, budget * 0.45)
        self.play(agent.animate.move_to(home),
                  issuer.animate.scale(0.55).move_to(
                      home + RIGHT * 0.62 + UP * 0.5),
                  run_time=anim, rate_func=smooth)
        self.beat_text("carry", budget - anim)

        # ---- close --------------------------------------------------------
        closer = Text("Identity belongs to the process, not the caller.",
                      font=FONT, font_size=22, color=FG)
        closer.move_to(DOWN * 2.5)
        self.play(FadeIn(closer, run_time=min(1.5, 6 / WPS)))
        self.wait(max(0.8, 9 / WPS))

        # Group, not VGroup: Flash and friends leave plain Mobjects behind.
        self.play(FadeOut(Group(*self.mobjects), run_time=1.0))

    # -- on-screen text -----------------------------------------------------
    def beat_text(self, key: str, hold: float) -> None:
        """Render this beat's text, then hold for the remaining narration time.

        `hold` is whatever is left of the spoken line after the animation, so
        total beat length always matches the narration regardless of TEXT.
        """
        hold = max(0.25, hold)
        line, anchor = SCRIPT[key]

        if TEXT == "none":
            self.wait(hold)
            return

        s = anchor if TEXT == "anchor" else line
        size = 22 if TEXT == "anchor" else 17
        t = Text(s, font=FONT, font_size=size, color=DIM)
        if t.width > config.frame_width - 1.6:
            t.scale_to_fit_width(config.frame_width - 1.6)
        t.move_to(DOWN * 1.9)

        fade = min(0.7, hold * 0.3)
        self.play(FadeIn(t, run_time=fade))
        self.wait(max(0.1, hold - 2 * fade))
        self.play(FadeOut(t, run_time=fade))
