# Cobra CLI Patterns

Patterns for Go CLIs built with [Cobra](https://github.com/spf13/cobra), derived from code review feedback across production applications. Terms follow RFC 2119: **MUST**, **MUST NOT**, **SHOULD**, **MAY**.

--------------------------------------------------------------------------------

## 1. Package Doc

The package doc of a `package main` CLI **MUST** describe end-user functionality and common usage. Internal file layout (which files do what) **MUST NOT** appear in the package doc — it **MUST** go in per-file comments instead.

Per-file comments **MUST** be separated from `package main` by a blank line, or they will be misclassified as package doc by `godoc`.

```go
// ✗ BEFORE - describes internal layout, not user behavior
// The mytool command is a CLI for managing cluster resources.
//
// Structure:
//   - clients.go: Client setup and API constants ...
//   - metadata.go: Metadata fetching helpers ...
package main
```

```go
// ✓ AFTER - concise user-facing description
// A CLI tool for managing cloud and cluster resources.
package main
```

```go
// ✓ Per-file comment in an individual file (blank line before package
// prevents this from being classified as the package doc)

// clients.go sets up the HTTP/gRPC client connections used by all subcommands.

package lib
```

**Why**: Cobra's `--help` flag surfaces usage, flags, and subcommands automatically. Internal file layout in the package doc adds maintenance burden and is not visible to end users.

--------------------------------------------------------------------------------

## 2. Naming: Reserve `ctx` for `context.Context`

Parameters that are not `context.Context` **MUST NOT** be named `ctx`. Use a descriptive name instead (e.g. `cliCtx` or `app` for an application context struct).

```go
// ✗ BEFORE - `ctx` collides with context.Context inside the closure
func diffCmd(ctx *cliContext) *cobra.Command {
    ...
    RunE: func(cmd *cobra.Command, args []string) error {
        return withTimeout(cmd, func(c context.Context) error {
            return lib.RunDiff(c, ctx.client, os.Stdout)
        })
    },
    ...
}
```

```go
// ✓ AFTER - cliCtx is unambiguous; ctx inside RunE is context.Context
func diffCmd(cliCtx *cliContext) *cobra.Command {
    ...
    RunE: func(cmd *cobra.Command, args []string) error {
        ctx, cancel := context.WithTimeout(cmd.Context(), defaultTimeout)
        defer cancel()
        return lib.RunDiff(ctx, cliCtx.client, os.Stdout)
    },
    ...
}
```

**Why**: In Go, `ctx` conventionally refers to `context.Context`. Reusing it for other types creates ambiguity in closures where both are in scope.

--------------------------------------------------------------------------------

## 3. Timeout Handling in `RunE`

`context.WithTimeout` **MUST** be inlined directly inside `RunE`. Abstracting it behind a helper function **MUST NOT** be done.

```go
// ✗ BEFORE - timeout lifecycle hidden behind a wrapper helper
func statusCmd(cliCtx *cliContext) *cobra.Command {
    ...
    RunE: func(cmd *cobra.Command, args []string) error {
        return withTimeout(cmd, func(c context.Context) error {
            return lib.RunStatus(c, cliCtx.client, os.Stdout)
        })
    },
    ...
}
```

```go
// ✓ AFTER - timeout and cancellation explicit at the call site
func statusCmd(cliCtx *cliContext) *cobra.Command {
    ...
    RunE: func(cmd *cobra.Command, args []string) error {
        ctx, cancel := context.WithTimeout(cmd.Context(), defaultTimeout)
        defer cancel()
        return lib.RunStatus(ctx, cliCtx.client, os.Stdout)
    },
    ...
}
```

**Why**: Inline usage keeps the context lifetime explicit. Abstracting it behind helpers hides standard plumbing that is expected at the call site.

--------------------------------------------------------------------------------

## 4. Subcommand Help Text

A parent command's `Long` field **MUST NOT** manually list subcommands. Cobra generates that listing automatically in `--help` output.

```go
// ✗ BEFORE - manual list becomes stale when subcommands change
cmd := &cobra.Command{
    Use:  "comments",
    Long: `Manage review comments.

Subcommands:
  list     Show published comments
  post     Post a new draft comment
  reply    Post a draft reply
  publish  Publish all pending drafts`,
}
cmd.AddCommand(commentsListCmd(cliCtx))
```

```go
// ✓ AFTER - Short only; Cobra renders subcommands automatically
cmd := &cobra.Command{
    Use:   "comments",
    Short: "List, post, reply to, edit, delete, or publish comments",
}
cmd.AddCommand(commentsListCmd(cliCtx))
```

**Why**: Avoids duplication; Cobra's `--help` flag already surfaces subcommands automatically.

--------------------------------------------------------------------------------

## 5. Testing `package main`

A `main_test.go` **SHOULD** exist for Cobra CLIs. Tests **SHOULD** cover required-flag enforcement and flag interaction logic — things that break silently during refactors and cannot be caught by library tests.

```go
// Three things worth testing in package main:

// 1 (MAY) - Subcommand registration: useful for large trees
cmd, _, _ := root.Find([]string{"comments", "post"})
if cmd == nil {
    t.Error("subcommand 'comments post' not registered")
}

// 2 (SHOULD) - Required-flag enforcement: MarkFlagRequired is easy to forget;
//              ValidateRequiredFlags catches it without making any network calls.
cmd, _, _ := root.Find([]string{"diff"})
cmd.ParseFlags([]string{}) // missing required --id
if err := cmd.ValidateRequiredFlags(); err == nil {
    t.Error("diff should reject missing --id")
}

// 3 (SHOULD) - Flag interaction logic: mutually dependent or conflicting
//              flags validated inside RunE can be tested without a real backend.
cmd.ParseFlags([]string{"--id=123", "--timeout=60"}) // --trigger absent
if err := cmd.RunE(cmd, nil); !strings.Contains(err.Error(), "--timeout requires --trigger") {
    t.Errorf("unexpected error: %v", err)
}
```

**Why**: Required-flag registration and flag interaction guards live in `package main` and are not exercised by library tests. Both are cheap to validate with `ValidateRequiredFlags()` and `RunE` — no mocks or network calls needed.
