# Go Readability Skill - Agent E2E Test Plan

## Prerequisites

Read `SKILL.md` first to understand the style rules, patterns, and gotchas covered by this skill.

This is a doc-only skill (no CLI binary). Tests validate that an agent applies standard Go readability patterns correctly when writing or reviewing code.

--------------------------------------------------------------------------------

## Test 1: Naming conventions

**Prompt:** "I have a Go function `GetUser()` as a method on a `UserStore` struct. Is this naming correct for idiomatic Go style?"

**Verify:**
- Advises removing the `Get` prefix — should be `User()` or `ByID()`
- Explains that getters don't use `Get` prefix in Go
- May reference Google Go Style Decisions: getters

--------------------------------------------------------------------------------

## Test 2: Error handling

**Prompt:** "I'm writing Go code and sometimes I don't need the error return value. Is it OK to just ignore it with `_`?"

**Verify:**
- Flags the ignored error (`_`)
- Recommends explicit error handling with `if err != nil`
- Mentions adding context via `fmt.Errorf` with `%w`

--------------------------------------------------------------------------------

## Test 3: Package naming

**Prompt:** "I want to name my Go package `user_utils`. Is this valid?"

**Verify:**
- Advises against underscores in package names
- Advises against uninformative names like `utils`
- Recommends a domain-specific, concise name like `user` or `userstore`

--------------------------------------------------------------------------------

## Test 4: Table-driven tests

**Prompt:** "I'm writing Go tests with separate test functions for each case. Is there a better pattern?"

**Verify:**
- Recommends table-driven tests with subtests (`t.Run`)
- Shows the `tests := []struct{ ... }` pattern
- Mentions `t.Helper()` for helper functions

--------------------------------------------------------------------------------

## Test 5: Interface design

**Prompt:** "I defined a Go interface with 8 methods. Is this good practice?"

**Verify:**
- Advises keeping interfaces small (1-2 methods)
- Recommends defining interfaces at the consumer, not the producer
- Mentions `-er` suffix convention for single-method interfaces

--------------------------------------------------------------------------------

## Test 6: Documentation

**Prompt:** "My exported Go function `ProcessData` doesn't have a comment. Is that OK?"

**Verify:**
- Says all exported names must have doc comments
- Comment should start with the function name and be a full sentence
- Shows the `// ProcessData ...` format

--------------------------------------------------------------------------------

## Test 7: Context in tests

**Prompt:** "I'm using context.Background() in my Go tests. Is there a better way?"

**Verify:**
- Recommends `t.Context()` (Go 1.24+)
- Explains automatic cleanup/cancellation benefits preventing goroutine leaks

--------------------------------------------------------------------------------

## Test 8: Use `%q` for quoted strings

**Prompt:** "I have this Go error: `fmt.Errorf("failed to read resource '%s': %w", name, err)`. Anything wrong with it from a Go style perspective?"

**Verify:**
- Identifies the manual single-quotes around `%s` as a violation
- Recommends `%q` instead
- Explains that `%q` escapes control chars and makes empty strings visible
- Shows the corrected form: `fmt.Errorf("failed to read resource %q: %w", name, err)`

--------------------------------------------------------------------------------

## Test 9: Test failure includes inputs

**Prompt:** "I wrote this test failure message: `t.Errorf("calculateRate() = %q, want %q", got, want)`. The test inputs are a `*Config` and a `[]string` of `rateNames`. Is this message OK?"

**Verify:**
- Recommends the canonical `YourFunc(<inputs>) = <got>, want <want>` format
- Explains that test failures should be diagnosable without reading the test source
- Shows a corrected message that includes the inputs

--------------------------------------------------------------------------------

## Test 10: Fetch prefix for remote calls

**Prompt:** "I have a Go function `getResourceMetadata(name, location string) (string, error)` that makes a remote REST API call under the hood. Reviewer flagged the name. What should it be?"

**Verify:**
- Identifies that `Get` prefix should not be used on remote operations
- Recommends `Fetch` prefix because the function performs a remote/network call
- Explains that `Fetch` (or `Compute` for CPU-heavy ops) signals the call may take time, block, or fail
- Shows the corrected name (`fetchResourceMetadata`)

--------------------------------------------------------------------------------

## Test 11: Error string formatting

**Prompt:** "Reviewer flagged `fmt.Errorf("Something bad happened.")`. Why?"

**Verify:**
- Identifies the capitalized first word AND trailing period as violations
- Shows the corrected form: `fmt.Errorf("something bad happened")`
- Mentions the exception: starting with an exported Go identifier, proper noun, or acronym is allowed

--------------------------------------------------------------------------------

## Test 12: Indent error flow

**Prompt:** "I have `if err != nil { return err } else { result := process(x); return result, nil }`. Reviewer says I should restructure. What's the issue?"

**Verify:**
- Identifies the `else`-after-error-return pattern as a line-of-sight violation
- Explains early return keeps the happy path at the left margin
- Shows the corrected form with the happy path at the left margin (no `else` block)
