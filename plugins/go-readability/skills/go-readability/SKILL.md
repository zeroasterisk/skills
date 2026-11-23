---
name: go-readability
description: >-
  Write and review Go code to meet modern Go and Google readability standards. Covers style,
  naming, error handling, testing, documentation, package design, linting,
  mentor feedback, and CLI checklist. Use for "readability", "go style",
  "go naming", "go errors", "go testing", "idiomatic Go", "go best practices",
  "go code review", "go lint", or "go linting".
license: Apache-2.0
metadata:
  version: "1.0.0"
---

# Go Readability

Concise guide to writing idiomatic Go that passes rigorous code review and adheres to Google and standard Go readability guidelines. Distilled from the [Google Go Style Guide](https://google.github.io/styleguide/go/), [Effective Go](https://go.dev/doc/effective_go), and [Go Code Review Comments](https://go.dev/wiki/CodeReviewComments).

## Formatting

-   All code **must** be formatted with `gofmt` (`gofmt -s -w .`) or `goimports`
-   No strict line length limit, but refactor long lines for clarity and readability
-   Organize packages cleanly following standard Go conventions (`cmd/`, `internal/`, `pkg/`, or flat layout)
-   Import paths should match standard Go module paths declared in `go.mod`

## Linting

Run standard linters (`golangci-lint`, `go vet`, `staticcheck`) regularly during development:

-   Run `gofmt -s -w .` to auto-format Go files
-   Run `go vet ./...` to check for common mistakes and suspicious constructs
-   Run `golangci-lint run` for comprehensive static analysis
-   To suppress specific lint warnings where strictly necessary, use `//nolint:RULE` comments:

    ```go
    value := someFunc() //nolint:errcheck
    ```

## Naming

Go uses **MixedCaps** (camelCase), not snake_case. **The only exception is test function names**, where underscores separate the function under test from the condition being tested (e.g. `TestParse_EmptyInput`, `TestParse_InvalidUTF8`).

Kind       | Convention                   | Example
---------- | ---------------------------- | -------------------------
Exported   | `UpperCamelCase`             | `UserManager`
Unexported | `lowerCamelCase`             | `userCount`
Package    | `lowercase` (no underscores) | `userutils`
Acronym    | All caps if exported         | `HTTPClient`, `xmlParser`

-   **Avoid** repeating the package name: `net.Conn` not `net.NetConn` (exception: eponymous types like `regexp.Regexp`)
-   **Avoid `Get` / `get` prefix** for plain getters: `u.Name()` not `u.GetName()`. If the call performs a remote/expensive operation that may take time, block, or fail, name it with a verb that signals that — use `Fetch` (for remote calls / I/O) or `Compute` (for expensive computation), NOT `Get`. See [decisions#getters](https://google.github.io/styleguide/go/decisions#getters).
    -   `getRolloutConfig(...)` (calls API/network) → `fetchRolloutConfig(...)`
    -   `GetUserCount()` (returns a stored field) → `UserCount()`
    -   `ComputeFingerprint()` (CPU-heavy hashing) → keep `Compute` prefix
-   **Receiver names**: 1-2 letters, abbreviation of the type, **applied consistently to every receiver for that type**. NEVER use `this`, `self`, or the full type name. `func (t *Tray) ...` not `func (tray *Tray) ...`, `func (this *X) ...`, or `func (self *X) ...`. See [decisions#receiver-names](https://google.github.io/styleguide/go/decisions#receiver-names).
-   Avoid uninformative package names: `util`, `common`, `helper`, `model` (these often indicate poor package design). Domain-specific utility packages are fine (e.g., `netutil` for network utilities).
-   **Avoid Generic Variable Names**: Outside of minimal local scopes with standard short names (`err`, `ctx`, `r`, `w`), avoid uninformative, cryptic, or generic single-word variable/parameter names (`id`, `p`, `res`, `data`, `obj`, `temp`, `val`, `resp`). Use clear, descriptive, domain-specific names instead (`userID`/`accountID`, `pageSize`/`priority`, `response`/`backendResponse`, `config`, `payload`/`parsedPayload`).
-   Functions returning something → noun-like names, like `strings.Fields`
-   Functions doing something → verb-like names, like `strings.TrimSpace`

## Imports

-   Group imports into standard blocks separated by blank lines:
    1. Standard library packages
    2. Third-party external packages
    3. Local module packages
-   Use `goimports` to automatically manage import grouping and ordering
-   Avoid redundant import aliases: do not alias if the alias is identical to the package name or already unambiguous at call sites
-   Rename generated protobuf imports to use a `pb` suffix (e.g., `userpb`) for clarity and consistency

## Error Handling

-   **Always** handle errors explicitly — `if err != nil { ... }`
-   Return errors, don't panic (panic is for truly unrecoverable situations). See **Don't panic / Must functions** below.
-   Add context when wrapping: `fmt.Errorf("loading config: %w", err)`
-   Use `%w` to wrap errors **if callers need** `errors.Is`/`errors.As` (e.g., to check for a specific sentinel error or extract a specific error type).
-   Use `%v` when you intentionally want to break the error chain or the caller does not need to inspect the underlying error (e.g., for security reasons, or when the underlying error is an implementation detail).
-   Define sentinel errors as package-level vars: `var ErrNotFound = errors.New("not found")`
-   Use structured logging (`log/slog`) for application logs

```go
func ProcessRequest() error {
    // ✗ Bad -- ignores error
    result, _ := DoSomething()

    // ✓ Good -- handles error
    result, err := DoSomething()
    if err != nil {
        return fmt.Errorf("processing request: %w", err)
    }
    return nil
}
```

### Error string formatting

Per [decisions#error-strings](https://google.github.io/styleguide/go/decisions#error-strings):

-   **Lowercase** (errors are usually wrapped in larger context before printing).
-   **No terminal punctuation** (no trailing `.`, `!`, or `?`).
-   **Exception**: starting with a proper noun, an acronym, or an exported Go identifier (`ProductConfig`, `URL`, `IPv6`) is fine and expected — those keep their canonical capitalization.

```go
// ✗ Bad
err := fmt.Errorf("Something bad happened.")

// ✓ Good
err := fmt.Errorf("something bad happened")

// ✓ Good (exported identifier)
err := fmt.Errorf("ProductConfig has both UnitKindName and UnitKindNames set")
```

### Use `%q` for quoted strings

Per [decisions#use-percent-q](https://google.github.io/styleguide/go/decisions#use-percent-q):
prefer `%q` over **manually wrapping** `%s` in single or double quotes. `%q` escapes control characters and makes empty strings (`""`) visible — both critical for debuggability. This applies to error strings, log messages, AND test failure messages.

```go
// ✗ Bad: manual quotes
fmt.Errorf("failed to read config '%s': %w", name, err)
fmt.Errorf("value \"%s\" looks like text", text)
slog.Info(fmt.Sprintf("Checking item '%s' at '%s'...", name, loc))

// ✓ Good
fmt.Errorf("failed to read config %q: %w", name, err)
fmt.Errorf("value %q looks like text", text)
slog.Info("checking item", "item", name, "location", loc)
```

**When NOT to use `%q`**: numeric values (`%d`, `%v`), error values (`%v` / `%w`), slices/maps/structs (`%v` / `%+v`), and pre-formatted multi-line output like `cmp.Diff` results (`%s`).

### Indent error flow (line of sight)

Per [decisions#indent-error-flow](https://google.github.io/styleguide/go/decisions#indent-error-flow):
handle errors first and return early. The "happy path" stays at the left-most indent — never inside an `else` block.

```go
// ✗ Bad: happy path is indented inside else
if err != nil {
    return err
} else {
    // normal code that looks abnormal due to indentation
    process(x)
    return nil
}

// ✓ Good: happy path stays at the left margin
if err != nil {
    return err
}
process(x)
return nil
```

### Don't panic / `Must` functions

Per [decisions#dont-panic](https://google.github.io/styleguide/go/decisions#dont-panic) and [decisions#must-functions](https://google.github.io/styleguide/go/decisions#must-functions):

-   **Don't `panic`** for normal error handling. Return an `error` and multiple return values.
-   In `package main` / CLI initialization code, exit cleanly with a clear error message (e.g., `os.Exit(1)`) rather than panicking with an unhelpful stack trace for user input errors.
-   For **package-level variable initializers** that genuinely cannot fail after a one-time setup, the `MustXYZ` (or `mustXYZ`) naming convention signals "panics on failure". Use sparingly:
    -   `template.Must`, `regexp.MustCompile`, `MustParse(...)`.
    -   In tests, `must*` helpers are fine if they call `t.Fatal` (mark with `t.Helper()`).
    -   NEVER call a `Must` function on user input or in a request handler — only on package-init constants.

## Documentation

-   **All exported names** must have doc comments
-   Comments are **full sentences**, ending with a period, starting with the name being documented (e.g., `// Foo does X.`).
-   Package comment: `// Package foo provides ...`
-   Function comment: `// FetchUser retrieves a user by ID.`
-   Use `//` comments, not `/* */`

```go
// A UserManager manages the lifecycle of user accounts.
type UserManager struct { ... }

// Create creates a new user with the given name.
func (m *UserManager) Create(name string) (*User, error) { ... }
```

## Testing

-   Use the standard `testing` package
-   **Table-driven tests** are strongly preferred
-   Test function names: `TestFunctionName` for single-scenario tests, or `TestFunctionName_Condition` when one target has multiple test functions (e.g. `TestParse_EmptyInput`, `TestParse_InvalidUTF8`). Underscores are permitted in test, benchmark, and example names ONLY (see [decisions#mixed-caps](https://google.github.io/styleguide/go/decisions#mixed-caps)).
-   Use `t.Helper()` in test helper functions
-   Use `cmp.Diff` (from `"github.com/google/go-cmp/cmp"`) for deep comparisons
-   Assert libraries (and custom assert helpers) are discouraged — use standard `t.Errorf`/`t.Fatalf` (see [decisions#assert](https://google.github.io/styleguide/go/decisions#assert)).
-   To get the context for use in tests, use `ctx := t.Context()` from `t *testing.T` (Go 1.24+) instead of `ctx := context.Background()`. `t.Context()` is automatically canceled when the test ends, preventing goroutine leaks and honoring test timeouts.

```go
func TestAdd_TableDriven(t *testing.T) {
    tests := []struct {
        name string
        a, b int
        want int
    }{
        {name: "positive", a: 1, b: 2, want: 3},
        {name: "zero", a: 0, b: 0, want: 0},
    }
    for _, tc := range tests {
        t.Run(tc.name, func(t *testing.T) {
            if got := Add(tc.a, tc.b); got != tc.want {
                t.Errorf("Add(%d, %d) = %d, want %d", tc.a, tc.b, got, tc.want)
            }
        })
    }
}
```

### Useful test failures (CRITICAL)

A test that fails should be diagnosable WITHOUT reading the test source. Use the canonical failure-message format:

```text
YourFunc(<inputs>) = <got>, want <want>
```

Per [decisions#useful-test-failures](https://google.github.io/styleguide/go/decisions#useful-test-failures), the message must convey: **what caused the failure**, **the inputs**, **what was actually returned**, **what was expected**.

The two most important rules here:

1.  **Identify the function** ([decisions#identify-the-function](https://google.github.io/styleguide/go/decisions#identify-the-function)) in the failure message, even if `TestXxx` makes it obvious.
2.  **Identify the input** ([decisions#identify-the-input](https://google.github.io/styleguide/go/decisions#identify-the-input)): print the function inputs in `%v` or `%+v` form. Under a subtest (`t.Run`), the subtest name already prefixes the failure, so there is no need to repeat the case `name` in the message itself.

```go
// ✗ Bad: missing both function name and inputs
t.Errorf("got %q, want %q", got, want)

// ✗ Bad: function name present but inputs missing
t.Errorf("calculateRate() = %q, want %q", got, want)
t.Errorf("groupItemsByCategory() succeeded, expected error")

// ✓ Good: function + inputs + got + want, in canonical form.
t.Errorf("calculateRate(%+v, %v) = %q, want %q",
    cfg, rates, got, want)
t.Errorf("groupItemsByCategory(%q, %v, %+v) succeeded, want error",
    env, categoryNames, items)
```

Quick rules to keep in mind:
-   **Got before want** for `cmp.Diff(want, got)`: include the legend `(-want +got)` in the message.
-   **`t.Error` over `t.Fatal`** unless subsequent checks would be meaningless or cause panics.
-   **Subtest names**: identifier-style. Avoid slashes — they collide with test filter flags.
-   **Use `%q`** for string inputs/outputs in failure messages so empty strings and control chars are visible.
-   See `references/testing_failures.md` for a comprehensive deep-dive.

## Interfaces

-   Keep interfaces **small** — prefer 1-2 methods
-   Define interfaces at the **consumer**, not the producer
-   Name single-method interfaces with `-er` suffix: `Reader`, `Writer`
-   Accept interfaces, return concrete types

## Concurrency

-   Use goroutines and channels **sparingly**, only where needed
-   Always use `context.Context` for cancellation and deadlines
-   Pass `ctx` as the **first parameter**
-   Don't store `context.Context` in structs

## Package Design

-   A package should be the transitive closure of closely related ideas — all types and functions a caller would naturally use together
-   Avoid circular dependencies between packages
-   Avoid type aliases and `internal` packages as workarounds for package structure; restructure instead

## Receiver type (pointer vs value)

Per [decisions#receiver-type](https://google.github.io/styleguide/go/decisions#receiver-type): **correctness wins over speed or simplicity**. Quick rules:

-   **MUST** use a pointer receiver if the method mutates the receiver, or if the struct contains fields that cannot safely be copied (e.g. anything embedding `sync.Mutex`).
-   **Use a value receiver** for small types whose methods don't mutate state.
-   **Make the methods for a type either all-pointer or all-value** — don't mix.
-   When in doubt: pointer receiver.

## Switch & break

Per [decisions#switch-break](https://google.github.io/styleguide/go/decisions#switch-break): Go `switch` cases automatically break — a bare `break` is redundant. To break out of an enclosing `for`, use a labeled `break`:

```go
loop:
for {
    switch x {
    case "A":
        break loop  // exits the loop
    }
}
```

## Nil slices

Per [decisions#nil-slices](https://google.github.io/styleguide/go/decisions#nil-slices): prefer `var s []T` over `s := []T{}` for empty-slice declarations. `len`, `cap`, `range`, and `append` all work on nil slices. Don't design APIs that force callers to distinguish nil from empty — use `len(s) == 0` to test for emptiness, not `s == nil`.

```go
// ✓ Good
var t []string

// ✗ Bad (when nothing forces non-nil)
t := []string{}
```

## Common Gotchas

-   Don't shadow named returns — it causes subtle bugs
-   `defer` runs at function exit, not scope exit (be careful in loops)
-   Slices share underlying arrays — copy if needed: `slices.Clone(s)`
-   `nil` maps can be read but panic on write — always `make(map[K]V)`
-   String iteration yields runes, not bytes — `len(s)` returns byte count, not character count. Use `utf8.RuneCountInString(s)` for rune count

## Deep-Dive References

For more detail on specific topics, see these reference files:

-   `references/common_mentor_feedback.md` — Detailed guide to frequent readability reviewer comments (naming, error handling, documentation, interfaces, concurrency, common gotchas)
-   `references/testing_failures.md` — Authoritative deep-dive on the 9 sub-decisions under `decisions#useful-test-failures`.
-   `references/decisions_index.md` — One-line-per-rule index of style decisions mapping to rules and examples.
-   `references/standard_go_patterns.md` — Reference for standard modern Go patterns (modules, logging with `slog`, flags, testing with `cmp.Diff`, contexts)
-   `references/self_audit_checklist.md` — Mechanical recursive greps for catching common style violations before submitting code.
-   `scripts/audit-go-readability.sh` — Executable recursive scanner that runs the self-audit checklist across an entire Go repository (`./scripts/audit-go-readability.sh /path/to/repo`).
-   `references/cli_review_checklist.md` — Comprehensive Go CLI review checklist covering 12 categories of issues.
-   `references/cobra_cli_patterns.md` — Cobra-specific patterns (package doc scope, `ctx` naming, inlining timeouts, testing `package main`).
-   `references/before_after_examples.md` — Before/after code transformations showing common fixes reviewers request.

## Review Guidelines

When reviewing or generating Go code, check for these common pitfalls:

1.  **Duplicate Code** — Extract repeated logic into helpers when it improves clarity
2.  **Function Naming** — Names must describe what the function actually does
3.  **Command Design** — Split multi-mode commands into one-command-per-action
4.  **Conflicting Flag Guards** — Guard against mutually exclusive flags
5.  **Error Handling** — Never silently ignore errors
6.  **Input Sanitization** — Sanitize user input before embedding in structured formats
7.  **Security & Privacy** — Prevent unintentional data exposure
8.  **Dangerous Operations** — Require confirmation for destructive actions
9.  **Control Flow Clarity** — Restructure complex conditionals for readability
10. **Logic Bugs** — Watch for dead code, unhandled error returns, or ignored output flags
11. **Idiomatic Go** — Prefer `strings.Cut`, `slices.Repeat`, `filepath.Ext`, descriptive names
12. **Code Style** — Consolidate var declarations, format cleanly with `gofmt`

## Key Resources

-   [Google Go Style Guide](https://google.github.io/styleguide/go/guide) — Core style guide
-   [Google Go Style Decisions](https://google.github.io/styleguide/go/decisions) — Detailed style decisions
-   [Google Go Best Practices](https://google.github.io/styleguide/go/best-practices) — Engineering best practices
-   [Effective Go](https://go.dev/doc/effective_go) — Foundational Go guide
-   [Go Code Review Comments](https://go.dev/wiki/CodeReviewComments) — Standard Go idioms
-   [Go Blog: Working with Errors in Go 1.13](https://go.dev/blog/go1.13-errors) — Error wrapping guidance
