# README Scoring Rubric

Based on the checklist in [`mark-allen-checklist.md`](mark-allen-checklist.md), sourced from Mark Allen's ["How to Write a Great README for Your Public GitHub Project"](https://www.markcallen.com/how-to-write-a-great-readme-for-your-public-github-project/).

Score each dimension 0–5 using the anchors below, then sum for a total out of 40.

| # | Dimension | 0 (Missing) | 3 (Present) | 5 (Strong) |
|---|---|---|---|---|
| 1 | Project Description | No description, or only a vague tagline/buzzwords | States what the project does | One or two sentences, specific, no fluff, obvious in the first 5 seconds |
| 2 | Installation Instructions | None, or "see docs" with no link | Steps present but incomplete or requires guesswork | Copy-pasteable one-liner or exact command sequence, right near the top |
| 3 | Usage Example | None | A usage example exists somewhere in the doc | A real, minimal, working example appears immediately after install, in a code block |
| 4 | Local Dev Setup | None | Clone/install steps exist | Exact clone → install → run sequence, with required versions/env vars/ports called out |
| 5 | Publish / Deploy Process | Applicable but undocumented | Documented but vague | Exact release commands documented, or explicitly and correctly marked not applicable |
| 6 | Contribution Guidance | No mention of contributing | Generic "PRs welcome" with no process | Clear stance on PRs/issues, links to `CONTRIBUTING.md`/`CODE_OF_CONDUCT.md` if present |
| 7 | Markdown Structure | Wall of text, no headings/code blocks | Some headings and code blocks, inconsistent | Consistent headings, fenced code blocks with language hints, lists used for steps, links instead of bare mentions |
| 8 | Optional Extras (TOC, screenshots, diagrams, FAQ, troubleshooting, badges) | None present and project would benefit from them | One or two present | The extras that reduce real confusion for *this* project are present, without padding |

## Notes on Scoring

- **N/A handling:** If a dimension genuinely doesn't apply (e.g. no publish step for a script that's never released), score it 5 only if the README explicitly says so or the omission is self-evidently correct. Silent omission where a reader would wonder "wait, how do I install this?" scores low, not N/A.
- **Don't reward length.** A concise README that nails dimensions 1–4 outscores a long one padded with dimension 8 extras but weak on the fundamentals.
- **Weight the first four dimensions more in judgment, not just math.** They are what Mark Allen's post treats as non-negotiable (description, install, usage, dev setup); 5–8 are what separate good from great.

## Score Bands (out of 40)

| Total | Band | Meaning |
|---|---|---|
| 34–40 | Excellent | Model README. A stranger can go from zero to running it with no questions. |
| 25–33 | Good | Solid and usable; a few gaps worth closing. |
| 14–24 | Needs Improvement | Functional for insiders but missing key sections a newcomer needs. |
| 0–13 | Poor | Effectively undocumented. Rewrite using the checklist from scratch. |

## Reporting Format

When presenting an assessment, use a table like this, then state the total and band:

| Dimension | Score | Why |
|---|---|---|
| Project Description | 4/5 | Clear one-liner, but title alone doesn't hint at the domain |
| Installation Instructions | 5/5 | `npm install -g <pkg>` right at the top |
| Usage Example | 2/5 | Example exists but buried after a long architecture section |
| Local Dev Setup | 0/5 | Not present |
| Publish/Deploy Process | 5/5 | N/A, correctly stated (internal tool, no releases) |
| Contribution Guidance | 3/5 | "PRs welcome" but no link to process |
| Markdown Structure | 4/5 | Good headings, one code block missing language hint |
| Optional Extras | 3/5 | Has badges, no TOC despite 9 sections |
| **Total** | **26/40** | **Good** |
