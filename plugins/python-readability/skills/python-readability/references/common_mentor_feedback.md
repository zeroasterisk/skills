# Common Mentor & Reviewer Feedback for Python Code

This document outlines recurring comments given during Google Python Readability reviews, explains the rationale behind each guideline, and demonstrates how to refactor the code.

---

## 1. Imports: "Import modules, not individual classes or functions"

### The Review Comment
> *"Please import the module rather than the class/function directly. E.g., `from my_project.services import billing` and use `billing.BillingClient()`, rather than `from my_project.services.billing import BillingClient`."*

### Why It Matters
When reading code at call sites:
- `billing.BillingClient()` immediately signals where `BillingClient` comes from.
- `BillingClient()` alone leaves the reader wondering whether it was defined in the current file, imported from a local package, or pulled from a third-party library.
- It also avoids local namespace collisions when two modules define types with identical or similar names (e.g. `Config`, `Client`, `Response`, `Handler`).

### The Exception
Symbols from `typing`, `collections.abc`, and `typing_extensions` used purely for type annotations are exempt:
```python
# ✓ Good: typing imports are exempt
from collections.abc import Mapping, Sequence
from typing import Any, Protocol, TypeVar
```

---

## 2. Unused Arguments: "Use `del arg  # Unused.` instead of `_` prefixes"

### The Review Comment
> *"Please use `del unused_arg  # Unused.` at the start of the function rather than naming the parameter `_unused_arg` or assigning `_ = unused_arg`."*

### Why It Matters
In Python, function parameters can be passed by keyword (`client.handle(event=e, context=c)`). When a signature is dictated by an interface, subclass override, or framework callback, renaming the argument to `_event` or `_` breaks callers attempting to pass the argument as a keyword.

Furthermore, `del arg  # Unused.` enforces that the argument is actually never used later in the function body (attempting to use it raises a `NameError`).

```python
# ✗ Bad
def on_event(event_name: str, payload: dict[str, Any], _timestamp: float) -> None:
    process_event(event_name, payload)

# ✓ Good
def on_event(event_name: str, payload: dict[str, Any], timestamp: float) -> None:
    del timestamp  # Unused.
    process_event(event_name, payload)
```

---

## 3. Preconditions: "Do not use `assert` for application logic or input validation"

### The Review Comment
> *"Do not use `assert` to validate function arguments or enforce production invariants. Raise `ValueError` or `TypeError` instead."*

### Why It Matters
Python evaluates `assert condition, message` statements only in non-optimized mode. When the Python interpreter runs with the `-O` or `-OO` optimization flags, all `assert` statements are completely removed from the bytecode.

If an `assert` guards critical application logic, authentication, or input sanitization, running with `-O` disables the check entirely.

```python
# ✗ Bad
def set_timeout(seconds: float) -> None:
    assert seconds > 0, "Timeout must be positive"
    self._timeout = seconds

# ✓ Good
def set_timeout(seconds: float) -> None:
    if seconds <= 0:
        raise ValueError(f"Timeout must be positive, got {seconds}")
    self._timeout = seconds
```

*Note: In `pytest` test functions, `assert` is expected and recommended.*

---

## 4. Default Arguments: "Never use mutable default arguments"

### The Review Comment
> *"Default parameter `tags=[]` is mutable. Use `None` as the default and initialize inside the function."*

### Why It Matters
Default parameter values are evaluated once when the module is imported, not every time the function is called. If you mutate a default list, dictionary, or set inside the function, that modification persists across subsequent invocations throughout the application lifetime.

```python
# ✗ Bad: state persists across calls
def register_user(username: str, roles: list[str] = []) -> User:
    roles.append("viewer")
    ...

# ✓ Good: new list created per call
def register_user(username: str, roles: Sequence[str] | None = None) -> User:
    actual_roles = list(roles) if roles is not None else ["viewer"]
    ...
```

---

## 5. Method Decorators: "Avoid `@staticmethod`; prefer module-level functions"

### The Review Comment
> *"Avoid `@staticmethod`. Move this utility to a module-level private function `_helper()`."*

### Why It Matters
`@staticmethod` creates an artificial coupling between a function and a class namespace without utilizing any instance (`self`) or class (`cls`) state. It complicates testing, prevents easy standalone reuse, and adds syntactic overhead.

In Python, modules are natural namespaces. Functions that do not need class or instance attributes belong at the module level.

```python
# ✗ Bad
class TokenParser:
    @staticmethod
    def sanitize(raw_token: str) -> str:
        return raw_token.strip().lower()

# ✓ Good: module-level function
def _sanitize_token(raw_token: str) -> str:
    return raw_token.strip().lower()

class TokenParser:
    ...
```

---

## 6. Exceptions: "Chain exceptions using `raise ... from err`"

### The Review Comment
> *"When wrapping and re-raising an exception, use `raise NewError(...) from err` to preserve the underlying cause and traceback."*

### Why It Matters
Explicit exception chaining (`from err`) makes debugging significantly easier by clearly displaying both the low-level cause and the high-level semantic exception in the traceback. If you intentionally want to suppress the cause, use `from None`.

```python
# ✗ Bad: hides root cause or creates confusing traceback
try:
    data = json.loads(payload)
except json.JSONDecodeError:
    raise ConfigParseError("Failed to parse config payload")

# ✓ Good: explicitly chains the cause
try:
    data = json.loads(payload)
except json.JSONDecodeError as err:
    raise ConfigParseError(f"Failed to parse config payload: {err}") from err
```

---

## 7. Typing: "Prefer abstract container types for arguments"

### The Review Comment
> *"Type function inputs as `Sequence[T]` or `Iterable[T]` rather than concrete `list[T]`. Return concrete types `list[T]`."*

### Why It Matters
Accepting `Sequence[T]` allows callers to pass lists, tuples, or custom sequence types without forcing unnecessary conversions (`list(...)`). Returning concrete types guarantees callers know the exact capabilities of the returned object (e.g. they can index, slice, or append).

```python
# ✗ Bad: unnecessarily restrictive input
def total_length(items: list[str]) -> int:
    return sum(len(x) for x in items)

# ✓ Good: flexible input, concrete return
from collections.abc import Sequence

def total_length(items: Sequence[str]) -> int:
    return sum(len(x) for x in items)
```
