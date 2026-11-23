# Before/After Examples — Go Readability

Common transformations that Go readability reviewers request. Each shows the pattern to avoid and the idiomatic replacement.

--------------------------------------------------------------------------------

## 1. Silent Error → Explicit Handling

```go
// ✗ BEFORE -- error silently discarded
data, _ := LoadConfig(path)

// ✓ AFTER -- error handled with context describing the calling function
data, err := LoadConfig(path)
if err != nil {
    return fmt.Errorf("setting up server: %w", err)
}
```

--------------------------------------------------------------------------------

## 2. Bare Error → Wrapped Error

> **Note:** Wrapping is not always correct. Use `%w` only when callers need to inspect the underlying error with `errors.Is`/`errors.As`. Use `%v` when wrapping would expose implementation details or internal state. See [Go Blog: Working with Errors](https://go.dev/blog/go1.13-errors#whether-to-wrap) for guidance.

```go
// ✗ BEFORE -- no context for debugging
func ProcessUser(id string) error {
    user, err := fetchUser(id)
    if err != nil {
        return err
    }
    return nil
}

// ✓ AFTER -- context added at each level
func ProcessUser(id string) error {
    user, err := fetchUser(id)
    if err != nil {
        return fmt.Errorf("processing user %q: %w", id, err)
    }
    return nil
}
```

--------------------------------------------------------------------------------

## 3. Repetitive Naming → Clean Naming

```go
// ✗ BEFORE -- callers write `config.ConfigManager`
package config

type ConfigManager struct{ ... }
func NewConfigManager() *ConfigManager { ... }

// ✓ AFTER -- callers write `config.Manager`
package config

type Manager struct{ ... }
func NewManager() *Manager { ... }
```

--------------------------------------------------------------------------------

## 4. Get Prefix → Bare Getter

```go
// ✗ BEFORE -- unnecessary Get prefix
func (u *User) GetName() string { return u.name }
func (u *User) GetEmail() string { return u.email }

// ✓ AFTER -- idiomatic Go getters
func (u *User) Name() string { return u.name }
func (u *User) Email() string { return u.email }
```

--------------------------------------------------------------------------------

## 5. reflect.DeepEqual → cmp.Diff

```go
// ✗ BEFORE -- no diff on failure, proto-unsafe
if !reflect.DeepEqual(got, want) {
    t.Errorf("got %v, want %v", got, want)
}

// ✓ AFTER -- clear diff output with github.com/google/go-cmp/cmp
if diff := cmp.Diff(want, got); diff != "" {
    t.Errorf("unexpected diff (-want +got):\n%s", diff)
}

// ✓ For protos -- use protocmp
if diff := cmp.Diff(want, got, protocmp.Transform()); diff != "" {
    t.Errorf("unexpected diff (-want +got):\n%s", diff)
}
```

--------------------------------------------------------------------------------

## 6. Flat Tests → Table-Driven Tests

```go
// ✗ BEFORE -- repetitive, hard to extend
func TestAdd(t *testing.T) {
    if got := Add(1, 2); got != 3 {
        t.Errorf("Add(1, 2) = %d, want 3", got)
    }
    if got := Add(0, 0); got != 0 {
        t.Errorf("Add(0, 0) = %d, want 0", got)
    }
    if got := Add(-1, 1); got != 0 {
        t.Errorf("Add(-1, 1) = %d, want 0", got)
    }
}

// ✓ AFTER -- table-driven with subtests
func TestAdd(t *testing.T) {
    tests := []struct {
        name string
        a    int
        b    int
        sum  int
    }{
        {name: "positive", a: 1, b: 2, sum: 3},
        {name: "zeros", a: 0, b: 0, sum: 0},
        {name: "negative", a: -1, b: 1, sum: 0},
    }
    for _, tc := range tests {
        t.Run(tc.name, func(t *testing.T) {
            if sum := Add(tc.a, tc.b); sum != tc.sum {
                t.Errorf("Add(%v, %v) = %v, want %v", tc.a, tc.b, sum, tc.sum)
            }
        })
    }
}
```

--------------------------------------------------------------------------------

## 7. Large Interface → Consumer-Scoped Interface

```go
// ✗ BEFORE -- function accepts a wide interface
type DataStore interface {
    Read(ctx context.Context, key string) ([]byte, error)
    Write(ctx context.Context, key string, val []byte) error
    Delete(ctx context.Context, key string) error
    List(ctx context.Context, prefix string) ([]string, error)
    Watch(ctx context.Context, key string) (<-chan Event, error)
    Close() error
}

func BackupKeys(ctx context.Context, store DataStore, prefix string) error {
    keys, err := store.List(ctx, prefix)
    // ... only uses List and Read
}

// ✓ AFTER -- function defines just the interface it needs
type KeyReader interface {
    List(ctx context.Context, prefix string) ([]string, error)
    Read(ctx context.Context, key string) ([]byte, error)
}

func BackupKeys(ctx context.Context, store KeyReader, prefix string) error {
    keys, err := store.List(ctx, prefix)
    // ...
}
```

--------------------------------------------------------------------------------

## 8. Nil Map Write → Initialized Map

```go
// ✗ BEFORE -- panics at runtime
func CountWords(words []string) map[string]int {
    var counts map[string]int
    for _, w := range words {
        counts[w]++  // panic: assignment to nil map
    }
    return counts
}

// ✓ AFTER -- properly initialized
func CountWords(words []string) map[string]int {
    counts := make(map[string]int)
    for _, w := range words {
        counts[w]++
    }
    return counts
}
```

--------------------------------------------------------------------------------

## 9a. Standard log → Structured `slog`

```go
// ✗ BEFORE -- unstructured stdlib log
import "log"

log.Printf("Processing %d items for user %s", count, userID)
log.Fatalf("Failed to initialize server: %v", err)

// ✓ AFTER -- structured, leveled slog
import (
    "log/slog"
    "os"
)

slog.Info("processing items", "count", count, "user_id", userID)
if err != nil {
    slog.Error("failed to initialize server", "error", err)
    os.Exit(1)
}
```

--------------------------------------------------------------------------------

## 9b. Global Flags → Scoped Command Flags

```go
// ✗ BEFORE -- global flag pollution across packages
package service

import "flag"

var Port = flag.Int("port", 8080, "server port")

// ✓ AFTER -- explicit config struct passed into service
package service

type Config struct {
    Port int
}

func New(cfg Config) *Server {
    return &Server{port: cfg.Port}
}
```

--------------------------------------------------------------------------------

## 10. Missing `t.Helper()` → Proper Test Helper

```go
// ✗ BEFORE -- failures point to the helper line, not the caller
func mustCreate(t *testing.T, name string) *Widget {
    w, err := CreateWidget(name)
    if err != nil {
        t.Fatalf("CreateWidget(%q) failed: %v", name, err)  // points here
    }
    return w
}

// ✓ AFTER -- failures point to the calling test
func mustCreate(t *testing.T, name string) *Widget {
    t.Helper()
    w, err := CreateWidget(name)
    if err != nil {
        t.Fatalf("CreateWidget(%q) failed: %v", name, err)  // points to caller
    }
    return w
}
```

--------------------------------------------------------------------------------

## 11. Context Stored in Struct → Context as Parameter

```go
// ✗ BEFORE -- context stored, can't be caller-controlled
type Worker struct {
    ctx context.Context
    db  *DB
}

func (w *Worker) Process() error {
    return w.db.Query(w.ctx, "SELECT ...")
}

// ✓ AFTER -- context passed per-call
type Worker struct {
    db *DB
}

func (w *Worker) Process(ctx context.Context) error {
    return w.db.Query(ctx, "SELECT ...")
}
```

--------------------------------------------------------------------------------

## 12. Missing Doc Comments → Proper Documentation

```go
// ✗ BEFORE -- no documentation
type UserService struct { ... }
func (s *UserService) Create(ctx context.Context, u *User) error { ... }

// ✓ AFTER -- exported names documented with full sentences
// UserService manages user lifecycle operations including creation,
// validation, and deletion.
type UserService struct { ... }

// Create validates and persists a new user. Returns an error if a user
// with the same email already exists.
func (s *UserService) Create(ctx context.Context, u *User) error { ... }
```

--------------------------------------------------------------------------------

## 13. Manual Quotes Around `%s` → `%q`

```go
// ✗ BEFORE -- manual quotes; empty strings invisible, control chars unescaped
return fmt.Errorf("failed to read resource '%s': %w", name, err)
fmt.Errorf("value \"%s\" looks like text", text)

// ✓ AFTER -- %q
return fmt.Errorf("failed to read resource %q: %w", name, err)
fmt.Errorf("value %q looks like text", text)
```

--------------------------------------------------------------------------------

## 14. Test Failure Without Inputs → Identifies Function and Inputs

```go
// ✗ BEFORE -- no function name, no inputs
t.Errorf("got %q, want %q", got, want)

// ✗ BEFORE -- function name but no inputs
t.Errorf("calculateRate() = %q, want %q", got, tc.want)

// ✓ AFTER -- function + inputs + got + want, in canonical form.
t.Errorf("calculateRate(%+v, %v) = %q, want %q",
    tc.cfg, tc.rates, got, tc.want)

t.Errorf("groupItemsByCategory(%q, %v, %+v) succeeded, want error",
    tc.env, tc.categories, tc.items)
```

--------------------------------------------------------------------------------

## 15. `else` After Error Return → Indent Error Flow (Line of Sight)

```go
// ✗ BEFORE -- happy path indented inside else
func process(input string) error {
    parsed, err := parse(input)
    if err != nil {
        return fmt.Errorf("parse: %w", err)
    } else {
        result, err := compute(parsed)
        if err != nil {
            return fmt.Errorf("compute: %w", err)
        } else {
            return store(result)
        }
    }
}

// ✓ AFTER -- happy path stays at the left margin
func process(input string) error {
    parsed, err := parse(input)
    if err != nil {
        return fmt.Errorf("parse: %w", err)
    }
    result, err := compute(parsed)
    if err != nil {
        return fmt.Errorf("compute: %w", err)
    }
    return store(result)
}
```

--------------------------------------------------------------------------------

## 16. `Get`-Prefixed Remote Call → `Fetch` Prefix

```go
// ✗ BEFORE -- Get prefix on a method that makes a network / API call
func getResourceMetadata(name, region string) (string, error) {
    out, err := client.FetchResource(ctx, name, region)
    // ...
}

// ✓ AFTER -- Fetch prefix signals "remote call may take time / fail"
func fetchResourceMetadata(name, region string) (string, error) {
    out, err := client.FetchResource(ctx, name, region)
    // ...
}

// For plain in-memory accessors, drop the prefix entirely:
// ✗ BEFORE
func (u *User) GetName() string { return u.name }

// ✓ AFTER
func (u *User) Name() string { return u.name }
```
