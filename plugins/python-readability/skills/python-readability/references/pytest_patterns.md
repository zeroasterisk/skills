# Pytest Patterns and Best Practices

Modern test authoring guidelines for Python using `pytest`, aligning with Google readability and maintainable test design.

---

## 1. Table-Driven Tests with `@pytest.mark.parametrize`

Prefer parameterized tests over multiple near-duplicate test functions. Always provide clear, descriptive case IDs via `ids=`:

```python
import pytest
from my_project.parsers import url_parser

@pytest.mark.parametrize(
    ("raw_url", "expected_host", "expected_port"),
    [
        ("https://example.com", "example.com", 443),
        ("http://localhost:8080", "localhost", 8080),
        ("ftp://files.example.com", "files.example.com", 21),
    ],
    ids=["standard_https", "custom_http_port", "ftp_default_port"],
)
def test_parse_host_and_port(
    raw_url: str,
    expected_host: str,
    expected_port: int,
) -> None:
    host, port = url_parser.parse(raw_url)
    assert host == expected_host
    assert port == expected_port
```

---

## 2. Exception Testing with `pytest.raises` and `match`

Always verify both the exception type and the expected error message or pattern using `match`:

```python
import pytest
from my_project.models import account

def test_negative_deposit_raises_value_error() -> None:
    acc = account.Account(balance=100)

    with pytest.raises(ValueError, match=r"Deposit amount must be positive, got -50"):
        acc.deposit(-50)
```

Without `match=`, a test might pass even if the function raised the expected exception class for an entirely unrelated, unexpected reason.

---

## 3. Fixtures and Lifecycle Management

Use fixtures for reusable setup and teardown. Prefer `yield` fixtures for resources requiring cleanup:

```python
from collections.abc import Generator
from pathlib import Path
import pytest
from my_project.db import session

@pytest.fixture
def db_session(tmp_path: Path) -> Generator[session.Session, None, None]:
    """Provides an isolated SQLite test database session."""
    db_file = tmp_path / "test.db"
    sess = session.create_session(f"sqlite:///{db_file}")
    sess.initialize_schema()

    yield sess

    sess.close()
```

- Use `tmp_path` (a `pathlib.Path` object) for filesystem isolation.
- Keep fixtures focused and minimal; avoid creating global fixture monoliths.

---

## 4. Avoiding Mock Abuse

Heavy use of `unittest.mock.patch` leads to brittle tests that pass even when real contracts break:

- **Prefer Real Implementations**: For fast, in-memory components (dataclasses, simple parsers, validators), use real objects.
- **Prefer Fakes over Mocks**: For I/O boundaries (databases, HTTP clients), implement a lightweight in-memory fake that satisfies a `Protocol` interface.
- **Narrow Mocks**: If mocking is unavoidable, mock at the highest architectural boundary (e.g. the service client), not private internal functions.

```python
# ✓ Good: In-memory fake client implementing Protocol
class FakeNotificationClient:
    def __init__(self) -> None:
        self.sent_messages: list[str] = []

    def send_alert(self, message: str) -> None:
        self.sent_messages.append(message)

def test_alert_on_failure() -> None:
    fake_client = FakeNotificationClient()
    monitor = SystemMonitor(notifier=fake_client)
    monitor.record_failure("Disk full")

    assert fake_client.sent_messages == ["Disk full"]
```
