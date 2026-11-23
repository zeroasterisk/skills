# Self-Audit Checklist for Python Code

Mechanical greps and checks to catch the most common Python style violations BEFORE submitting code for review. Run from the repository root or package directory. False positives may occur—use these as rapid diagnostics for inspection.

For each match: review against the corresponding section in `SKILL.md` and the [Google Python Style Guide](https://google.github.io/styleguide/pyguide.html).

---

## 1. Imports

```bash
# 1. Relative imports (Google style strictly forbids relative imports)
#    Use full package path: 'from sound.effects import echo', not 'from . import echo'
grep -nE '^\s*from\s+\.[a-zA-Z0-9_.]*\s+import' **/*.py

# 2. Direct symbol imports from non-exempt packages
#    Import modules, not functions/classes (except typing, collections.abc, typing_extensions)
#    Inspect matches for classes/functions directly imported:
grep -nE '^\s*from\s+[a-zA-Z0-9_.]+\s+import\s+[A-Z][a-zA-Z0-9]+' **/*.py | grep -vE 'typing|collections\.abc|typing_extensions|dataclasses|enum|pydantic'

# 3. Wildcard imports (never permitted)
grep -nE '^\s*from\s+[a-zA-Z0-9_.]+\s+import\s+\*' **/*.py
```

---

## 2. Exceptions & Control Flow

```bash
# 4. Assert used in production code (assert must only be used in tests, not for input validation)
grep -nE '^\s*assert\b' **/*.py | grep -vE 'tests/|_test\.py|test_'

# 5. Bare except or broad Exception catching
grep -nE '^\s*except\s*:' **/*.py
grep -nE '^\s*except\s+Exception\s*:' **/*.py

# 6. Mutable default arguments (def f(x=[]), def f(x={}), def f(x=set()))
grep -nE 'def\s+[a-zA-Z0-9_]+\([^)]*=\s*(\[\]|\{\}|set\(\))' **/*.py
```

---

## 3. Unused Arguments & Variables

```bash
# 7. Unused argument underscore prefix (Google style prefers 'del arg  # Unused.')
grep -nE 'def\s+[a-zA-Z0-9_]+\([^)]*\b_[a-zA-Z0-9_]+' **/*.py
```

---

## 4. Comparisons & Booleans

```bash
# 8. Comparison to None or booleans with == instead of 'is' or implicit truthiness
grep -nE '==\s*None\b' **/*.py
grep -nE '!=\s*None\b' **/*.py
grep -nE '==\s*True\b' **/*.py
grep -nE '==\s*False\b' **/*.py

# 9. len() used in boolean condition (use implicit truthiness: 'if not seq:', not 'if len(seq) == 0:')
grep -nE 'if\s+len\([a-zA-Z0-9_.]+\)\s*==\s*0' **/*.py
grep -nE 'if\s+len\([a-zA-Z0-9_.]+\)\s*>\s*0' **/*.py
```

---

## 5. Classes & Methods

```bash
# 10. @staticmethod decorator (discouraged; prefer module-level functions)
grep -nE '^\s*@staticmethod\b' **/*.py

# 11. Redundant object inheritance (class Foo(object): is Python 2 legacy; use class Foo:)
grep -nE 'class\s+[a-zA-Z0-9_]+\(object\):' **/*.py
```

---

## 6. Typing Modernity

```bash
# 12. Legacy typing module aliases in Python 3.10+ (use list[], dict[], tuple[], X | None)
grep -nE 'from\s+typing\s+import\s+.*\b(List|Dict|Tuple|Set|Optional|Union)\b' **/*.py
```

---

## Pre-Review Workflow

After inspecting with greps, run automated formatters, linters, and type checkers:

```bash
ruff check . --fix    # linter pass with auto-fixes
ruff format .         # format code with 80-char line limit
mypy .                # strict type checking
pytest                # test suite execution
```
