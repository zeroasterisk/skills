# Elixir Best Practices

You have access to the Elixir Best Practices skill. Use it when writing, reviewing, or refactoring Elixir code.

## When to Use

Apply these rules whenever you:
- Write new Elixir modules or functions
- Review Elixir pull requests
- Refactor existing Elixir code
- Work on Phoenix/LiveView applications

## Core Rules

1. **Pattern matching over conditionals** — Use multi-clause functions, `case`, and guards instead of `if/else`. Exception: `if/else` is fine for boolean checks.
2. **`with` for happy-path pipelines** — Chain fallible operations with `with`, avoid nested `case`. Keep `else` blocks minimal.
3. **Pipe operator for transformations** — Data flows left to right through `|>`. Don't pipe when data isn't the first argument.
4. **Doctests on every public function** — The doctest IS the unit test for the happy path. Write it first.
5. **Structs with `@enforce_keys` and `@type t()`** — Always define required fields and type specs.
6. **`{:ok, value}` / `{:error, reason}` tuples** — Never raise for expected failures. Reserve `!` functions for programmer errors.
7. **Verb-first `snake_case` functions** — `create_user`, `validate_email`. Predicates end with `?`.
8. **GenServer over Agent** — Agent is for trivial state only. Use Supervisor trees, let processes crash.
9. **Phoenix: thin controllers, context modules own logic** — Changesets validate at the boundary. Use `Ecto.Multi` for transactions.
10. **Testing: doctests + ExUnit + Mox** — Async by default (`async: true`). Use `setup` blocks for fixtures.

## Never Do

- `String.to_atom/1` with user input (atom table exhaustion)
- `apply/3` when pattern matching works
- Ignore warnings — use `mix compile --warnings-as-errors`
- `Enum.each` when you need the result — use `Enum.map`
- Logic in templates — extract to functions/components
- Bare `try/rescue` — use `{:ok, _} / {:error, _}` tuples
- `is_list/1` for keyword lists — use `Keyword.keyword?/1`

See `skills/elixir-best-practices/SKILL.md` for detailed documentation with code examples.
