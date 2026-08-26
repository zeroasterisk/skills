# Elixir Best Practices

Elixir coding standards and best practices for AI coding agents. Enforces idiomatic patterns, proper error handling, and Phoenix conventions.

## What It Does

Provides a comprehensive set of Elixir coding rules that agents follow when writing, reviewing, or refactoring Elixir code. Covers:

- **Pattern matching** — Multi-clause functions and guards over `if/else`
- **Error handling** — `{:ok, value}` / `{:error, reason}` tuples, `with` for happy paths
- **Pipe operator** — Idiomatic data transformation chains
- **Documentation** — Doctests on every public function
- **Types** — Structs with `@enforce_keys` and `@type t()`
- **Process design** — GenServer, Supervisors, Registry
- **Phoenix/LiveView** — Thin controllers, context modules, Ecto.Multi
- **Testing** — Doctests, ExUnit, Mox, async by default

## When to Use

- Writing new Elixir modules or functions
- Reviewing Elixir pull requests
- Refactoring existing Elixir code
- Working on Phoenix/LiveView applications

## Installation

### Universal (npx skills)

```bash
npx skills add zeroasterisk/elixir-best-practices
```

### Gemini CLI Extension

```bash
gemini extensions install https://github.com/zeroasterisk/elixir-best-practices
```

### Manual

Copy the `elixir-best-practices/` folder into your agent's skills directory.

## Compatibility

| Platform | Install Method | Status |
|----------|---------------|--------|
| Claude Code | `npx skills add` | Supported |
| Cursor | `npx skills add` | Supported |
| Codex | `npx skills add` | Supported |
| Gemini CLI | `gemini extensions install` | Supported |
| OpenClaw | Copy to skills dir | Supported |

## License

Apache 2.0
