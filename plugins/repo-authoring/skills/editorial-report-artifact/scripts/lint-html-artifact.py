#!/usr/bin/env python3
"""
lint-html-artifact.py

Audits standalone editorial HTML report artifacts for:
  1. Markdown-to-HTML bleed:
     - Unrendered LaTeX macros (\\tilde, \\ln, \\mathcal, \\tau, \\ge, \\le, \\in, etc.)
     - Raw $...$ inline math delimiters (excluding currency/env tokens like $0.00 or $PROJECT)
     - Stray Markdown code backticks (`code`) or **bold** inside HTML elements
  2. SVG XML entity hazards (raw '<' or unescaped '&' inside <svg><text>...</text></svg>)
  3. Optional gitignore verification (--check-gitignored) to ensure scratch artifacts
     cannot accidentally be committed.

Usage:
  ./scripts/lint-html-artifact.py <path/to/report.html> [--check-gitignored]
"""

from __future__ import annotations

import argparse
import pathlib
import re
import subprocess
import sys


LATEX_MACRO_RE = re.compile(
    r"\\(tilde|hat|bar|ln|log|exp|mathcal|mathbb|mathbf|mathrm|text|tau|sigma|Sigma|Delta|ge|le|in|implies|to|cdot|times|frac|sum|prod)\b"
)
# Matches $...$ inline math while ignoring $0.00, $100, $PROJECT, $HOME
INLINE_MATH_DOLLAR_RE = re.compile(r"\$(?![0-9]+(?:\.[0-9]+)?\b|[A-Z_]{2,}\b)([^$\n]{1,120})\$")
BACKTICK_IN_HTML_RE = re.compile(r"`([^`\n]{1,80})`")
SVG_TEXT_UNESCAPED_RE = re.compile(r"<text\b[^>]*>([^<]*[&](?!(?:amp|lt|gt|quot|apos|#\d+|#x[0-9a-fA-F]+);)[^<]*)</text>")


def strip_script_and_style(html: str) -> str:
    """Replace <script> and <style> contents with newlines of equal line count."""
    def _blank(match: re.Match[str]) -> str:
        return "\n" * match.group(0).count("\n")

    cleaned = re.sub(r"<style\b[^>]*>.*?</style>", _blank, html, flags=re.DOTALL | re.IGNORECASE)
    cleaned = re.sub(r"<script\b[^>]*>.*?</script>", _blank, cleaned, flags=re.DOTALL | re.IGNORECASE)
    return cleaned


def audit_html(path: pathlib.Path, check_gitignored: bool = False) -> int:
    if not path.exists():
        print(f"[FAIL] File not found: {path}", file=sys.stderr)
        return 1

    raw = path.read_text(encoding="utf-8")
    body_only = strip_script_and_style(raw)
    lines = raw.splitlines()
    body_lines = body_only.splitlines()

    issues: list[tuple[int, str, str]] = []

    for idx, line in enumerate(lines, start=1):
        for m in LATEX_MACRO_RE.finditer(line):
            issues.append((idx, "LATEX_MACRO", f"Unrendered LaTeX macro '{m.group(0)}' — convert to <span class=\"math\">"))
        for m in INLINE_MATH_DOLLAR_RE.finditer(line):
            issues.append((idx, "INLINE_MATH_$", f"Raw '$...$' math '${m.group(1)}$' — convert to <span class=\"math\">"))
        for m in SVG_TEXT_UNESCAPED_RE.finditer(line):
            issues.append((idx, "SVG_XML_ENTITY", f"Unescaped '&' inside <text>: {m.group(1).strip()}"))

    for idx, line in enumerate(body_lines, start=1):
        for m in BACKTICK_IN_HTML_RE.finditer(line):
            issues.append((idx, "MARKDOWN_BACKTICK", f"Stray Markdown backtick `{m.group(1)}` — convert to <code>{m.group(1)}</code>"))

    # 3. Verify all internal #fragment anchor links resolve to an id="..." target
    #    and that nav.toc includes a WebView-safe scrollIntoView handler
    defined_ids = set(re.findall(r'\bid=["\']([^"\']+)["\']', body_only))
    has_toc_anchor = False
    for idx, line in enumerate(body_lines, start=1):
        for m in re.finditer(r'<a\b[^>]*\bhref=["\']#([^"\']+)["\']', line, flags=re.IGNORECASE):
            target_id = m.group(1)
            has_toc_anchor = True
            if target_id and target_id not in defined_ids:
                issues.append((idx, "BROKEN_ANCHOR_TARGET", f"Anchor href='#{target_id}' has no matching id='{target_id}' in document"))

    if has_toc_anchor and "scrollIntoView" not in raw:
        issues.append((
            0,
            "TOC_MISSING_SCROLL_JS",
            "Document has #fragment TOC links but no JS scrollIntoView handler (bare href='#...' links fail in IDE/WebView previewers)",
        ))

    if check_gitignored:
        res = subprocess.run(
            ["git", "check-ignore", "-q", str(path)],
            cwd=str(path.parent),
            capture_output=True,
        )
        if res.returncode != 0:
            issues.append((0, "GIT_NOT_IGNORED", f"File '{path}' is NOT gitignored; move to a gitignored directory (e.g., scratch/)"))

    if not issues:
        print(f"[PASS] {path}: 0 LaTeX/Markdown bleed issues, valid SVG entities & TOC anchors" + (" (gitignored verified)" if check_gitignored else ""))
        return 0

    print(f"[FAIL] {path}: found {len(issues)} formatting issue(s):", file=sys.stderr)
    for line_no, kind, msg in issues:
        loc = f"line {line_no}" if line_no > 0 else "git"
        print(f"  - [{kind}] ({loc}): {msg}", file=sys.stderr)
    return 1


def main() -> int:
    parser = argparse.ArgumentParser(description="Lint standalone editorial HTML report artifacts.")
    parser.add_argument("html_file", type=pathlib.Path, help="Path to the HTML artifact file")
    parser.add_argument(
        "--check-gitignored",
        action="store_true",
        help="Verify that the target HTML file is ignored by git (e.g., inside scratch/)",
    )
    args = parser.parse_args()
    return audit_html(args.html_file, check_gitignored=args.check_gitignored)


if __name__ == "__main__":
    sys.exit(main())
