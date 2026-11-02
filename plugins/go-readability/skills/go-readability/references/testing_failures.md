# Useful Test Failures (Go)

Authoritative deep-dive on the 9 sub-decisions of [Google Go Style Decisions: Useful Test Failures](https://google.github.io/styleguide/go/decisions#useful-test-failures).
A test that fails should be diagnosable WITHOUT reading the test source.

## The canonical failure-message format

Every `t.Errorf` / `t.Fatalf` call on a single mismatch should produce a message in this shape:

```text
YourFunc(<inputs>) = <got>, want <want>
```

Concrete examples:

```go
t.Errorf("Add(%d, %d) = %d, want %d", a, b, got, want)
t.Errorf("Translate(%q, %q, %q) = %q, want %q", srcLang, dstLang, srcText, got, want)
t.Errorf("Foo(%v) returned unexpected diff (-want +got):\n%s", input, diff)
```

A reader seeing the failure in CI logs, with no access to the test source, should know exactly what was tried and what was wrong.

## The 9 sub-decisions

### 1. [Identify the function](https://google.github.io/styleguide/go/decisions#identify-the-function)

Even if the surrounding test function name (e.g. `TestAdd`) makes the function-under-test obvious, the FAILURE MESSAGE must name it explicitly. A single-line failure in a CI summary often shows just the message text; the test name may be truncated.

```go
// ✗ Bad
t.Errorf("got %d, want %d", got, want)

// ✓ Good
t.Errorf("Add(%d, %d) = %d, want %d", a, b, got, want)
```

### 2. [Identify the input](https://google.github.io/styleguide/go/decisions#identify-the-input)

If the inputs are short, INCLUDE THEM. If inputs are large or opaque, give the test case a descriptive `name:` and use it as the `t.Run` subtest name. Because the subtest name already prefixes the failure output, if you are using `t.Run` you do not need to include the `name` or `desc` again inside the failure message itself.

```go
// ✗ Bad: missing both function name and inputs
t.Errorf("got %q, want %q", got, want)

// ✗ Bad: function name present but inputs missing
t.Errorf("calculateRate() = %q, want %q", got, want)

// ✓ Good: short inputs included directly, in the canonical form.
t.Errorf("calculateRate(%+v, %v) = %q, want %q",
    cfg, rateNames, got, want)

// ✓ Good: large inputs tested using a descriptive subtest name
t.Errorf("Translate(%q, %q, %q) = %q, want %q",
    tc.srcLang, tc.dstLang, tc.srcText, got, tc.wantDstText)
```

### 3. [Got before want](https://google.github.io/styleguide/go/decisions#got-before-want)

Print the ACTUAL value first, then the EXPECTED value. Use the words `got` and `want` (not `actual` / `expected`). The order convention is load-bearing: many `cmp.Diff` invocations rely on it for the `(-want +got)` legend.

```go
// ✓ Standard
t.Errorf("Foo(%v) = %v, want %v", input, got, want)

// ✓ Diff form: call cmp.Diff(want, got) to match the (-want +got) legend
if diff := cmp.Diff(want, got); diff != "" {
    t.Errorf("Foo(%v) returned unexpected diff (-want +got):\n%s", input, diff)
}

// ✗ Bad: no legend, ambiguous direction
if diff := cmp.Diff(got, want); diff != "" {
    t.Errorf("diff: %s", diff)
}
```

### 4. [Compare full structures](https://google.github.io/styleguide/go/decisions#compare-full-structures)

When comparing structs, slices, or maps: use `cmp.Diff` (from `"github.com/google/go-cmp/cmp"`) on the WHOLE structure rather than checking field-by-field. Field-by-field comparisons miss new fields when the type evolves and produce N test failures for one underlying mismatch.

```go
// ✗ Bad: field-by-field
if got.Name != want.Name {
    t.Errorf("...")
}
if got.Age != want.Age {
    t.Errorf("...")
}

// ✓ Good: whole-struct diff
if diff := cmp.Diff(want, got); diff != "" {
    t.Errorf("GetUser() returned unexpected diff (-want +got):\n%s", diff)
}

// ✓ Good: protobufs need protocmp.Transform()
if diff := cmp.Diff(want, got, protocmp.Transform()); diff != "" {
    t.Errorf("GetUserProto() returned unexpected diff (-want +got):\n%s", diff)
}
```

### 5. [Compare stable results](https://google.github.io/styleguide/go/decisions#compare-stable-results)

Don't compare against the byte-output of `json.Marshal`, `proto.Marshal`, or any other formatter you don't own. Parse the output and compare the semantic structure instead.

```go
// ✗ Bad: fragile to JSON formatting changes
if got := string(jsonBytes); got != `{"name":"alice"}` {
    t.Errorf("...")
}

// ✓ Good: compare the parsed structure
var got User
if err := json.Unmarshal(jsonBytes, &got); err != nil {
    t.Fatalf("json.Unmarshal failed: %v", err)
}
if diff := cmp.Diff(want, got); diff != "" {
    t.Errorf("json.Unmarshal returned unexpected diff (-want +got):\n%s", diff)
}
```

### 6. [Keep going](https://google.github.io/styleguide/go/decisions#keep-going)

Prefer `t.Error` (continue running checks after a mismatch) over `t.Fatal` (stop the test). The maintainer fixing a regression wants to see ALL the failures from one run, not have to fix-and-rerun N times.

Use `t.Fatal` only when subsequent checks would be MEANINGLESS or PANIC:

```go
// ✓ Good: t.Fatal because subsequent checks deref a pointer that would be nil on error
got, err := FetchUser(id)
if err != nil {
    t.Fatalf("FetchUser(%q) returned unexpected error: %v", id, err)
}
if got.Name != wantName {
    t.Errorf("FetchUser(%q).Name = %q, want %q", id, got.Name, wantName)
}

// ✓ Good: t.Error for independent checks
gotMean, gotVariance, err := Distribution(input)
if err != nil {
    t.Fatalf("Distribution(%v) returned unexpected error: %v", input, err)
}
if gotMean != wantMean {
    t.Errorf("Distribution(%v) mean = %v, want %v", input, gotMean, wantMean)
}
if gotVariance != wantVariance {
    t.Errorf("Distribution(%v) variance = %v, want %v", input, gotVariance, wantVariance)
}
```

### 7. [Equality comparison and diffs](https://google.github.io/styleguide/go/decisions#types-of-equality)

-   `==` works for scalars, strings, and comparable structs (no slices/maps inside).
-   Use `cmp.Equal` / `cmp.Diff` for slices, maps, and non-comparable structs.
-   For protobufs, ALWAYS pass `protocmp.Transform()`.
-   Avoid `reflect.DeepEqual` in new code — it's sensitive to unexported field changes in dependencies.

### 8. [Level of detail](https://google.github.io/styleguide/go/decisions#level-of-detail)

The conventional `YourFunc(%v) = %v, want %v` format is the default. Adjust as needed:

-   When test inputs/outputs are STRINGS, use `%q` so empty strings show as `""` and control characters are escaped.
-   When values are structs, `%+v` (with field names) is often more debuggable than `%v`.
-   When values are large, print a `cmp.Diff` instead of full values.

### 9. [Print diffs](https://google.github.io/styleguide/go/decisions#print-diffs)

For large outputs, print a diff instead of both values:

```go
if diff := cmp.Diff(want, got); diff != "" {
    t.Errorf("Foo(%v) returned unexpected diff (-want +got):\n%s", input, diff)
}
```

ALWAYS include the direction legend (`(-want +got)` for `cmp.Diff(want, got)`). Put a `\n` between the message and the diff.

## Subtest names

Per [decisions#subtest-names](https://google.github.io/styleguide/go/decisions#subtest-names):
think of subtest names as function identifiers, not prose.

-   **AVOID slashes** — `t.Run("AM/PM", ...)` is unfriendly to test filter flags (`-run`) because slashes have special meaning in regexes/subtest hierarchies.
-   Do not redundantly print the subtest name inside the `t.Errorf` failure string.

## Don't identify the row by index

Per [decisions#table-tests-identifying-the-row](https://google.github.io/styleguide/go/decisions#table-tests-identifying-the-row):
always name your test cases in table-driven tests.

```go
// ✗ Bad
for i, d := range tests {
    if got := strings.ToUpper(d.input); got != d.want {
        t.Errorf("Failed on case #%d", i)
    }
}

// ✓ Good: subtest with name
for _, d := range tests {
    t.Run(d.name, func(t *testing.T) {
        if got := strings.ToUpper(d.input); got != d.want {
            t.Errorf("ToUpper(%q) = %q, want %q", d.input, got, d.want)
        }
    })
}
```

## Test error semantics, not message text

Per [decisions#test-error-semantics](https://google.github.io/styleguide/go/decisions#test-error-semantics):
don't use `strings.Contains(err.Error(), "...")` to test error conditions unless the string is an explicit public API guarantee. Use `errors.Is` or `errors.As` instead.

```go
// ✗ Bad: fragile change-detector
if !strings.Contains(err.Error(), "not found") {
    t.Errorf("got %v, want ErrNotFound", err)
}

// ✓ Good: semantic check
if !errors.Is(err, ErrNotFound) {
    t.Errorf("got error %v, want %v", err, ErrNotFound)
}
```
