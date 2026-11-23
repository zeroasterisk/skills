# Google Python Docstrings Guide

Authoritative reference for formatting docstrings according to the [Google Python Style Guide](https://google.github.io/styleguide/pyguide.html#38-comments-and-docstrings).

---

## 1. Anatomy of a Google Docstring

Every docstring must use triple double quotes `"""` and follow this structure:

1. **Summary line**: A concise description on a single line, $\le 80$ characters, ending in a period. Can be imperative (`Fetch user record.`) or descriptive (`Fetches user record.`), but must remain consistent within a file.
2. **Blank line**: Required between the summary line and detailed prose (if present).
3. **Detailed description**: Explains behavior, edge cases, invariants, or side-effects.
4. **Sections**: `Args:`, `Returns:`, `Yields:`, `Raises:`, `Attributes:` as applicable.
5. **Closing quotes**: `"""` on its own line if the docstring spans multiple lines.

```python
def fetch_account(account_id: str, timeout_seconds: float = 5.0) -> Account:
    """Fetches an account record from the database.

    Queries the primary data store for the given account ID. If the primary
    replica is unreachable, falls back to the read replica.

    Args:
        account_id: Unique 12-character alphanumeric identifier.
        timeout_seconds: Maximum time in seconds to wait for a response.

    Returns:
        The matching Account instance with active permissions loaded.

    Raises:
        AccountNotFoundError: If no account exists for account_id.
        TimeoutError: If the remote database does not respond in time.
    """
```

---

## 2. Docstring Sections

Each section header begins with the section name followed by a colon. Content within the section is indented with 2 or 4 spaces (consistent within the file).

### `Args:`
Documents each parameter:
- When code is **type-annotated**, omit types from the docstring:
  ```python
  Args:
      user_id: The unique identifier for the user.
      force: Whether to override active cache locks.
  ```
- If the signature is not type-annotated, include types in parentheses:
  ```python
  Args:
      user_id (str): The unique identifier for the user.
      force (bool): Whether to override active cache locks.
  ```
- Parameter names should align cleanly with descriptions.

### `Returns:` (or `Yields:`)
Describes the returned value, its meaning, and any guarantees:
```python
Returns:
    A mapping from cluster name to the active node count.
```
For generators, use `Yields:` instead of `Returns:`:
```python
Yields:
    Chunks of decrypted binary data up to 64 KB each.
```

### `Raises:`
Lists exceptions that callers should anticipate and handle as part of the public interface. Do not document internal programming errors (such as unexpected `IndexError` bugs):
```python
Raises:
    ValueError: If port is outside the range 1024-65535.
    ConnectionError: If the network socket fails to connect.
```

---

## 3. Class and Module Docstrings

### Module Docstrings
Placed at the very top of `.py` files, after any shebang or license header, before imports:
```python
"""Batch processing utilities for streaming event logs.

This module provides workers and queue helpers to aggregate incoming telemetry
events into hourly partitioned storage buckets.

Typical usage example:

    processor = EventProcessor(batch_size=100)
    processor.consume_stream(stream_uri)
"""
```

### Class Docstrings
Describes the purpose of the class and documents public attributes:
```python
class RateLimiter:
    """Token-bucket rate limiter for outbound API calls.

    Attributes:
        rate_per_second: Maximum allowed sustained requests per second.
        burst_capacity: Maximum temporary burst allowance.
    """

    def __init__(self, rate_per_second: float, burst_capacity: int) -> None:
        self.rate_per_second = rate_per_second
        self.burst_capacity = burst_capacity
        self._tokens = float(burst_capacity)
```

---

## 4. Property Docstrings

The docstring for a `@property` should describe what the property represents (noun phrase), rather than using an action verb:

```python
# ✗ Bad
@property
def is_active(self) -> bool:
    """Returns whether the account is currently active."""
    return self._status == Status.ACTIVE

# ✓ Good
@property
def is_active(self) -> bool:
    """Whether the account is currently active."""
    return self._status == Status.ACTIVE
```

---

## 5. TODO Comments

Per Google style, all TODO comments must include the username of the person responsible in parentheses:

```python
# ✗ Bad
# TODO: add retry logic

# ✓ Good
# TODO(ghchinoy): Add exponential backoff retry logic for 503 responses.
```
