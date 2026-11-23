---
name: python-readability
description: >-
  Write, review, and refactor Python code to meet Google and modern Python readability standards. Covers style, naming, imports, error handling, docstrings, testing, typing, linter automation (Ruff, Mypy), mentor feedback, and pre-review checklists. Use for "python readability", "python style", "google python style", "python docstrings", "python linting", "ruff google", "python code review", or "idiomatic python".
license: Apache-2.0
metadata:
  version: "1.0.0"
---

# Python Readability

Concise guide to writing idiomatic Python that adheres to Google and modern Python readability guidelines. Distilled from the [Google Python Style Guide](https://google.github.io/styleguide/pyguide.html), modern PEPs (PEP 8, PEP 257, PEP 585, PEP 604), and battle-tested code review feedback.

---

## Formatting and Layout

- **Line length**: 80 characters maximum per Google style (or 88 characters if your team adopts the standard Black/Ruff default).
- **Indentation**: 4 spaces per indentation level. Never use tabs.
- **Parentheses**: Use implicit line joining inside parentheses, brackets, and braces rather than backslash line continuation (`\`).
- **Blank lines**:
  - Two blank lines between top-level functions and class definitions.
  - One blank line between method definitions within a class.
- **Whitespace**:
  - No whitespace inside parentheses, brackets, or braces (`spam(ham[1], {'eggs': 2})`).
  - No spaces around `=` when passing keyword arguments or default parameters, **except** when a type annotation is present (`real: float = 0.0`).
  - Single space on either side of binary operators (`=`, `==`, `<`, `+`, `-`).
  - No trailing whitespace on any line.

---

## Linting and Automated Tooling

Modern Python projects enforce Google readability standards using high-speed static analysis and formatting:

- **Ruff**: Enforces Google docstrings (`convention = "google"`), banned relative imports (`TID252`), pylint conventions (`PLC`, `PLE`, `PLR`, `PLW`), and flake8-bugbear design checks (`B`).
- **Mypy**: Enforces strict type annotations (`strict = true`) across public modules.
- **Pre-commit**: Automates formatting and lint checks on git commit.

Run linter checks and auto-formatters during development:

```bash
ruff check . --fix    # auto-fixes imports, docstring errors, and conventions
ruff format .         # formats files with 80-character limit
mypy .                # verifies strict static typing
```

To audit or bootstrap linter configuration automatically in any repository, use the included CLI script:

```bash
./scripts/setup-linters.py --check
./scripts/setup-linters.py --apply --line-length 80
```

Ready-to-use template configurations are provided in:
- `assets/pyproject.toml.template` — Complete Ruff and Mypy configuration.
- `assets/pylintrc.template` — Google baseline `.pylintrc`.
- `assets/pre-commit-config.yaml.template` — Turnkey pre-commit hooks.

To suppress specific warnings where strictly necessary, use symbolic comments:

```python
def do_PUT(self):  # WSGI interface name, so noqa: N802 (or pylint: disable=invalid-name)
    ...
```

---

## Imports

Google style enforces strict import hygiene to guarantee that every identifier's origin is unambiguous at call sites:

1. **Import packages and modules only**:
   - Do NOT import individual classes, functions, or constants from internal or external packages.
   - Access symbols via the module prefix.
2. **Never use relative imports**:
   - Always use the full package path location (e.g. `from sound.effects import echo`, never `from . import echo` or `from ..effects import echo`).
3. **Group imports into standard blocks** separated by blank lines:
   1. Standard library imports
   2. Third-party library imports
   3. Local application / package imports
4. **Standard exemptions**:
   - Symbols from `typing`, `collections.abc`, and `typing_extensions` used for type annotations are exempt (`from typing import Protocol`, `from collections.abc import Sequence`).
   - Standard community abbreviations are permitted (`import numpy as np`, `import pandas as pd`).

```python
# ✗ Bad: imports class directly, relative import
from ..models.user import User

def get_user() -> User:
    ...

# ✓ Good: absolute module import, explicit origin at call site
from my_project.models import user

def get_user() -> user.User:
    ...
```

---

## Naming Conventions

Target | Convention | Example
:--- | :--- | :---
**Packages & Modules** | `snake_case` (short, lowercase, no hyphens) | `url_parser`, `db`
**Classes & Exceptions** | `PascalCase` (exceptions end in `Error`) | `OrderProcessor`, `ConfigError`
**Functions & Methods** | `snake_case` (verb-like for actions) | `calculate_rate`, `fetch_user`
**Variables & Arguments** | `snake_case` | `user_id`, `retry_count`
**Constants (Module-level)** | `ALL_CAPS` with underscores | `_MAX_TIMEOUT_SECONDS`, `DEFAULT_PORT`
**Internal / Protected** | Leading single underscore `_` | `_internal_cache`, `_parse_token`
**Type Variables** | `PascalCase` (usually single letter or short) | `T`, `AnyStr`, `KeyType`

- **Avoid Generic Names**: Avoid cryptic abbreviations (`res`, `obj`, `tmp`, `val`, `data`). Use clear, domain-specific names (`response`, `user_profile`, `timeout_seconds`).
- **Internal Module Variables**: Internal constants or mutable singletons must be prefixed with a single underscore `_`.

---

## Error Handling and Exceptions

1. **Never use `assert` for application logic or preconditions**:
   - Python removes `assert` statements entirely when run with `-O` optimization flags.
   - Raise `ValueError`, `TypeError`, or domain-specific exceptions for parameter validation.
   - Use `assert` strictly in test suites (e.g. `pytest`).
2. **Never catch-all with bare `except:` or `except Exception:`**:
   - Bare `except:` catches `KeyboardInterrupt` and `SystemExit`, preventing clean shutdown.
   - Catch specific exceptions (`except (KeyError, ValueError) as err:`).
   - If a top-level isolation boundary must catch `Exception`, log the full traceback and re-raise or cleanly handle.
3. **Chain wrapped exceptions with `from err`**:
   - When raising a high-level exception in response to a caught low-level error, use `raise CustomError(...) from err` to preserve the root cause.
4. **Keep `try` bodies minimal**:
   - Only place lines capable of raising the targeted exception inside the `try` block to avoid masking unexpected bugs.
5. **Use context managers and `finally`**:
   - Always use `with` statements for files, sockets, locks, and database connections.

```python
# ✗ Bad: assert in prod, bare except
def connect_to_port(port: int) -> Socket:
    assert port >= 1024, "Port must be >= 1024"
    try:
        return open_socket(port)
    except:
        return None

# ✓ Good: explicit exception, targeted catch, chained error
def connect_to_port(port: int) -> Socket:
    if port < 1024:
        raise ValueError(f"Port must be at least 1024, got {port}")
    try:
        return open_socket(port)
    except OSError as err:
        raise ConnectionFailedError(f"Could not connect to port {port}: {err}") from err
```

---

## Functions, Methods, and Control Flow

1. **Never use mutable default arguments**:
   - Default values are evaluated once at module load time. Mutating `def f(items=[])` alters state across all callers.
   - Use `None` as the default value and initialize inside the function:
     ```python
     def process_items(items: Sequence[str] | None = None) -> list[str]:
         actual_items = list(items) if items is not None else []
     ```
2. **Unused arguments**:
   - Do NOT rename unused arguments to `_` or `_unused_arg` if they are part of a public API or callback signature (this breaks callers passing arguments by keyword).
   - Delete them explicitly at the start of the function body:
     ```python
     def on_event(event_name: str, payload: dict[str, Any], timestamp: float) -> None:
         del timestamp  # Unused by this event handler.
         process(event_name, payload)
     ```
3. **Avoid `@staticmethod`**:
   - Move methods that do not access instance (`self`) or class (`cls`) state to module-level private functions (`def _helper():`).
4. **Limit `@classmethod`**:
   - Use `@classmethod` primarily for alternate or factory constructors (`from_dict`, `from_json`).
5. **Truth value testing**:
   - Use implicit false for empty collections (`if not users:` rather than `if len(users) == 0:`).
   - Use explicit `is None` or `is not None` when checking for `None`.
   - Never compare booleans to `True` or `False` using `==` (`if is_valid:` not `if is_valid == True:`).
6. **Comprehensions**:
   - Keep simple. Avoid multiple `for` loops or deeply nested conditionals within list, dict, or set comprehensions.

---

## Documentation and Google Docstrings

- Every public module, class, method, and function must have a docstring using triple double quotes `"""`.
- Format docstrings using the **Google Docstring format**:
  - One-line summary ($\le 80$ characters) ending in a period.
  - Blank line.
  - Extended description if necessary.
  - Sections: `Args:`, `Returns:`, `Yields:`, `Raises:` indented with 2 or 4 spaces.
  - When code has type hints on parameters, omit types from the docstring.
- Format TODO comments with the owner's username: `# TODO(username): Description.`

```python
def fetch_user_balance(user_id: str, include_pending: bool = False) -> Decimal:
    """Calculates the total account balance for a user.

    Queries both settled ledger entries and, optionally, pending authorizations
    to produce the effective available balance.

    Args:
        user_id: Unique string identifier for the user account.
        include_pending: Whether to deduct pending authorized transactions.

    Returns:
        The total computed balance as a high-precision Decimal.

    Raises:
        UserNotFoundError: If user_id does not exist in the database.
        LedgerUnreachableError: If the ledger database replica fails to respond.
    """
```

See `references/google_docstrings.md` for a comprehensive guide to class, module, and generator docstrings.

---

## Static Type Annotations

- Annotate all public functions and methods with Python 3.10+ modern typing syntax.
- Use `int | None` instead of `Optional[int]`.
- Use `list[str]`, `dict[str, Any]`, `tuple[int, ...]` instead of legacy `typing.List`, `typing.Dict`.
- Accept abstract container types (`Sequence[T]`, `Mapping[K, V]`, `Iterable[T]`) for inputs; return concrete types (`list[T]`, `dict[K, V]`).
- Use `typing.Protocol` for structural duck typing instead of deep inheritance trees.
- Run `mypy --strict` to verify type completeness.

See `references/typing_patterns.md` for in-depth patterns.

---

## Testing with Pytest

- Use standard `pytest` test runners.
- Write table-driven tests using `@pytest.mark.parametrize` with explicit `ids=`.
- Assert exceptions with `pytest.raises(ExceptionClass, match=r"regex")` to verify both exception type and message.
- Use `tmp_path` fixture for temporary file operations.
- Avoid over-mocking; prefer lightweight in-memory fakes satisfying `Protocol` interfaces over fragile monkeypatching.

See `references/pytest_patterns.md` for testing guidelines.

---

## Deep-Dive References

For detailed guidelines, audit scripts, and examples, refer to these references:

- `references/decisions_index.md` — One-line-per-rule lookup table matching Google style decisions to rules and rationales.
- `references/common_mentor_feedback.md` — Explanations for frequent reviewer comments (module imports, `del` unused args, `ValueError` vs `assert`, mutable defaults).
- `references/self_audit_checklist.md` — Mechanical grep patterns for rapid pre-review self-audits.
- `references/google_docstrings.md` — Complete reference for Google docstring formatting.
- `references/typing_patterns.md` — Modern Python typing conventions (PEP 585/604, Protocols, Generics).
- `references/pytest_patterns.md` — Pytest patterns, parametrization, and mock avoidance.
- `examples/before_after_examples.md` — Side-by-side refactoring diffs.
- `scripts/setup-linters.py` — Automated linter auditor and bootstrap CLI tool.
- `assets/pyproject.toml.template` — Ruff and Mypy template configuration.
- `assets/pylintrc.template` — Google `.pylintrc` template.
- `assets/pre-commit-config.yaml.template` — Pre-commit hook configuration template.
- `TEST.md` — Agent E2E validation test plan with prompts and verification assertions.

---

## Review Guidelines

When reviewing Python code, inspect against this top-10 checklist:

1. **Imports**: Are imports limited to modules and packages? Are relative imports avoided?
2. **Preconditions**: Are arguments validated with `ValueError` rather than `assert`?
3. **Default Arguments**: Are all function default values immutable?
4. **Unused Arguments**: Are callback arguments suppressed using `del arg  # Unused.`?
5. **Exceptions**: Are catch blocks specific? Are wrapped exceptions chained with `from err`?
6. **Docstrings**: Do public functions carry Google-formatted docstrings with summary $\le 80$ characters?
7. **Type Annotations**: Are signatures strictly typed using modern `X | None` and `list[T]` syntax?
8. **Static Methods**: Have `@staticmethod` usages been refactored to module-level functions?
9. **Booleans**: Is emptiness checked via `if not seq:` rather than `if len(seq) == 0:`?
10. **Formatting & Tooling**: Does the code pass `ruff check`, `ruff format --check`, and `mypy`?
