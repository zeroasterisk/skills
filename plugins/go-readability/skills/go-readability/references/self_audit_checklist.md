# Self-Audit Checklist for Go Code

Mechanical recursive greps (also bundled in `scripts/audit-go-readability.sh`) to catch the most common Go style violations BEFORE submitting code for review. Run from the repository root or the modified package directory. False positives are expected — these are starting points for inspection, not auto-rejection.

For each match: review against the corresponding section in `SKILL.md` and the linked [Google Go Style Decisions](https://google.github.io/styleguide/go/decisions).

## Automated Runner

Run all checks recursively across a repository in one pass:

```bash
./scripts/audit-go-readability.sh /path/to/go-repo
```

## Strings & format verbs

```bash
# 1. Manually-quoted format verbs (should be %q, not '%s' / \"%s\")
#    See decisions#use-percent-q
grep -rnE --include='*.go' "('%[svqd]'|\\\\\"%[svqd]\\\\\")" .
```

## Errors

```bash
# 2. Capitalized error strings (allowed only when starting with an exported
#    Go identifier, proper noun, or acronym -- inspect each match).
#    See decisions#error-strings
grep -rnE --include='*.go' 'fmt\.Errorf\("[A-Z]' .
grep -rnE --include='*.go' 'errors\.New\("[A-Z]' .

# 3. Error strings ending in punctuation
#    See decisions#error-strings
grep -rnE --include='*.go' 'fmt\.Errorf\(".*[.!?]"' .
```

## Test failure messages

```bash
# 4. Test failures missing the function-under-test name
#    See decisions#identify-the-function
grep -rnE --include='*_test.go' 't\.(Error|Fatal)f?\("(got|expected) ' .

# 5. Test failures with empty parens (missing inputs)
#    See decisions#identify-the-input
grep -rnE --include='*_test.go' 't\.(Error|Fatal)f?\("[A-Za-z_]+\(\)' .
```

## Naming

```bash
# 6. Get-prefixed functions or methods (review each: plain accessor -> drop prefix;
#    directory/state ensure -> use Ensure; remote call -> use Fetch; CPU-heavy -> use Compute).
#    See decisions#getters
grep -rnE --include='*.go' 'func (\([^)]+\) )?Get[A-Z]' .

# 7. Receiver names longer than 2 letters (style: 1-2 letters,
#    abbreviation of the type, applied consistently).
#    See decisions#receiver-names
grep -rnE --include='*.go' 'func \([a-zA-Z]{3,} \*?[A-Z]' .
```

## Control flow

```bash
# 8. else { return } anti-pattern (line-of-sight violation).
#    See decisions#indent-error-flow
grep -rnE --include='*.go' '\} else \{$' .

# 9. Bare break inside switch (redundant in Go).
#    See decisions#switch-break
grep -rnB2 --include='*.go' -E '^\s+break$' . | grep -B1 -A1 case
```

## Language & Security

```bash
# 10. interface{} (use any instead, Go 1.18+).
#     See decisions#use-any
grep -rnE --include='*.go' '\binterface\{\}' .

# 11. context.Background() outside of main / init / TestXXX.
#     See decisions#contexts
grep -rnE --include='*.go' 'context\.Background\(\)' . | grep -vE '_test\.go|main\.go|init\.go'

# 12. Empty slice declaration as []T{} (prefer `var s []T`).
#     See decisions#nil-slices
grep -rnE --include='*.go' ':= \[\][a-zA-Z*]+\{\}' .

# 13. Overly permissive world-writable file modes (prefer 0644 or 0600).
grep -rnE --include='*.go' '\b0(666|0777|777)\b' .
```

## Pre-Review Workflow

After inspecting with greps, run standard Go formatting, linting, and tests:

```bash
gofmt -s -w .       # standard formatting
go vet ./...        # static analysis checks
golangci-lint run   # comprehensive linter pass
go test -race ./... # test suite with race detector
```
