# Automated Verification Recipes & Probing Patterns

Concrete, runnable recipes for verifying friction fixes and workspace health during developer friction reviews.

---

## 1. FastAPI & Serving Endpoint Probing Suite

Probe local HTTP serving and discovery endpoints in memory using `TestClient` without needing to bind to host network ports:

```python
"""probe_endpoints.py — Run via: uv run python probe_endpoints.py"""
from fastapi.testclient import TestClient
# Import your FastAPI app instance
from my_app.fast_api_app import app

def test_routes():
    with TestClient(app) as client:
        # 1. Health Probe
        health = client.get("/healthz")
        print(f"GET /healthz -> {health.status_code}")
        assert health.status_code == 200, f"Health check failed: {health.text}"

        # 2. Agent Card Discovery (Root & Redirect)
        card = client.get("/.well-known/agent-card.json", follow_redirects=True)
        print(f"GET /.well-known/agent-card.json -> {card.status_code}")
        assert card.status_code == 200, f"Agent card failed: {card.text}"
        data = card.json()
        assert "name" in data or "description" in data, "Agent card missing core fields"

        # 3. App Listing
        apps = client.get("/list-apps")
        print(f"GET /list-apps -> {apps.status_code} {apps.json()}")
        assert apps.status_code == 200

        # 4. Session Initialization / API route
        session = client.post(
            "/api/reasoning_engine",
            json={"class_method": "create_session", "input": {"user_id": "probe_user"}}
        )
        print(f"POST /api/reasoning_engine -> {session.status_code}")
        assert session.status_code == 200, f"Session creation failed: {session.text}"

    print("\n✓ All serving endpoints probed successfully!")

if __name__ == "__main__":
    test_routes()
```

---

## 2. Unauthenticated Import Crash Probe

Verify that importing the application package does not crash if cloud credentials (ADC, API keys) are uninitialized in the developer environment:

```bash
# Temporarily clear credential environment variables and attempt package import
env -u GOOGLE_APPLICATION_CREDENTIALS -u GEMINI_API_KEY python3 -c "
import sys
try:
    import my_package
    print('✓ Package imported successfully without credentials!')
except Exception as e:
    print(f'✖ Import crashed without credentials: {e}', file=sys.stderr)
    sys.exit(1)
"
```

---

## 3. Container Hermeticity & `.dockerignore` Audit

Verify that sensitive files and bulky build caches are not sent to the Docker build context:

```bash
# Check if sensitive files exist in the build context
cat << 'EOF' > /tmp/check_dockerignore.sh
#!/usr/bin/env bash
set -euo pipefail

TARGET_DIR="${1:-.}"
DOCKERIGNORE="$TARGET_DIR/.dockerignore"

if [ ! -f "$DOCKERIGNORE" ]; then
  echo "✖ Missing .dockerignore in $TARGET_DIR"
  exit 1
fi

REQUIRED_PATTERNS=(
  ".env*"
  ".git"
  ".venv"
  "__pycache__"
  "*.pyc"
  ".ruff_cache"
  ".pytest_cache"
  "*.pem"
  "*.key"
)

ERRORS=0
for pattern in "${REQUIRED_PATTERNS[@]}"; do
  if ! grep -q -F "$pattern" "$DOCKERIGNORE"; then
    echo "⚠ Warning: '$pattern' not found in $DOCKERIGNORE"
    ERRORS=$((ERRORS + 1))
  fi
done

if [ "$ERRORS" -eq 0 ]; then
  echo "✓ .dockerignore contains all recommended exclusions"
else
  echo "✖ .dockerignore missing $ERRORS security/cache patterns"
  exit 1
fi
EOF
chmod +x /tmp/check_dockerignore.sh
/tmp/check_dockerignore.sh contrib/python/my-recipe
```

---

## 4. Test Segregation Gate: Offline vs Live

Ensure fast unit tests pass offline, and slow integration tests are clearly flagged:

```bash
# Gate 1: Run offline smoke and unit tests (must pass in CI and cold start)
uv run pytest tests/test_runnability.py -v

# Gate 2: Run live integration tests (only if live credentials are configured)
if [ -n "${GOOGLE_APPLICATION_CREDENTIALS:-}" ] || [ -n "${GEMINI_API_KEY:-}" ]; then
  echo "Credentials present: Running live integration suite..."
  uv run pytest tests/integration -v
else
  echo "Skipping live integration tests (no credentials configured)."
fi
```

---

## 5. Ecosystem Linters & Structure Checkers

Standard commands for validating workspace cleanliness:

### Python
```bash
# Linter check
uvx ruff check <path>/

# Formatter check
uvx ruff format --check <path>/

# Auto-fix formatting
uvx ruff format <path>/
```

### Node / TypeScript
```bash
# Linter
npx eslint <path>/

# Formatter check
npx prettier --check <path>/
```

### Go
```bash
# Vet and formatting
go vet ./...
gofmt -l .
```

### Bash Scripts
```bash
# Shellcheck
shellcheck <script-path>
```
