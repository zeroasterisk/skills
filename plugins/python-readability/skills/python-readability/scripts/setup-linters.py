#!/usr/bin/env python3
"""Audit and configure linters for Google Python Readability standards.

Supports checking and bootstrapping:
  - Ruff with Google docstrings (D), flake8-bugbear (B), pylint rules (PL),
    banned relative imports (TID252), and 80-char formatting.
  - Mypy with strict type-checking configuration.
  - Pre-commit configuration hooks.

Usage:
  ./scripts/setup-linters.py --check [path]
  ./scripts/setup-linters.py --apply [path] [--line-length 80|88]
"""

from __future__ import annotations

import argparse
import os
from pathlib import Path
import sys

DEFAULT_RUFF_BLOCK = """
[tool.ruff]
line-length = {line_length}
target-version = "py311"

[tool.ruff.lint]
select = [
    "E",     # pycodestyle errors
    "W",     # pycodestyle warnings
    "F",     # pyflakes
    "I",     # isort (import sorting)
    "N",     # pep8-naming
    "D",     # pydocstyle (Google docstring convention)
    "UP",    # pyupgrade (modern Python syntax)
    "B",     # flake8-bugbear (design & common bug checks)
    "C4",    # flake8-comprehensions
    "SIM",   # flake8-simplify
    "TID",   # flake8-tidy-imports (ban relative imports)
    "PLC",   # pylint conventions
    "PLE",   # pylint errors
    "PLR",   # pylint refactorings
    "PLW",   # pylint warnings
    "RUF",   # ruff-specific rules
]
ignore = [
    "D100",  # Missing docstring in public module
    "D104",  # Missing docstring in public package
    "PLR0913", # Too many arguments in function definition
]

[tool.ruff.lint.pydocstyle]
convention = "google"

[tool.ruff.lint.flake8-tidy-imports]
ban-relative-imports = "all"

[tool.ruff.lint.isort]
combine-as-imports = true
lines-after-imports = 2

[tool.ruff.format]
quote-style = "double"
indent-style = "space"
line-ending = "auto"
docstring-code-format = true
"""

DEFAULT_MYPY_BLOCK = """
[tool.mypy]
python_version = "3.11"
strict = true
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = true
disallow_incomplete_defs = true
check_untyped_defs = true
disallow_untyped_decorators = true
no_implicit_optional = true
warn_redundant_casts = true
warn_unused_ignores = true
warn_no_return = true
show_error_codes = true
"""

PRE_COMMIT_CONFIG = """# Pre-commit configuration for Google Python Readability
repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.6.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-toml
      - id: check-added-large-files

  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.5.5
    hooks:
      - id: ruff
        args: [--fix, --exit-non-zero-on-fix]
      - id: ruff-format

  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.11.1
    hooks:
      - id: mypy
        args: [--strict]
"""


def check_readability_setup(target_dir: Path) -> int:
    """Audit the project root for Google readability linter configuration."""
    print(f"Auditing Python readability setup in: {target_dir.resolve()}\n")

    pyproject_file = target_dir / "pyproject.toml"
    pre_commit_file = target_dir / ".pre-commit-config.yaml"

    issues = 0

    if not pyproject_file.is_file():
        print("[-] pyproject.toml not found.")
        issues += 1
    else:
        content = pyproject_file.read_text(encoding="utf-8")
        print("[+] pyproject.toml found.")

        # Check Ruff
        if "[tool.ruff]" not in content:
            print("  [-] [tool.ruff] configuration block is missing.")
            issues += 1
        else:
            print("  [+] [tool.ruff] configuration detected.")
            if 'convention = "google"' in content or "convention = 'google'" in content:
                print("    [+] Ruff pydocstyle configured with Google convention.")
            else:
                print("    [-] Ruff pydocstyle Google convention missing (rule 'D' with convention = 'google').")
                issues += 1

            if 'ban-relative-imports = "all"' in content or "ban-relative-imports = 'all'" in content:
                print("    [+] Banned relative imports (TID252) configured.")
            else:
                print("    [-] Banned relative imports missing (flake8-tidy-imports ban-relative-imports = 'all').")
                issues += 1

        # Check Mypy
        if "[tool.mypy]" not in content:
            print("  [-] [tool.mypy] strict configuration block is missing.")
            issues += 1
        else:
            print("  [+] [tool.mypy] configuration detected.")
            if "strict = true" in content:
                print("    [+] Mypy strict mode enabled.")
            else:
                print("    [-] Mypy strict mode not explicitly enabled.")
                issues += 1

    # Check pre-commit
    if not pre_commit_file.is_file():
        print("[-] .pre-commit-config.yaml not found.")
        issues += 1
    else:
        print("[+] .pre-commit-config.yaml found.")

    print("\n" + "=" * 50)
    if issues == 0:
        print("✓ Project conforms to recommended Google Python Readability tooling.")
        return 0
    else:
        print(f"✗ Found {issues} tooling gap(s). Run with --apply to configure automatically.")
        return 1


def apply_readability_setup(target_dir: Path, line_length: int, write_precommit: bool) -> int:
    """Inject or update linter configurations in target directory."""
    target_dir.mkdir(parents=True, exist_ok=True)
    pyproject_file = target_dir / "pyproject.toml"

    print(f"Applying Google readability linter configuration to: {target_dir.resolve()}")

    formatted_ruff = DEFAULT_RUFF_BLOCK.format(line_length=line_length).strip()
    formatted_mypy = DEFAULT_MYPY_BLOCK.strip()

    if pyproject_file.is_file():
        existing = pyproject_file.read_text(encoding="utf-8")
        append_blocks = []

        if "[tool.ruff]" not in existing:
            append_blocks.append(formatted_ruff)
            print("  + Added [tool.ruff] block to pyproject.toml")
        else:
            print("  * [tool.ruff] already exists in pyproject.toml (preserved)")

        if "[tool.mypy]" not in existing:
            append_blocks.append(formatted_mypy)
            print("  + Added [tool.mypy] block to pyproject.toml")
        else:
            print("  * [tool.mypy] already exists in pyproject.toml (preserved)")

        if append_blocks:
            new_content = existing.rstrip() + "\n\n" + "\n\n".join(append_blocks) + "\n"
            pyproject_file.write_text(new_content, encoding="utf-8")
    else:
        initial_content = f"""[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "{target_dir.name}"
version = "0.1.0"
description = "Project following Google Python Readability standards"
requires-python = ">=3.11"
dependencies = []

[dependency-groups]
dev = [
    "mypy>=1.10.0",
    "pytest>=8.0.0",
    "ruff>=0.5.0",
]

{formatted_ruff}

{formatted_mypy}
"""
        pyproject_file.write_text(initial_content, encoding="utf-8")
        print("  + Created pyproject.toml with Ruff & Mypy configurations")

    if write_precommit:
        pre_commit_file = target_dir / ".pre-commit-config.yaml"
        if not pre_commit_file.is_file():
            pre_commit_file.write_text(PRE_COMMIT_CONFIG.strip() + "\n", encoding="utf-8")
            print("  + Created .pre-commit-config.yaml")
        else:
            print("  * .pre-commit-config.yaml already exists (preserved)")

    print("\n✓ Setup complete. You can now run:")
    print("  ruff check . --fix")
    print("  ruff format .")
    print("  mypy .")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Audit and setup linters for Google Python Readability standards."
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--check", action="store_true", help="Audit repository for linter configurations")
    group.add_argument("--apply", action="store_true", help="Apply Google readability linter configurations")

    parser.add_argument("path", nargs="?", default=".", help="Target project root directory (default: current directory)")
    parser.add_argument("--line-length", type=int, choices=[80, 88], default=80, help="Max line length (default: 80, per Google style)")
    parser.add_argument("--no-pre-commit", action="store_true", help="Skip creating .pre-commit-config.yaml when applying")

    args = parser.parse_args()
    target = Path(args.path)

    if args.check:
        return check_readability_setup(target)
    elif args.apply:
        return apply_readability_setup(target, args.line_length, not args.no_pre_commit)

    return 0


if __name__ == "__main__":
    sys.exit(main())
