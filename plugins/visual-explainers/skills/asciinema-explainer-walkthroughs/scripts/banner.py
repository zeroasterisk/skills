#!/usr/bin/env python3
"""
ANSI Color Double-Border Banner Header Generator
Creates cleanly formatted, width-calibrated scenario banners for terminal recordings.
Supports double, single, and rounded borders, ANSI colors, and auto-centered text.
"""

import argparse
import os
import re
import sys
from typing import List, Optional

ANSI_COLORS = {
    "cyan": "\033[1;36m",
    "green": "\033[1;32m",
    "blue": "\033[1;34m",
    "magenta": "\033[1;35m",
    "yellow": "\033[1;33m",
    "red": "\033[1;31m",
    "white": "\033[1;37m",
    "gray": "\033[0;90m",
    "bold": "\033[1m",
    "dim_yellow": "\033[0;33m",
    "reset": "\033[0m",
}

BORDER_STYLES = {
    "double": {"tl": "╔", "tr": "╗", "bl": "╚", "br": "╝", "h": "═", "v": "║"},
    "single": {"tl": "┌", "tr": "┐", "bl": "└", "br": "┘", "h": "─", "v": "│"},
    "rounded": {"tl": "╭", "tr": "╮", "bl": "╰", "br": "╯", "h": "─", "v": "│"},
}

ANSI_ESCAPE_RE = re.compile(r"\x1b(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])")


def strip_ansi(text: str) -> str:
    """Remove ANSI escape codes to calculate visual string length."""
    return ANSI_ESCAPE_RE.sub("", text)


def visual_len(text: str) -> int:
    """Return the visual display length of a string (ignoring ANSI codes)."""
    return len(strip_ansi(text))


def make_banner(
    title: str,
    subtitle: Optional[str] = None,
    step: Optional[int] = None,
    step_label: Optional[str] = None,
    width: int = 112,
    color: str = "cyan",
    style: str = "double",
    align: str = "left",
    no_color: bool = False,
) -> str:
    """
    Generate a double-border formatted ANSI banner string.
    """
    if no_color or os.environ.get("NO_COLOR") or os.environ.get("TERM") == "dumb":
        c_border = c_title = c_sub = c_reset = ""
    else:
        c_border = ANSI_COLORS.get(color.lower(), ANSI_COLORS["cyan"])
        c_title = ANSI_COLORS["white"]
        c_sub = ANSI_COLORS["dim_yellow"]
        c_reset = ANSI_COLORS["reset"]

    b = BORDER_STYLES.get(style, BORDER_STYLES["double"])
    inner_width = max(20, width - 2)

    # Construct Title Line
    if step is not None:
        prefix = f"STEP {step}: "
    elif step_label:
        prefix = f"{step_label}: "
    else:
        prefix = ""

    full_title = f"{prefix}{title}".strip()

    # Construct Top & Bottom borders
    top_line = f"{c_border}{b['tl']}{b['h'] * inner_width}{b['tr']}{c_reset}"
    bottom_line = f"{c_border}{b['bl']}{b['h'] * inner_width}{b['br']}{c_reset}"

    def pad_line(content_str: str, raw_color: str) -> str:
        vlen = visual_len(content_str)
        if vlen > inner_width - 4:
            # Truncate with ellipsis if text exceeds width
            content_str = strip_ansi(content_str)[: inner_width - 7] + "..."
            vlen = len(content_str)

        if align == "center":
            total_padding = inner_width - vlen
            left_pad = total_padding // 2
            right_pad = total_padding - left_pad
            return f"{c_border}{b['v']}{c_reset}{' ' * left_pad}{raw_color}{content_str}{c_reset}{' ' * right_pad}{c_border}{b['v']}{c_reset}"
        else:
            # Left align with 2 space margin
            left_pad = 2
            right_pad = inner_width - vlen - left_pad
            return f"{c_border}{b['v']}{c_reset}{' ' * left_pad}{raw_color}{content_str}{c_reset}{' ' * max(0, right_pad)}{c_border}{b['v']}{c_reset}"

    lines = [top_line, pad_line(full_title, c_title)]

    if subtitle:
        lines.append(pad_line(subtitle, c_sub))

    lines.append(bottom_line)
    return "\n".join(lines)


def print_banner(
    title: str,
    subtitle: Optional[str] = None,
    step: Optional[int] = None,
    step_label: Optional[str] = None,
    width: int = 112,
    color: str = "cyan",
    style: str = "double",
    align: str = "left",
    no_color: bool = False,
) -> None:
    """Print the banner directly to stdout."""
    print(
        make_banner(
            title=title,
            subtitle=subtitle,
            step=step,
            step_label=step_label,
            width=width,
            color=color,
            style=style,
            align=align,
            no_color=no_color,
        )
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate ANSI scenario banners.")
    parser.add_argument("title", nargs="?", default="DEMO TITLE • INTERACTIVE EXPLAINER", help="Banner title text")
    parser.add_argument("subtitle", nargs="?", default=None, help="Banner subtitle or description")
    parser.add_argument("--step", type=int, default=None, help="Step number (e.g. 1, 2, 3)")
    parser.add_argument("--step-label", type=str, default=None, help="Custom step label (e.g. 'SCENARIO 1')")
    parser.add_argument("--width", type=int, default=112, help="Terminal column width (default: 112)")
    parser.add_argument("--color", type=str, default="cyan", choices=list(ANSI_COLORS.keys()), help="Border color")
    parser.add_argument("--style", type=str, default="double", choices=list(BORDER_STYLES.keys()), help="Border style")
    parser.add_argument("--align", type=str, default="left", choices=["left", "center"], help="Text alignment")
    parser.add_argument("--no-color", action="store_true", help="Disable ANSI color codes")

    args = parser.parse_args()

    # Pre-set step color mappings if step is given and color is default
    if args.step is not None and args.color == "cyan":
        color_map = {0: "cyan", 1: "green", 2: "blue", 3: "magenta", 4: "yellow", 5: "cyan"}
        args.color = color_map.get(args.step, "cyan")

    print_banner(
        title=args.title,
        subtitle=args.subtitle,
        step=args.step,
        step_label=args.step_label,
        width=args.width,
        color=args.color,
        style=args.style,
        align=args.align,
        no_color=args.no_color,
    )


if __name__ == "__main__":
    main()
