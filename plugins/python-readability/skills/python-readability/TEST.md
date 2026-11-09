# Python Readability Skill - Agent E2E Test Plan

## Prerequisites

Read `SKILL.md` first to understand the style rules, patterns, and gotchas covered by this skill.

Tests validate that an agent applies Google and idiomatic Python readability standards correctly when writing, reviewing, or refactoring Python code.

---

## Test 1: Module Imports vs Symbol Imports

**Prompt:** "In my Python file, I have `from my_project.services.billing import BillingClient, InvoiceGenerator`. Is this naming and import style recommended?"

**Verify:**
- Advises importing packages/modules only, not classes or functions directly.
- Recommends `from my_project.services import billing` and calling `billing.BillingClient()`.
- Explains that module imports avoid namespace collisions and make the origin of identifiers explicit at call sites.
- Mentions that `typing` and `collections.abc` are exceptions to this rule.

---

## Test 2: Banned Relative Imports

**Prompt:** "I have a file `my_project/api/routes.py` with `from .models import User` and `from ..utils import format_date`. Is this good style?"

**Verify:**
- Flags relative imports (`from .` and `from ..`) as violations of Google style.
- Recommends absolute imports: `from my_project.api import models` and `from my_project import utils`.
- Explains that absolute imports prevent duplicate imports and make search/refactoring predictable.

---

## Test 3: Precondition Validation (Assert vs Exception)

**Prompt:** "I'm validating inputs in my payment service: `assert amount > 0, 'Amount must be positive'`. Is this proper Python practice?"

**Verify:**
- Identifies that `assert` should NEVER be used for production input validation or application logic.
- Explains that running Python with `-O` (optimized) strips all `assert` statements from bytecode.
- Recommends checking with `if amount <= 0:` and raising `ValueError`.
- Clarifies that `assert` is appropriate in `pytest` test suites.

---

## Test 4: Mutable Default Arguments

**Prompt:** "Review this function signature: `def add_item(item: str, target_list: list[str] = []) -> list[str]:`."

**Verify:**
- Identifies mutable default argument (`target_list: list[str] = []`).
- Explains that default values are evaluated once at import time and mutated across subsequent calls.
- Recommends sentinel default `target_list: Sequence[str] | None = None` (or `list[str] | None = None`).
- Shows runtime initialization: `actual_list = list(target_list) if target_list is not None else []`.

---

## Test 5: Unused Argument Handling

**Prompt:** "In a Flask or FastAPI callback, I don't need the `request` argument. Should I name it `_request` or `_`?"

**Verify:**
- Explains that Google style prefers `del request  # Unused.` at the start of the function.
- Explains that renaming parameters to `_request` can break callers passing arguments by keyword.
- Demonstrates the canonical pattern with the `# Unused.` comment.

---

## Test 6: Google Docstring Formatting

**Prompt:** "Write a docstring for a function that fetches user records by ID and may raise `UserNotFoundError`."

**Verify:**
- Formats docstrings with triple double-quotes `"""`.
- Includes a summary line $\le 80$ characters ending in a period.
- Uses `Args:`, `Returns:`, and `Raises:` sections with consistent 2 or 4 space indentation.
- When signatures are type-annotated, omits redundant type annotations in the docstring.

---

## Test 7: Modern Type Annotations

**Prompt:** "How should I type-annotate an optional list of string tags for Python 3.11?"

**Verify:**
- Recommends modern union syntax `list[str] | None` or `Sequence[str] | None`.
- Discourages legacy `typing.Optional[typing.List[str]]`.
- Mentions importing abstract sequence types from `collections.abc.Sequence` for input parameters.

---

## Test 8: Static Method Removal

**Prompt:** "I have a helper method inside a class: `@staticmethod def format_name(first: str, last: str) -> str: return f'{first} {last}'`. Is this idiomatic?"

**Verify:**
- Identifies `@staticmethod` as discouraged in Google Python style.
- Recommends moving the function to the module level (e.g. `def _format_name(first: str, last: str) -> str:`).
- Explains that Python modules are natural namespaces and standalone functions are easier to test and reuse.

---

## Test 9: Exception Chaining

**Prompt:** "I caught `requests.RequestException` and want to raise my own `GatewayError`. How should I write it?"

**Verify:**
- Recommends explicit exception chaining: `raise GatewayError(...) from err`.
- Explains that `from err` preserves the original traceback and root cause for debugging.

---

## Test 10: Falsy Comparisons

**Prompt:** "I wrote `if len(users) == 0:` and `if flag == True:`. What does Python readability recommend?"

**Verify:**
- Recommends `if not users:` for empty container checks.
- Recommends `if flag:` instead of comparison to `True`.
- Notes that `is None` should remain explicit when checking for `None`.

---

## Test 11: Linter Setup and Tooling

**Prompt:** "How do I configure Ruff and Mypy to enforce Google Python style automatically in my project?"

**Verify:**
- Explains configuring `pyproject.toml` with `[tool.ruff.lint.pydocstyle] convention = "google"`.
- Explains configuring `[tool.ruff.lint.flake8-tidy-imports] ban-relative-imports = "all"`.
- Recommends `select` rules including `D` (docstrings), `B` (bugbear), `TID` (tidy imports), `I` (isort), and `PL` (pylint).
- Explains configuring Mypy with `strict = true`.
- Points to `./scripts/setup-linters.py` or `assets/pyproject.toml.template` for turnkey setup.
