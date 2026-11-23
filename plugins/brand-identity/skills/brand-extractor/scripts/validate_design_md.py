#!/usr/bin/env python3
"""
DESIGN.md Validator.
Validates conformance with Google Labs DESIGN.md Alpha specification.
Checks YAML frontmatter tokens, standard ## sections, and syntax structure.
"""

import argparse
import json
import os
import re
import sys

try:
    import yaml
except ImportError:
    print("Error: PyYAML is required. Install via pip install pyyaml", file=sys.stderr)
    sys.exit(1)

REQUIRED_SECTIONS = [
    "Overview",
    "Colors",
    "Typography",
    "Layout",
    "Elevation & Depth",
    "Shapes",
    "Components",
    "Do's and Don'ts",
]

SECTION_ALIASES = {
    "Overview": ["Brand & Style", "Brand Identity"],
    "Layout": ["Layout & Spacing"],
    "Elevation & Depth": ["Elevation"],
}

def validate_design_md(content):
    report = {
        "errors": [],
        "warnings": [],
        "summary": {"errors": 0, "warnings": 0}
    }

    # 1. Frontmatter check
    if not content.startswith("---"):
        report["errors"].append("Missing opening YAML frontmatter delimiter (---) at line 1")
        report["summary"]["errors"] = len(report["errors"])
        return report

    parts = re.split(r'^---[ 	]*$', content, maxsplit=2, flags=re.MULTILINE)
    if len(parts) < 3:
        report["errors"].append("Malformed YAML frontmatter (missing closing --- delimiter)")
        report["summary"]["errors"] = len(report["errors"])
        return report

    fm_text = parts[1]
    body_text = parts[2]

    # Parse YAML
    try:
        data = yaml.safe_load(fm_text)
    except Exception as e:
        report["errors"].append(f"YAML parse error in frontmatter: {e}")
        data = None

    if data and isinstance(data, dict):
        # Validate tokens
        colors = data.get("colors")
        if not colors or not isinstance(colors, dict):
            report["errors"].append("Missing or invalid 'colors' mapping in frontmatter tokens")
        else:
            if "primary" not in colors:
                report["errors"].append("Missing 'primary' color token under 'colors'")
        
        typography = data.get("typography")
        if not typography:
            report["warnings"].append("No 'typography' tokens defined in frontmatter")
        
        spacing = data.get("spacing")
        if not spacing:
            report["warnings"].append("No 'spacing' tokens defined in frontmatter")

        rounded = data.get("rounded")
        if not rounded:
            report["warnings"].append("No 'rounded' tokens defined in frontmatter")
    elif data is not None:
        report["errors"].append("Frontmatter must parse as a YAML mapping/dictionary")

    # 2. Section Headings (## Heading)
    for sec in REQUIRED_SECTIONS:
        aliases = SECTION_ALIASES.get(sec, [])
        candidates = [re.escape(sec)] + [re.escape(a) for a in aliases]
        pattern = rf"(?im)^##\s+(?:{'|'.join(candidates)})"
        if not re.search(pattern, body_text):
            report["warnings"].append(f"Missing standard section heading: '## {sec}'")

    # 3. Duplicate Section Headings
    h2_matches = re.findall(r'(?m)^##\s+(.+)$', body_text)
    seen = set()
    for h in h2_matches:
        h_clean = h.strip()
        if h_clean in seen:
            report["errors"].append(f"Duplicate section heading: '## {h_clean}'")
        seen.add(h_clean)

    report["summary"]["errors"] = len(report["errors"])
    report["summary"]["warnings"] = len(report["warnings"])
    return report

def main():
    parser = argparse.ArgumentParser(description="Validate a DESIGN.md file against the Design Alpha specification")
    parser.add_argument("file", help="Path to DESIGN.md file (or - for stdin)")
    parser.add_argument("--format", choices=["text", "json"], default="text", help="Output format")
    args = parser.parse_args()

    if args.file == "-":
        content = sys.stdin.read()
    else:
        if not os.path.exists(args.file):
            print(f"Error: file '{args.file}' not found.", file=sys.stderr)
            sys.exit(1)
        with open(args.file, "r", encoding="utf-8") as f:
            content = f.read()

    report = validate_design_md(content)

    if args.format == "json":
        print(json.dumps(report, indent=2))
    else:
        if report["summary"]["errors"] == 0 and report["summary"]["warnings"] == 0:
            print("[1;32m✓ DESIGN.md is fully valid according to the Design Alpha spec![0m")
        else:
            if report["summary"]["errors"] > 0:
                print(f"[1;31m✖ Found {report['summary']['errors']} Error(s):[0m")
                for e in report["errors"]:
                    print(f"  - {e}")
            if report["summary"]["warnings"] > 0:
                print(f"[1;33m⚠ Found {report['summary']['warnings']} Warning(s):[0m")
                for w in report["warnings"]:
                    print(f"  - {w}")

    if report["summary"]["errors"] > 0:
        sys.exit(1)

if __name__ == "__main__":
    main()
