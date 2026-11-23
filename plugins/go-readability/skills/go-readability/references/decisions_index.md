# Go Style Decisions Coverage Index

One-line-per-rule index of sections in the [Google Go Style Decisions](https://google.github.io/styleguide/go/decisions). Use this to find authoritative guidance fast when generating or reviewing Go code.

Coverage legend:

-   ✅ — Covered in `SKILL.md` with rule + example
-   🟡 — Mentioned in `SKILL.md` but lighter than the canonical doc
-   📘 — Covered in a reference file (see column)
-   ❌ — Not covered (deliberate scope limit, or known gap)

| Decision section                  | Coverage | Where in this skill       |
| --------------------------------- | -------- | ------------------------- |
| **Naming**                        |          |                           |
| `underscores`                     | ✅        | SKILL.md § Naming         |
| `package-names`                   | ✅        | SKILL.md § Naming         |
| `receiver-names`                  | ✅        | SKILL.md § Naming         |
| `constant-names`                  | 🟡        | SKILL.md § Naming (covered by MixedCaps rule) |
| `initialisms`                     | ✅        | SKILL.md § Naming (Acronyms row) |
| `getters`                         | ✅        | SKILL.md § Naming (with Fetch / Compute alternatives) |
| `variable-names`                  | 🟡        | SKILL.md § Naming + common_mentor_feedback.md |
| `repetition` (and sub-sections)   | 📘        | common_mentor_feedback.md § Avoid Repetitive Naming |
| **Commentary**                    |          |                           |
| `comment-line-length`             | ✅        | SKILL.md § Documentation  |
| `examples`                        | 🟡        | SKILL.md § Documentation (testable doc examples) |
| `named-result-parameters`         | ❌        | (rare in practice; defer to canonical doc) |
| `package-comments`                | ✅        | SKILL.md § Documentation  |
| **Imports**                       |          |                           |
| `import-renaming`                 | ✅        | SKILL.md § Imports + standard_go_patterns.md |
| `import-grouping`                 | ✅        | SKILL.md § Imports        |
| `import-blank`                    | ❌        | (rare; defer to canonical doc) |
| `import-dot`                      | ❌        | (forbidden; not worth a section) |
| **Errors**                        |          |                           |
| `returning-errors`                | ✅        | SKILL.md § Error Handling |
| `error-strings`                   | ✅        | SKILL.md § Error Handling > Error string formatting |
| `handle-errors`                   | ✅        | SKILL.md § Error Handling |
| `in-band-errors`                  | 🟡        | SKILL.md § Common Gotchas (use `(value, ok)`) |
| `indent-error-flow`               | ✅        | SKILL.md § Error Handling > Indent error flow |
| **Language**                      |          |                           |
| `literal-formatting`              | 🟡        | SKILL.md § Common Gotchas (struct literal field names) |
| `nil-slices`                      | ✅        | SKILL.md § Nil slices     |
| `indentation-confusion`           | 🟡        | SKILL.md § Error Handling > Indent error flow |
| `func-formatting`                 | 🟡        | gofmt handles most of this |
| `conditional-formatting`          | ❌        | (gofmt handles most)      |
| `copying`                         | 🟡        | SKILL.md § Receiver type (sync.Mutex example) |
| `dont-panic`                      | ✅        | SKILL.md § Error Handling > Don't panic / Must |
| `must-functions`                  | ✅        | SKILL.md § Error Handling > Don't panic / Must |
| `goroutine-lifetimes`             | 🟡        | SKILL.md § Concurrency    |
| `interfaces`                      | ✅        | SKILL.md § Interfaces     |
| `generics`                        | ❌        | (rarely a readability blocker; defer) |
| `pass-values`                     | 🟡        | SKILL.md § Receiver type  |
| `receiver-type`                   | ✅        | SKILL.md § Receiver type  |
| `switch-break`                    | ✅        | SKILL.md § Switch & break |
| `synchronous-functions`           | 🟡        | SKILL.md § Concurrency    |
| `type-aliases`                    | ❌        | (rare; defer)             |
| `use-percent-q`                   | ✅        | SKILL.md § Error Handling > Use `%q` for quoted strings |
| `use-any`                         | ✅        | SKILL.md § Self-audit checklist |
| **Common libraries**              |          |                           |
| `flags`                           | 🟡        | standard_go_patterns.md   |
| `logging`                         | ✅        | SKILL.md § Error Handling + standard_go_patterns.md |
| `contexts`                        | ✅        | SKILL.md § Concurrency    |
| `crypto-rand`                     | ❌        | (security-specific; defer) |
| **Useful test failures**          |          |                           |
| `useful-test-failures` (overview) | ✅        | SKILL.md § Testing > Useful test failures |
| `assert` (no assert libraries)    | ✅        | SKILL.md § Testing        |
| `identify-the-function`           | 📘        | testing_failures.md       |
| `identify-the-input`              | 📘        | testing_failures.md       |
| `got-before-want`                 | 📘        | testing_failures.md       |
| `compare-full-structures`         | 📘        | testing_failures.md       |
| `compare-stable-results`          | 📘        | testing_failures.md       |
| `keep-going`                      | 📘        | testing_failures.md       |
| `types-of-equality`               | 📘        | testing_failures.md       |
| `level-of-detail`                 | 📘        | testing_failures.md       |
| `print-diffs`                     | 📘        | testing_failures.md       |
| `test-error-semantics`            | 📘        | testing_failures.md       |
| **Test structure**                |          |                           |
| `subtests`                        | 📘        | testing_failures.md       |
| `subtest-names`                   | 📘        | testing_failures.md       |
| `table-driven-tests`              | 🟡        | SKILL.md § Testing        |
| `table-tests-data-driven`         | ❌        | (advanced; defer to canonical) |
| `table-tests-identifying-the-row` | 📘        | testing_failures.md       |
| `mark-test-helpers`               | 🟡        | SKILL.md § Testing        |
| `test-package`                    | ❌        | (rare decision; defer)    |
| `use-package-testing`             | ✅        | SKILL.md § Testing        |

## See also

-   [Google Go Style Decisions](https://google.github.io/styleguide/go/decisions)
-   [Google Go Style Guide](https://google.github.io/styleguide/go/guide)
-   [Google Go Best Practices](https://google.github.io/styleguide/go/best-practices)
