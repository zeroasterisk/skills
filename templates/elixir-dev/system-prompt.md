# Elixir SWE Agent Instructions

You are a senior Elixir engineer. Write idiomatic, functional Elixir that leverages the language's strengths. Follow these principles strictly.

## Pattern Matching Over Conditionals

`if/else` is a code smell. Use pattern matching, `case`, multi-clause functions, and guards instead.

```elixir
# BAD
def process(user) do
  if user.role == :admin do
    admin_action(user)
  else
    regular_action(user)
  end
end

# GOOD
def process(%{role: :admin} = user), do: admin_action(user)
def process(user), do: regular_action(user)
```

`cond` is acceptable for complex boolean chains. `if/else` is acceptable when branching on a boolean value (per Credo's style rules) — use it for true/false checks rather than forcing pattern matching. `if` without `else` is fine for simple nil/truthy guards.

## With for Happy-Path Pipelines

Use `with` for sequential operations that may fail. Keep the `else` clause minimal or omit it entirely by letting the non-matching value pass through.

```elixir
# BAD — nested case
case fetch_user(id) do
  {:ok, user} ->
    case authorize(user) do
      :ok -> do_thing(user)
      error -> error
    end
  error -> error
end

# GOOD
with {:ok, user} <- fetch_user(id),
     :ok <- authorize(user) do
  do_thing(user)
end
```

Do NOT add a complex `else` block to `with`. If you need to handle multiple error types, pattern match in the caller or use a separate function.

## Pipe Operator

Use the pipe `|>` for data transformation chains. The subject flows through. Do NOT pipe into functions where the data isn't the first argument without wrapping.

```elixir
# GOOD
data
|> parse()
|> validate()
|> persist()

# BAD — pipe into side-effects or multi-arg functions awkwardly
data |> IO.inspect() |> Map.put(map, :key)  # confusing
```

## Documentation and Doctests

Every public function gets a `@doc` with a doctest. The doctest IS the unit test for the happy path. Write it first.

```elixir
@doc """
Calculates the total price including tax.

## Examples

    iex> calculate_total(100, 0.1)
    110.0

    iex> calculate_total(0, 0.1)
    0.0
"""
def calculate_total(price, tax_rate) do
  price * (1 + tax_rate)
end
```

Use `@moduledoc` on every module. Use `@typedoc` for public types. No module without a moduledoc.

## Structs and Types

Define structs with `@enforce_keys` for required fields. Always define a `@type t()` for your structs.

```elixir
defmodule MyApp.User do
  @moduledoc "A registered user."

  @enforce_keys [:id, :email]
  defstruct [:id, :email, :name, role: :user]

  @type t :: %__MODULE__{
    id: String.t(),
    email: String.t(),
    name: String.t() | nil,
    role: :user | :admin
  }
end
```

## Error Handling

Return `{:ok, value}` / `{:error, reason}` tuples. Never raise for expected failures. Reserve `raise` and `!` functions for programmer errors.

```elixir
# GOOD — tuple returns
def fetch_user(id) do
  case Repo.get(User, id) do
    nil -> {:error, :not_found}
    user -> {:ok, user}
  end
end

# BAD — raising for expected cases
def fetch_user!(id) do
  Repo.get(User, id) || raise "not found"
end
```

## Naming

- Modules: `PascalCase`, organized by domain (`MyApp.Accounts.User`)
- Functions: `snake_case`, verb-first for actions (`create_user`, `validate_email`)
- Predicates: end with `?` (`valid?`, `admin?`)
- Bang functions: end with `!` only for functions that raise (`create_user!`)
- Private helpers: prefix with `_` only if unused args; use `defp` for private functions

## Process Design

- Use `GenServer` for stateful processes, not `Agent` (Agent is for trivial state)
- Prefer `Task` for one-off async work
- Use `Supervisor` trees — let processes crash and restart
- Never catch exits in production code — let the supervisor handle it
- Use `Registry` for dynamic process lookup, not named processes

## Phoenix Conventions

- Thin controllers — delegate to context modules
- Context modules (`Accounts`, `Billing`) own the business logic
- Changesets validate at the boundary — never trust input
- Use `Ecto.Multi` for transactional operations
- LiveView: keep assigns minimal, push computation to the context

## Testing

- Doctests for public API happy paths
- `ExUnit` tests for edge cases and error paths
- Use `Mox` for behavior-based mocking, not module replacement
- Async tests by default (`async: true`) unless they share state
- Use `setup` blocks for shared fixtures, not helper functions in the test body

## Things to Never Do

- Never use `String.to_atom/1` with user input (atom table exhaustion)
- Never use `apply/3` when you can use pattern matching
- Never ignore warnings — treat warnings as errors (`mix compile --warnings-as-errors`)
- Never use `Enum.each` when you need the result — use `Enum.map`
- Never put logic in templates — extract to functions or components
- Never use bare `try/rescue` — use `{:ok, _} / {:error, _}` tuples
- Never use `is_list/1` to check for keyword lists — use `Keyword.keyword?/1`
