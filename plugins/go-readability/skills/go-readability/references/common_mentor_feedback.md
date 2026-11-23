# Common Go Readability Reviewer Feedback

Distilled from real-world Go code reviews and the [Google Go Style Guide](https://google.github.io/styleguide/go/) — the most frequent comments Go readability reviewers give.

## Naming

### Avoid Repetitive Naming

Don't repeat the package name in exported identifiers. Callers already qualify with the package name.

```go
// ✗ Repetitive -- callers write `userutils.UserManager`
package userutils
type UserManager struct{}

// ✓ Clean -- callers write `userutils.Manager`
package userutils
type Manager struct{}
```

### Getters Have No Prefix

Per [decisions#getters](https://google.github.io/styleguide/go/decisions#getters): don't use `Get` / `get` prefix for getters. For functions that perform a remote call or expensive computation, use a different verb that signals the cost: `Fetch` for I/O, `Compute` for CPU-heavy work — NOT `Get`. The `Get` prefix is reserved for the underlying concept actually being a "get" (like HTTP GET).

```go
// ✗ Redundant prefix on plain accessor
func (u *User) GetName() string { return u.name }

// ✓ Idiomatic
func (u *User) Name() string { return u.name }

// ✗ Get prefix on a remote-call method (misleads about cost)
func getResourceMetadata(id, region string) (string, error) {
    return callRemoteAPI(...) // performs an RPC / HTTP request
}

// ✓ Fetch prefix signals "remote call may take time / fail"
func fetchResourceMetadata(id, region string) (string, error) {
    return callRemoteAPI(...)
}

// ✓ Compute prefix for expensive in-process computation
func ComputeFingerprint(data []byte) [32]byte {
    return sha256.Sum256(data)
}
```

### Acronyms

Keep acronyms consistent: all caps if exported, all lower if unexported.

```go
// ✓ Correct
type HTTPClient struct{}   // exported
var xmlParser *Parser      // unexported -- whole acronym lower
func ServeHTTP(...)        // exported
var userID string          // when capitalized, ID is spelled with a capital D
```

### Avoid Meaningless Names

Packages named `util`, `common`, `helper`, `base`, `model` are red flags. Name packages after what they provide, not how generic they are.

```go
// ✗ What does this package do?
package util

// ✓ Clear purpose
package configloader
```

### Variable Names

Go prefers short names in limited scopes. Don't be unnecessarily verbose.

```go
// ✗ Over-verbose for a loop variable
for userIndex := range users { ... }

// ✓ Short, clear in context
for i, u := range users { ... }

// But DO use descriptive names for broader scopes
func ProcessOrder(order *CustomerOrder) error { ... }
```

## Error Handling

### Always Handle Errors

Never use the blank identifier for errors unless you truly intend to discard (and you should comment why).

```go
func ProcessRequest() error {
    // ✗ Silent failure
    result, _ := DoSomething()

    // ✓ Handle it
    result, err := DoSomething()
    if err != nil {
        return fmt.Errorf("processing request: %w", err)
    }
    return nil
}
```

### Wrap with Context

Usually add context when propagating errors. The context should describe what the current function was trying to do.

```go
// ✗ No context -- hard to trace
if err != nil {
    return err
}

// ✓ Context added -- easy to trace
if err != nil {
    return fmt.Errorf("loading user config for %q: %w", username, err)
}
```

### %w vs %v

Use `%w` to wrap errors if callers are expected to inspect the error with `errors.Is` / `errors.As`. Use `%v` when you intentionally want to break the error chain, or if it's not clear that the caller needs to inspect the underlying error.

```go
// Preserves error chain (caller needs to inspect)
return fmt.Errorf("parsing config: %w", err)

// Breaks error chain (intentional, or caller doesn't need to inspect)
return fmt.Errorf("parsing config: %v", err)
```

### Sentinel Errors

Define package-level sentinel errors for expected conditions.

```go
var ErrNotFound = errors.New("not found")
var ErrPermissionDenied = errors.New("permission denied")

// Callers can check:
if errors.Is(err, ErrNotFound) { ... }
```

## Documentation

### Every Exported Name

All exported types, functions, methods, variables, and constants must have doc comments.

```go
// ✗ Missing doc comment
func ProcessBatch(items []*Item) error { ... }

// ✓ Doc comment starts with the name

// ProcessBatch processes all items in a single transaction.
func ProcessBatch(items []*Item) error { ... }
```

### Comment Format

Comments are full sentences. Start with the name of the thing being documented.

```go
// ✗ Not a sentence, doesn't start with name

// processes the user
func Process(u *User) {}

// ✓ Full sentence, starts with function name

// Process validates and stores the user in the database.
func Process(u *User) error {}
```

### Package Comments

Every package needs a package comment. For multi-file packages, put it in `doc.go` or above the main package declaration.

```go
// Package configloader loads and validates application configuration
// from disk files and environment variables.
package configloader
```

## Interfaces

### Keep Small

Interfaces should be as small as possible — ideally 1-2 methods.

```go
// ✗ Too wide -- hard to implement and mock
type DataStore interface {
    Read(key string) (Value, error)
    Write(key string, v Value) error
    Delete(key string) error
    List(prefix string) ([]Value, error)
    Watch(key string) <-chan Value
    Close() error
}

// ✓ Small, composable
type Reader interface {
    Read(key string) (Value, error)
}
```

### Define at the Consumer

Define interfaces where they are used, not where they are implemented.

```go
// ✗ In the producer package
package storage
type Store interface { ... }
type FileStore struct { ... }

// ✓ In the consumer package
package userservice
type UserLoader interface {
    Load(ctx context.Context, id string) (*User, error)
}
```

## Concurrency

### Context First

Always pass `context.Context` as the first parameter. Never store it in a struct.

```go
// ✗ Bad -- context in struct
type Server struct {
    ctx context.Context
}

// ✓ Good -- context as first param
func (s *Server) HandleRequest(ctx context.Context, req *Request) error {}
```

### Goroutine Cleanup

Always ensure goroutines can be stopped. Use context cancellation or done channels.

```go
func Watch(ctx context.Context, ch <-chan *Item) {
    go func() {
        for {
            select {
            case <-ctx.Done():
                return
            case item := <-ch:
                process(item)
            }
        }
    }()
}
```

## Common Gotchas

### Nil Maps

A nil map can be read (returns zero value) but panics on write. Always initialize maps.

```go
// ✗ Panics on write
var m map[string]int
m["key"] = 1  // panic!

// ✓ Initialize first
m := make(map[string]int)
m["key"] = 1
```

### Slice Aliasing

Slices share underlying arrays. Appending to a sub-slice can overwrite the original.

```go
// ✗ Modifies original
sub := original[:3]
sub = append(sub, newItem)  // may overwrite original[3]

// ✓ Copy first
sub := slices.Clone(original)
sub = append(sub, newItem)
```

### Defer Timing

`defer` runs at function exit, not block exit. Be careful in loops.

```go
// ✗ Files stay open until function returns
for _, name := range files {
    f, err := os.Open(name)
    if err != nil { return err }
    defer f.Close()  // won't close until loop's function returns
    if err := process(f); err != nil {
        return err
    }
}

// ✓ Pass the file to a helper function that defers Close:
for _, name := range files {
    if err := processFile(name); err != nil {
        return err
    }
}

// ✓ Or use an explicit Close:
for _, name := range files {
    f, err := os.Open(name)
    if err != nil {
        return err
    }
    err = process(f)
    f.Close()
    if err != nil {
        return err
    }
}
```

## Code Organization

### Exported Functions First

In a Go source file, exported functions and types **MUST** appear before unexported helpers. Readers scan top-to-bottom; the most important entry points **SHOULD** be encountered first.

```go
// ✗ BEFORE - exported RunTask buried after unexported helpers
func formatOutput(i int, res *Result) string { ... }
func groupResults(results []*Result) map[string][]*Result { ... }

func RunTask(ctx context.Context, ...) error {
    ...
}

// ✓ AFTER - RunTask first; helpers follow
func RunTask(ctx context.Context, ...) error {
    ...
}

func formatOutput(i int, res *Result) string { ... }
func groupResults(results []*Result) map[string][]*Result { ... }
```

The same rule applies to **test files**: exported test functions (`TestX`) **MUST** appear before unexported test helpers.

```go
// ✗ BEFORE - test helper before the test that uses it
func makeFixture(t *testing.T, ...) { ... }

func TestProcess(t *testing.T) {
    ...
}

// ✓ AFTER - test first, helper after
func TestProcess(t *testing.T) {
    ...
}

func makeFixture(t *testing.T, ...) { ... }
```

## Testing

### Cache Repeated Method Calls

When the same method call appears multiple times to read the same value, assign the result to a named variable first.

```go
// ✗ BEFORE - buf.String() called multiple times
if !strings.Contains(buf.String(), tc.wantOut) {
    t.Errorf("output missing %q\nfull output:\n%s", tc.wantOut, buf.String())
}
if !strings.Contains(buf.String(), "123456") {
    t.Errorf("output missing ID\nfull output:\n%s", buf.String())
}

// ✓ AFTER - captured once
gotOutput := buf.String()
if !strings.Contains(gotOutput, tc.wantOut) {
    t.Errorf("output missing %q\nfull output:\n%s", tc.wantOut, gotOutput)
}
if !strings.Contains(gotOutput, "123456") {
    t.Errorf("output missing ID\nfull output:\n%s", gotOutput)
}
```

### Useful Test Failure Messages

See `references/testing_failures.md` for the full deep dive.

-   **Identify the function**: `t.Errorf("Add(%d, %d) = %d, want %d", a, b, got, want)`
-   **Identify the input**: include inputs directly or use descriptive `t.Run` subtest names
-   **Use `%q`**: for string inputs/outputs to make empty strings and spaces visible
-   **Got before want**: standard `got, want` ordering, or `cmp.Diff(want, got)` with `(-want +got)`
