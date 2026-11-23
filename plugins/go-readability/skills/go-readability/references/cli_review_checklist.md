# Go CLI Review Checklist

Comprehensive Go CLI review checklist derived from code review feedback across production Go CLIs (~45 patterns catalogued across 12 categories).

## 1. Duplicate Code → Extract Helpers

Look for repeated code blocks and extract them into helper functions.

| Pattern | Fix |
| :--- | :--- |
| Repeated header extraction loops (`for _, h := range headers { if h.Name == ... }`) | Extract `func getHeader(headers []Header, name string) string` |
| Repeated client calls with identical error handling | Extract `func modifyResource(svc *Client, id string, req *Request) error` |
| Repeated text parsing / extraction | Extract `func extractText(elem *StructuralElement) string` |
| Color / format conversions repeated | Extract `func hexToRGB(hex string) (*RGBColor, error)` |
| Pipe-separated or CSV row parsing duplicated | Extract `func parsePipeSeparatedRows(args []string) ([][]any, error)` — name describes format |
| Data extraction duplicated across multiple subcommands | Extract `func extractBasicInfo(item *Item) (name, email, phone string)` |
| JSON output marshalling repeated in every command | Use shared helper: `cliutil.PrintJSON(out, data)` |
| Table output with manual `fmt.Printf` formatting | Use shared table printer: `cliutil.PrintTable(out, headers, rows)` |
| Auth/context setup boilerplate identical across commands | Extract `func setupRequest(cmd *cobra.Command) (context.Context, context.CancelFunc, error)` |

## 2. Function Naming

Names should accurately describe what the function does.

| Pattern | Fix |
| :--- | :--- |
| Function name mentions `Raw` but returns base64 or encoded data | Rename to `encodePayload` or `buildBase64Payload` |
| Getter calls an expensive/remote method twice | Use `if v := item.DisplayName(); v != "" { return v }` |
| Remote call named with `Get` prefix | Rename with `Fetch` prefix (`fetchRemoteConfig`) |

## 3. Command Design → One-Command-Per-Action

Multi-mode commands with conflicting flags should be split into separate subcommands.

| Pattern | Fix |
| :--- | :--- |
| `service` command with `--enable` and `--disable` flags | Split into `get-service`, `enable-service`, `disable-service` |
| `rules` command with `--create` and `--delete` flags | Split into `list-rules`, `create-rule`, `delete-rule` |

**Why**: Separate commands are easier to discover via `--help`, have focused flag sets, and eliminate invalid flag combinations.

## 4. Conflicting Flag Guards

If a command still accepts mutually exclusive flags, always guard against conflicts explicitly.

| Pattern | Fix |
| :--- | :--- |
| `--enable` and `--disable` both passed | `if enable && disable { return fmt.Errorf("cannot specify both --enable and --disable") }` |
| `--create` and `--delete` both passed | `if create && delete { return fmt.Errorf("cannot specify both --create and --delete") }` |

## 5. Error Handling

Never silently ignore errors.

| Pattern | Fix |
| :--- | :--- |
| `_, _ := svc.Do()` (result and error ignored) | Handle or log the error |
| `fmt.Sscanf(str, "%d", &idx)` without checking error | Check error — invalid input silently leaves `idx=0`, causing wrong behavior |
| Network errors in loops producing empty results | Log warning to `os.Stderr`: `fmt.Fprintf(os.Stderr, "warning: %v\n", err)` |
| Fetch error swallowed before mutation | Return error immediately before proceeding to write operation |
| Cleanup `Delete()` error ignored | At minimum log: `fmt.Fprintf(os.Stderr, "warning: failed to clean up: %v\n", err)` |
| Loop over items printing errors but returning `nil` | Collect errors with `errors.Join(errs...)` so caller sees failures |

## 6. Input Sanitization & Header Injection

User-supplied strings must be sanitized before embedding in structured formats.

| Pattern | Fix |
| :--- | :--- |
| Header fields (`To`, `Subject`, `Cc`) with embedded newlines | Strip all ASCII control characters: `strings.Map` to drop runes ≤ 0x1F (except tab) and 0x7F |
| API search queries with special characters | Escape special characters before embedding in query strings |
| Coordinate/range parsing that only extracts digits | Use a proper regex or parser to validate prefixes, letters, and separators |

## 7. Security & Privacy

Guard against operations that expose user data unintentionally.

| Pattern | Fix |
| :--- | :--- |
| File upload sets world-readable / public permissions | Require explicit `--public` flag; default to private / scoped permissions |
| Sensitive credentials printed in verbose logs | Redact API keys, tokens, and authorization headers before logging |

## 8. Dangerous Operations → Confirmation Guards

Commands that permanently delete or modify data must be explicitly guarded.

| Pattern | Fix |
| :--- | :--- |
| `delete` — permanent resource deletion | Add `--confirm` or `--force` flag; require interactive confirmation if stdin is a TTY |
| `delete-all` / `purge` — bulk destructive actions | Require typing resource name or explicit `--confirm` flag |

## 9. Control Flow Clarity

Complex conditional logic should be restructured for readability.

| Pattern | Fix |
| :--- | :--- |
| Nested if/else chains for get/enable/disable | Restructure: `if enable { ... } if disable { ... }` with early returns |
| Output separator missing between logical sections | Print consistent delimiters (e.g. `---`) between headers and body |

## 10. Logic Bugs

| Pattern | Fix |
| :--- | :--- |
| Export command ignores requested format extension | Respect `--output` extension (JSON vs YAML vs CSV) |
| Dead API call (result and error both unused) | Remove dead code entirely |
| Zero values omitted when updating remote resources | Ensure zero-values are explicitly serialized when clearing fields |

## 11. Idiomatic Go

| Pattern | Fix |
| :--- | :--- |
| `strings.SplitN(s, sep, 2)` + length check | Use `strings.Cut(s, sep)` — returns `(before, after, ok)`, much cleaner |
| `make([]T, n)` + `for i := range { fill }` | Use `slices.Repeat([]T{val}, n)` |
| Magic number `-1` in `strings.Map` to drop runes | Use `unicode.ReplacementChar` or document deletion logic |
| Generic function name like `parseInputValues` | Name should describe format: `parsePipeSeparatedRows` |
| Manual file extension check via `strings.LastIndexByte` | Use `filepath.Ext(path)` — handles edge cases correctly |

## 12. Code Style

| Pattern | Fix |
| :--- | :--- |
| Multiple `var x string` on consecutive lines | Consolidate: `var name, email, phone string` |
| CLI name in help text doesn't match actual binary name | Ensure Examples and Short descriptions use the current CLI binary name |
| Map literal with multiple entries on one line | One key-value per line, trailing commas |
