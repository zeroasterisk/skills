#!/usr/bin/env python3
"""
Asciinema Explainer Walkthrough Builder & Preview Server
- Parses .cast recordings and extracts chapter markers and text transcripts.
- Injects markers and transcripts into player_template.html to create a standalone index.html.
- Validates .cast schema compliance and verifies zero-traceback execution.
- Optionally serves the interactive walkthrough via a lightweight HTTP server for rapid human review.
"""

import argparse
import http.server
import json
import os
import re
import socketserver
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

REPO_ROOT = Path(__file__).resolve().parent.parent
TEMPLATE_PATH = REPO_ROOT / "templates" / "player_template.html"

ANSI_ESCAPE_RE = re.compile(r"\x1b(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])")


def strip_ansi(text: str) -> str:
    """Remove ANSI escape sequences."""
    return ANSI_ESCAPE_RE.sub("", text)


def format_time(seconds: float) -> str:
    """Format seconds into MM:SS string."""
    mins = int(seconds // 60)
    secs = int(seconds % 60)
    return f"{mins:02d}:{secs:02d}"


def parse_cast_file(cast_path: Path) -> Dict[str, Any]:
    """Parse .cast file to extract header, events, markers, and plain-text transcript."""
    if not cast_path.exists():
        raise FileNotFoundError(f"Cast file not found: {cast_path}")

    with open(cast_path, "r", encoding="utf-8") as f:
        raw_lines = [line.strip() for line in f if line.strip()]

    if not raw_lines:
        raise ValueError(f"Empty cast file: {cast_path}")

    header = json.loads(raw_lines[0])
    events = [json.loads(line) for line in raw_lines[1:]]

    markers: List[Tuple[float, str]] = []
    text_chunks: List[str] = []

    for ev in events:
        ts, kind, payload = ev[0], ev[1], ev[2]
        if kind == "m":
            markers.append((ts, str(payload)))
        elif kind == "o":
            text_chunks.append(str(payload))

    raw_text = "".join(text_chunks)
    clean_text = strip_ansi(raw_text)
    duration = events[-1][0] if events else 0.0

    return {
        "header": header,
        "events": events,
        "markers": markers,
        "duration": duration,
        "transcript": clean_text,
        "raw_text": raw_text,
    }


def validate_cast(cast_path: Path, forbidden_terms: Optional[List[str]] = None) -> bool:
    """Validate that .cast conforms to schema v2 and contains zero forbidden error strings."""
    data = parse_cast_file(cast_path)
    header = data["header"]
    if header.get("version") != 2:
        raise ValueError(f"Expected Asciicast version 2, got {header.get('version')}")

    forbidden = forbidden_terms or [
        "Traceback (most recent call last)",
        "No such file or directory",
        "FATAL ERROR",
        "UnhandledPromiseRejection",
    ]
    transcript = data["transcript"]
    for term in forbidden:
        if term in transcript:
            raise AssertionError(f"Validation failure in {cast_path.name}: detected '{term}'")

    print(f"✓ Validated {cast_path.name}: {len(data['events'])} events, {len(data['markers'])} markers, duration {format_time(data['duration'])}")
    return True


def render_html_walkthrough(
    cast_path: Path,
    output_html_path: Path,
    title: Optional[str] = None,
    subtitle: Optional[str] = None,
    template_path: Path = TEMPLATE_PATH,
) -> None:
    """Render standalone index.html with populated markers and transcript."""
    if not template_path.exists():
        raise FileNotFoundError(f"Template not found: {template_path}")

    data = parse_cast_file(cast_path)
    with open(template_path, "r", encoding="utf-8") as f:
        html = f.read()

    # Generate Chapter list HTML
    if data["markers"]:
        chapter_items = []
        for i, (ts, label) in enumerate(data["markers"]):
            active_cls = " active" if i == 0 else ""
            time_str = format_time(ts)
            item = f"""          <li class="chapter-item{active_cls}" onclick="seekChapter({i}, {ts})">
            <span class="chapter-time">{time_str}</span>
            <div class="chapter-info">
              <div class="chapter-title">{label}</div>
              <div class="chapter-desc">Jump directly to {label}</div>
            </div>
          </li>"""
            chapter_items.append(item)
        chapters_html = "\n".join(chapter_items)
        html = re.sub(r'<ul class="chapter-list"[^>]*>[\s\S]*?</ul>', f'<ul class="chapter-list" id="chapter-list">\n{chapters_html}\n        </ul>', html)
        html = html.replace('id="chapter-count-badge">5 Steps</span>', f'id="chapter-count-badge">{len(data["markers"])} Steps</span>')

    # Replace Transcript
    transcript_escaped = data["transcript"].replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    html = re.sub(r'<div class="transcript-box"[^>]*>[\s\S]*?</div>', f'<div class="transcript-box" id="transcript-box">\n{transcript_escaped}\n        </div>', html)

    if title:
        html = re.sub(r'<h1>.*?</h1>', f'<h1>{title}</h1>', html)
    if subtitle:
        html = re.sub(r'<p class="subtitle">.*?</p>', f'<p class="subtitle">{subtitle}</p>', html)

    with open(output_html_path, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"🎉 Successfully built interactive walkthrough HTML: {output_html_path}")


def serve_preview(directory: Path, port: int = 8080) -> None:
    """Serve walkthrough directory with local HTTP server for human review."""
    os.chdir(directory)
    handler = http.server.SimpleHTTPRequestHandler
    with socketserver.TCPServer(("", port), handler) as httpd:
        print(f"\n🌐 Local walkthrough preview server running at: http://localhost:{port}/index.html")
        print("Press Ctrl+C to stop server.\n")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nServer stopped.")


def main() -> None:
    parser = argparse.ArgumentParser(description="Asciinema Walkthrough Builder & Review Server")
    parser.add_argument("--cast", type=str, default="demo.cast", help="Input .cast file")
    parser.add_argument("--output", type=str, default="index.html", help="Output HTML file")
    parser.add_argument("--title", type=str, default=None, help="Walkthrough title override")
    parser.add_argument("--subtitle", type=str, default=None, help="Walkthrough subtitle override")
    parser.add_argument("--validate-only", action="store_true", help="Validate .cast without generating HTML")
    parser.add_argument("--serve", action="store_true", help="Start local HTTP review server")
    parser.add_argument("--port", type=int, default=8080, help="Port for review server")

    args = parser.parse_args()
    cast_path = Path(args.cast).resolve()

    if not cast_path.exists():
        # Fallback to repo demo.cast or demo-basics.cast
        alt_paths = [REPO_ROOT / args.cast, REPO_ROOT / "demo.cast", REPO_ROOT / "demo-basics.cast"]
        for p in alt_paths:
            if p.exists():
                cast_path = p
                break

    if cast_path.exists():
        validate_cast(cast_path)
        if not args.validate_only:
            out_path = Path(args.output).resolve()
            render_html_walkthrough(cast_path, out_path, title=args.title, subtitle=args.subtitle)
    else:
        print(f"Notice: Cast file {args.cast} does not exist yet. Run recording first.")

    if args.serve:
        serve_dir = Path(args.output).resolve().parent if not args.validate_only else REPO_ROOT
        serve_preview(serve_dir, port=args.port)


if __name__ == "__main__":
    main()
