#!/usr/bin/env python3
"""init-friction-log.py — Scaffold a standardized Friction Log markdown artifact.

Usage:
  python3 init-friction-log.py --target contrib/python/my-recipe --persona "Novice Developer" --output /path/to/log.md
"""

from __future__ import annotations

import argparse
import datetime
import os
from pathlib import Path
import subprocess
import sys


def get_git_info() -> tuple[str, str]:
    repo = "unknown/repo"
    branch = "main"
    try:
        remote = (
            subprocess.check_output(
                ["git", "remote", "get-url", "origin"],
                stderr=subprocess.DEVNULL,
                text=True,
            )
            .strip()
        )
        if "github.com" in remote:
            # Handle git@github.com:org/repo.git or https://github.com/org/repo.git
            parts = remote.split("github.com")[-1].lstrip(":").lstrip("/")
            if parts.endswith(".git"):
                parts = parts[:-4]
            repo = parts
        else:
            repo = remote
    except Exception:
        pass

    try:
        branch = (
            subprocess.check_output(
                ["git", "rev-parse", "--abbrev-ref", "HEAD"],
                stderr=subprocess.DEVNULL,
                text=True,
            )
            .strip()
        )
    except Exception:
        pass

    return repo, branch


def generate_log(target: str, persona: str, repo: str, branch: str) -> str:
    today = datetime.date.today().isoformat()
    target_name = Path(target).name or target

    return f"""# {target_name.replace('-', ' ').title()}: {persona} Friction Log & Review Report

**Date:** {today}  
**Target Recipe:** `{target}`  
**Reviewer Role:** Critical Reviewer & {persona} Persona  
**Repository:** `{repo}`  
**Branch:** `{branch}`  

---

## 1. Executive Summary

A comprehensive walkthrough of `{target}` was conducted from the viewpoint of a **{persona}** attempting to discover, clone, configure, locally execute, probe serving endpoints, run tests, containerize, and deploy the application from a true cold start.

*(Summary of findings and verification results will be populated here by the reviewer).*

---

## 2. Friction Matrix

| ID | Stage | Severity | Title | Root Cause | Status |
|:---|:---|:---:|:---|:---|:---:|
| **FL-01** | Discovery | **P0** | *(Describe initial blocker or friction point)* | *(Root cause explanation)* | **IDENTIFIED** |

---

## 3. Step-by-Step {persona} Journey Walkthrough & Analysis

### Journey Stage 1: Discovery, Clone & Directory Navigation
- **User Action:** Followed instructions in `README.md`.
- **Observed Result:** *(Log output or errors)*
- **Severity:** P0/P1/P2
- **Fix Applied:** *(Pending / Implemented fix)*

---

### Journey Stage 2: Environment Setup & Auth Configuration
- **User Action:** Installed dependencies and configured environment.
- **Observed Result:** *(Log output or errors)*
- **Severity:** P0/P1/P2
- **Fix Applied:** *(Pending / Implemented fix)*

---

### Journey Stage 3: Local Run & CLI Execution
- **User Action:** Executed primary CLI command.
- **Observed Result:** *(Log output or errors)*
- **Severity:** P0/P1/P2
- **Fix Applied:** *(Pending / Implemented fix)*

---

### Journey Stage 4: Local Serving & Endpoint Probing
- **User Action:** Started local server and probed health and API endpoints.
- **Observed Result:** *(Log output or errors)*
- **Severity:** P0/P1/P2
- **Fix Applied:** *(Pending / Implemented fix)*

---

### Journey Stage 5: Testing & Verification Suite
- **User Action:** Executed test suite.
- **Observed Result:** *(Log output or errors)*
- **Severity:** P0/P1/P2
- **Fix Applied:** *(Pending / Implemented fix)*

---

### Journey Stage 6: Container Packaging & Deployment
- **User Action:** Evaluated Dockerfile, container build, and deployment instructions.
- **Observed Result:** *(Log output or errors)*
- **Severity:** P0/P1/P2
- **Fix Applied:** *(Pending / Implemented fix)*

---

## 4. Verification Evidence & Test Results

*(Terminal outputs from linters, formatters, and test runners will be recorded here).*

---

## 5. File Changes Summary

*(List of modified files and descriptions will be recorded here).*
"""


def main() -> None:
    parser = argparse.ArgumentParser(description="Initialize a Friction Log artifact.")
    parser.add_argument("--target", required=True, help="Target directory or recipe path")
    parser.add_argument(
        "--persona",
        default="Novice Developer",
        help="Reviewer persona name (e.g. 'Novice Developer', 'Production SRE')",
    )
    parser.add_argument("--output", required=True, help="Output markdown file path")
    parser.add_argument("--repo", default=None, help="Repository name (e.g. google/adk-samples)")
    parser.add_argument("--branch", default=None, help="Git branch name")

    args = parser.parse_args()

    git_repo, git_branch = get_git_info()
    repo = args.repo or git_repo
    branch = args.branch or git_branch

    content = generate_log(
        target=args.target, persona=args.persona, repo=repo, branch=branch
    )

    out_path = Path(args.output).resolve()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(content, encoding="utf-8")
    print(f"✓ Initialized Friction Log at: {out_path}")


if __name__ == "__main__":
    main()
