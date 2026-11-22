---
name: ui-developer
description: End-to-end loop for building React/TypeScript UI features with agents - typed component, behavior tests, Storybook isolation, property tests for stateful UI, and feature-map-driven visual verification. Use when building or changing a UI feature or component, together with engineering-discipline. Don't use for a one-line style or copy tweak (core rules only), stories alone (use storybook), or journey capture alone (use cuj-screenshots).
license: Apache-2.0
---

# UI Developer

The loop for shipping a UI feature that a human can review from evidence instead of reading every line. Commands below use `bun`; use the repo's own package manager.

## The loop

1. **Name it.** Find the feature in the repo's feature map (`docs/features/` or `docs/CUJs.md`) and use its exact name. If the feature is new, add its entry first: what the user sees, how they reach it, and the end state that proves it works. See cuj-screenshots for the shape.
2. **Build the component.** Typed props, no `any`. Use the repo's blessed wrappers for effects, timers, and data fetching (see below).
3. **Test behavior.** React Testing Library queries by role and accessible name, not by class or DOM position. Assert what the user sees, not internal state. Run `bun test <Component>`.
4. **Isolate in Storybook.** One story per state: default, loading, empty, error, long content, mobile. See the storybook skill.
5. **Property-test stateful UI.** For anything with more than a couple of states (forms, editors, lists with selection, undo), add a property test that runs random action sequences and checks invariants. Example with `fast-check`: "after any sequence of add, remove, and undo, the visible count equals the model count". A UI property tester such as Bombadil does the same against the running app.
6. **Verify through the real surface.** Drive the running app through the repo's verification driver and capture the journey (cuj-screenshots). Look at the screenshots yourself before you claim done.
7. **Ship evidence.** Commit the code, tests, stories, and updated feature map together. Put the screenshots or GIF in the PR description so review starts from behavior.

## Ban nuance in product code

Raw effects and timers are where agent-written UI goes wrong: missing cleanup, stale closures, render races, flicker. If the repo has a lint ban and a blessed wrapper, use the wrapper. If it has neither, do not spread the raw form. Propose the wrapper and lint ban (codebase-gardening, step 3).

| Raw form | Prefer |
|---|---|
| `useEffect` to sync or derive state | compute during render, `useMemo`, or an event handler |
| `useEffect` to fetch data | the repo's data layer (TanStack Query, loaders, server components) |
| `setTimeout`, `setInterval`, `requestAnimationFrame` | a scheduling wrapper that cleans up on unmount |
| imports across `client/`, `server/`, `main/`, `renderer/` | the declared API between the two sides |

## Done checklist

- [ ] Feature map entry exists and matches the shipped behavior.
- [ ] Behavior tests and property tests pass (paste counts).
- [ ] Stories cover every state.
- [ ] Journey captured through the real app after the last code change.
- [ ] No new lint suppressions, `any`, or raw effects and timers outside wrappers.

## Related skills

- **storybook**: story patterns, play functions, batch screenshots.
- **cuj-screenshots**: journey capture, GIFs, feature map shape.
- **engineering-discipline**: verification evidence and freshness rules.
- **codebase-gardening**: lint bans, boundaries, and a reusable verification driver.
