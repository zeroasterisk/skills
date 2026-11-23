# Google Python Style Decisions Index

A quick lookup table mapping Google Python style decisions to rules, rationales, and preferred syntax.

| Decision Area | Rule | Rationale | Good Example | Bad Example |
| :--- | :--- | :--- | :--- | :--- |
| **Imports** | Import packages and modules only | Avoids namespace collisions and ambiguity over origin | `from sound.effects import echo` | `from sound.effects.echo import EchoFilter` |
| **Relative Imports** | Never use relative imports | Guarantees clear module paths and avoids duplicate imports | `from my_project.utils import text` | `from . import text` or `from ..utils import text` |
| **Import Exemptions** | `typing`, `collections.abc`, `typing_extensions` symbols | Static typing symbols are universally recognized | `from typing import Protocol, TypeVar` | N/A |
| **Exceptions** | Never use `assert` for application logic | Asserts can be disabled at runtime via `-O` flag | `if port < 1024: raise ValueError(...)` | `assert port >= 1024, "Invalid port"` |
| **Catch-All Exceptions** | Avoid bare `except:` or `except Exception:` | Hides typos, interrupts (`KeyboardInterrupt`), and bugs | `except KeyError as err:` | `except:` or `except Exception:` |
| **Mutable Defaults** | Never use mutable objects as default args | Evaluated once at import time; shares state across calls | `def foo(items: list[str] \| None = None):` | `def foo(items: list[str] = []):` |
| **Unused Arguments** | Suppress with `del arg  # Unused.` | Keeps explicit signature and prevents silent call breakages | `del context, request  # Unused.` | `def handler(_context, _request):` |
| **Docstrings** | Google Docstring format with summary $\le 80$ chars | Standardized documentation generation and readability | `Args:`, `Returns:`, `Yields:`, `Raises:` | Free-form or unformatted multi-line blocks |
| **Docstring Quotes** | Always triple double quotes `"""` | PEP 257 standard | `"""Summary line."""` | `'''Summary line.'''` |
| **Static Methods** | Avoid `@staticmethod` | Methods that do not use class or instance state belong at module level | Module-level function `def helper():` | `@staticmethod def helper():` |
| **Class Methods** | Use only for factory / alternate constructors | Preserves clear object lifecycle expectations | `@classmethod def from_json(cls, ...):` | Using `@classmethod` as a generic namespace |
| **True / False** | Implicit false for empty collections, explicit for `None` | Readable and idiomatic; prevents falsy `0` vs `None` bugs | `if not users:` and `if val is None:` | `if len(users) == 0:` or `if val == None:` |
| **Comprehensions** | Keep simple; no multiple `for` clauses | Minimizes cognitive load | `[x * 2 for x in seq if x > 0]` | `[y for row in matrix for y in row if y > 0]` |
| **Lambdas** | One-liners under 60-80 chars; prefer `operator` module | Readability and clear stack traces | `operator.itemgetter(1)` or small lambda | Multi-line complex lambda expressions |
| **Line Length** | 80 characters (strict) or 88 (Black standard) | Prevents horizontal scrolling and eases side-by-side review | Wrap with implicit parens `(a + b)` | Backslash line continuation `a + \ b` |
| **Type Annotations** | Modern syntax (`int \| None`, `list[str]`) on all public APIs | Compile-time bug detection and clear interface contracts | `def process(names: Sequence[str]) -> int:` | `def process(names):` |
| **Global State** | Avoid mutable module-level state | Prevents hidden coupling and multi-threading race hazards | Internal constants: `_MAX_RETRIES = 5` | Mutable module-level list or dict mutated in funcs |
| **Power Features** | Avoid metaclasses, bytecode manipulation, `__del__` | Complex meta-programming harms readability and debuggability | Clean composition or `@dataclass` | Custom metaclass modifying `__dict__` dynamically |
| **Testing** | Use `pytest` with descriptive assertions and fixtures | Diagnosable test failures with minimal boilerplate | `assert got == want` with descriptive names | Complex deep inheritance in `unittest.TestCase` |
