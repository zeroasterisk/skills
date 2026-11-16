## Enforced rules

Every recurring correction lives here with what enforces it. Prose-only rows are debt: if one is violated again, move it up to code/types/lint/test in the same change. Delete a row once the mistake is impossible.

| Rule | Enforced by | Level | Proven on |
|------|-------------|-------|-----------|
| e.g. No main-process imports in renderer | `eslint no-restricted-imports` (`.eslintrc` L12), error names `src/shared/ipc` | lint | revert of abc123 |
| e.g. Dates parsed only at API boundary | `ParsedDate` brand type in `src/types.ts` | types | PR #42 bug |
| e.g. Prefer small PRs | — (judgment) | prose | — |

Levels, highest first: architecture → types → lint/CI → test → prose.
