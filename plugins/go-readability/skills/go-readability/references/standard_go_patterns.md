# Standard Go Patterns

Quick reference for standard, modern Go patterns frequently reviewed in production codebases.

## Modules and Imports

Standard Go uses `go.mod` for dependency management and module-relative import paths.

```go
import (
    "context"
    "fmt"
    "log/slog"
    "os"

    "github.com/google/go-cmp/cmp"
    "google.golang.org/protobuf/proto"

    userpb "github.com/example/project/proto/user"
)
```

Import groups are handled canonically by `goimports`:

1.  Standard library packages
2.  Third-party external packages
3.  Local / module packages

### Avoid Unnecessary Aliases

An import **MUST NOT** be aliased when the alias is identical to the package name. An import **SHOULD NOT** be aliased when usage with the bare package name already reads clearly at the call site.

```go
// ✗ BEFORE - alias is identical to the package name; redundant
import (
    cliutil "github.com/example/project/pkg/cliutil"
)
cliutil.PrintTable(...)

// ✓ AFTER - package name is already cliutil; no alias needed
import (
    "github.com/example/project/pkg/cliutil"
)
cliutil.PrintTable(...)
```

**Why**: Redundant aliases reduce readability. Reserve aliasing for protobuf packages (which often end in `pb` or collide with local package names) and genuine name conflicts between packages.

## Structured Logging (`log/slog`)

Use standard `log/slog` (Go 1.21+) for structured, leveled logging:

```go
import "log/slog"

slog.Info("processing items", "count", count)
slog.Warn("retrying after error", "error", err)
slog.Error("failed to connect", "error", err)

// Context-aware logging
slog.InfoContext(ctx, "handling request", "user_id", userID)

// Sub-logger with pre-attached fields
logger := slog.With("component", "worker", "job_id", jobID)
logger.Info("starting job")
```

For CLI fatal errors, log the error clearly and exit with `os.Exit(1)`:

```go
if err := run(); err != nil {
    slog.Error("fatal error", "error", err)
    os.Exit(1)
}
```

## Command-Line Flags

For standard utilities, use the standard `flag` package or `github.com/spf13/pflag`:

```go
import "flag"

var (
    port    = flag.Int("port", 8080, "Server listen port")
    verbose = flag.Bool("verbose", false, "Enable verbose logging")
)

func main() {
    flag.Parse()
    // ...
}
```

For CLI applications with subcommands, use `github.com/spf13/cobra` (see `references/cobra_cli_patterns.md`).

## Protobufs

### Import & Construction

Standard Protobuf uses `google.golang.org/protobuf/proto`:

```go
import (
    "google.golang.org/protobuf/proto"
    userpb "github.com/example/project/proto/user"
)

// Construction
req := &userpb.CreateUserRequest{
    Name:  "alice",
    Email: "alice@example.com",
}
```

### Comparison

Use `proto.Equal` for runtime equality, not `==` or `reflect.DeepEqual`:

```go
if proto.Equal(got, want) { ... }
```

In tests, use `protocmp.Transform()` with `cmp.Diff`:

```go
import (
    "github.com/google/go-cmp/cmp"
    "google.golang.org/protobuf/testing/protocmp"
)

if diff := cmp.Diff(want, got, protocmp.Transform()); diff != "" {
    t.Errorf("unexpected diff (-want +got):\n%s", diff)
}
```

## Testing with `cmp.Diff`

Prefer `cmp.Diff` over manual field-by-field comparison for structs, slices, and maps:

```go
import "github.com/google/go-cmp/cmp"

if diff := cmp.Diff(want, got); diff != "" {
    t.Errorf("User() returned unexpected diff (-want +got):\n%s", diff)
}
```

## gRPC Patterns

Use `google.golang.org/grpc/status` and `google.golang.org/grpc/codes` for gRPC service implementations:

```go
import (
    "context"
    "errors"

    "google.golang.org/grpc/codes"
    "google.golang.org/grpc/status"
)

func (s *Server) GetUser(ctx context.Context, req *userpb.GetUserRequest) (*userpb.User, error) {
    if req.GetUserId() == "" {
        return nil, status.Errorf(codes.InvalidArgument, "user_id is required")
    }
    user, err := s.store.Get(ctx, req.GetUserId())
    if err != nil {
        if errors.Is(err, ErrNotFound) {
            return nil, status.Errorf(codes.NotFound, "user %q not found", req.GetUserId())
        }
        return nil, status.Errorf(codes.Internal, "fetching user: %v", err)
    }
    return user, nil
}
```

## Context Usage

### Always First Parameter

```go
// ✗ Context not first
func FetchData(id string, ctx context.Context) (*Data, error) { ... }

// ✓ Context is first
func FetchData(ctx context.Context, id string) (*Data, error) { ... }
```

### Never Store in Structs

```go
// ✗ Context stored in struct
type Service struct {
    ctx context.Context
}

// ✓ Pass through method params
type Service struct{}
func (s *Service) Process(ctx context.Context) error { ... }
```

### Cancellation

Always respect context cancellation in loops or long operations:

```go
func ProcessItems(ctx context.Context, items []Item) error {
    for _, item := range items {
        select {
        case <-ctx.Done():
            return ctx.Err()
        default:
        }
        if err := process(ctx, item); err != nil {
            return err
        }
    }
    return nil
}
```

## Key References

-   [Google Go Style Guide](https://google.github.io/styleguide/go/guide)
-   [Google Go Best Practices](https://google.github.io/styleguide/go/best-practices)
-   [Effective Go](https://go.dev/doc/effective_go)
-   [Go Code Review Comments](https://go.dev/wiki/CodeReviewComments)
