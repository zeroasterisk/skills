# Before & After Examples

Concrete code transformations illustrating common Google Python Readability refactorings.

---

## Example 1: Imports and Package Layout

### ✗ Before: Deep symbol imports and relative imports
```python
# In my_project/services/order_service.py
from ..models.order import Order, OrderStatus
from ..utils.math_utils import calculate_tax, round_currency
from ..clients.payment_client import PaymentGatewayClient

def process_order(order_id: str) -> Order:
    client = PaymentGatewayClient()
    ...
```

### ✓ After: Absolute module-level imports
```python
# In my_project/services/order_service.py
from my_project.clients import payment_client
from my_project.models import order
from my_project.utils import math_utils

def process_order(order_id: str) -> order.Order:
    client = payment_client.PaymentGatewayClient()
    ...
```

---

## Example 2: Preconditions and Invariants

### ✗ Before: Using `assert` in application logic
```python
def resize_image(image_bytes: bytes, max_width: int, max_height: int) -> bytes:
    assert len(image_bytes) > 0, "Image bytes cannot be empty"
    assert max_width > 0 and max_height > 0, "Dimensions must be positive"
    ...
```

### ✓ After: Explicit exception checks
```python
def resize_image(image_bytes: bytes, max_width: int, max_height: int) -> bytes:
    if not image_bytes:
        raise ValueError("Image bytes cannot be empty")
    if max_width <= 0 or max_height <= 0:
        raise ValueError(
            f"Dimensions must be positive integers, got {max_width}x{max_height}"
        )
    ...
```

---

## Example 3: Mutable Default Arguments

### ✗ Before: List instantiated at module import
```python
def compile_report(
    title: str,
    sections: list[str] = [],
    options: dict[str, str] = {},
) -> Report:
    sections.append("Appendix")
    ...
```

### ✓ After: Sentinel default with runtime instantiation
```python
from collections.abc import Mapping, Sequence

def compile_report(
    title: str,
    sections: Sequence[str] | None = None,
    options: Mapping[str, str] | None = None,
) -> Report:
    actual_sections = list(sections) if sections is not None else []
    actual_options = dict(options) if options is not None else {}
    actual_sections.append("Appendix")
    ...
```

---

## Example 4: Unused Arguments in Callback Signatures

### ✗ Before: Renaming with underscores
```python
class WebhookHandler:
    def on_event(self, event_name: str, payload: dict[str, Any], _request_id: str) -> None:
        logging.info("Received event: %s", event_name)
```

### ✓ After: Explicit deletion with comment
```python
class WebhookHandler:
    def on_event(self, event_name: str, payload: dict[str, Any], request_id: str) -> None:
        del request_id  # Unused by this handler.
        logging.info("Received event: %s", event_name)
```

---

## Example 5: Exception Chaining

### ✗ Before: Swallowing original cause or uninformative message
```python
def load_configuration(path: str) -> AppConfig:
    try:
        with open(path, "r", encoding="utf-8") as f:
            raw = yaml.safe_load(f)
        return AppConfig(**raw)
    except Exception:
        raise ConfigError("Failed to load config")
```

### ✓ After: Narrow exception, descriptive message, chained traceback
```python
def load_configuration(path: str) -> AppConfig:
    try:
        with open(path, "r", encoding="utf-8") as f:
            raw = yaml.safe_load(f)
        return AppConfig(**raw)
    except (OSError, yaml.YAMLError, TypeError) as err:
        raise ConfigError(f"Failed to load config from {path}: {err}") from err
```

---

## Example 6: Static Methods to Module-Level Functions

### ✗ Before: `@staticmethod` inside a class namespace
```python
class HashUtil:
    @staticmethod
    def sha256_hex(data: bytes) -> str:
        return hashlib.sha256(data).hexdigest()
```

### ✓ After: Clean module-level function
```python
def sha256_hex(data: bytes) -> str:
    """Computes the hex-encoded SHA-256 digest of data."""
    return hashlib.sha256(data).hexdigest()
```
