# Modern Python Typing Patterns

Guide to writing clean, idiomatic, and strictly checked Python type annotations per Google style and modern PEPs (PEP 585, PEP 604, PEP 544).

---

## 1. Modern Syntax Standards (Python 3.10+)

Always prefer modern built-in generics and union syntax over legacy `typing` imports:

| Category | Modern (Python 3.10+) | Legacy (Deprecated Style) |
| :--- | :--- | :--- |
| **Optional / Nullable** | `str \| None` | `Optional[str]` or `Union[str, None]` |
| **Union Types** | `int \| float` | `Union[int, float]` |
| **Lists** | `list[str]` | `typing.List[str]` |
| **Dictionaries** | `dict[str, Any]` | `typing.Dict[str, Any]` |
| **Tuples** | `tuple[int, str]` or `tuple[int, ...]` | `typing.Tuple[int, str]` |
| **Sets** | `set[int]` | `typing.Set[int]` |

```python
# ✓ Good: clean modern typing
def parse_record(
    raw_id: str | None,
    values: list[float],
) -> dict[str, float] | None:
    ...
```

---

## 2. Abstract Containers for Inputs, Concrete for Outputs

Follow the robust principle: **be liberal in what you accept, specific in what you return**.

- **Function Parameters**: Accept `Sequence[T]`, `Mapping[K, V]`, `Iterable[T]`, or `Set[T]` from `collections.abc`. This allows callers to pass lists, tuples, sets, or custom collections without casting.
- **Return Types**: Return concrete types like `list[T]`, `dict[K, V]`, or exact dataclasses so callers have full access to concrete methods.

```python
from collections.abc import Mapping, Sequence

# ✓ Good
def extract_keys(
    data: Mapping[str, int],
    filters: Sequence[str],
) -> list[str]:
    return [k for k in data if k in filters]
```

---

## 3. Structural Subtyping with `Protocol`

When typing behaviors rather than concrete class hierarchies, use `typing.Protocol` (PEP 544) instead of deep abstract base classes:

```python
from typing import Protocol

class Serializable(Protocol):
    """Protocol for objects capable of serializing to JSON."""

    def to_json(self) -> str:
        ...

def write_to_disk(item: Serializable, path: str) -> None:
    content = item.to_json()
    ...
```

Any class implementing `to_json() -> str` satisfies `Serializable` without explicit inheritance.

---

## 4. Generic Functions and Type Variables

Define `TypeVar` with clear bounds or constraints when a function's return type depends on its input type:

```python
from collections.abc import Sequence
from typing import TypeVar

T = TypeVar("T")

def first_or_default(items: Sequence[T], default: T) -> T:
    """Returns the first element of a sequence or default if empty."""
    return items[0] if items else default
```

In Python 3.12+, PEP 695 generic syntax is also supported:
```python
def first_or_default[T](items: Sequence[T], default: T) -> T:
    return items[0] if items else default
```

---

## 5. Avoiding `Any`

Excessive use of `Any` disables type checker guarantees. Prefer safer alternatives:

- Use `object` if the value is truly opaque and only used for identity or string representation:
  ```python
  def log_identity(value: object) -> None:
      logging.info("Object at: %s", id(value))
  ```
- Use generic `T` or bounded `TypeVar` if the value preserves its type through a pipeline.
- Use `TypedDict` for structured dictionary payloads rather than `dict[str, Any]`:
  ```python
  from typing import TypedDict

  class UserPayload(TypedDict):
      username: str
      age: int
      active: bool
  ```
