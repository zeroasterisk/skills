# Standard Readme Compliance Checklist

Source: [Standard Readme](https://github.com/RichardLitt/standard-readme) by Richard Littauer (MIT licensed), [full spec](https://github.com/RichardLitt/standard-readme/blob/main/spec.md).

This is a **structural compliance spec**, not a quality rubric. It defines exact required sections, exact section order, and exact heading names. A README can satisfy every rule here and still be unhelpful, or fail several rules and still be genuinely good — this checklist only answers "does this follow the standard-readme format," not "is this a good README." Use [`scoring-rubric.md`](scoring-rubric.md) for quality; use this file only when the user asks specifically for standard-readme compliance (they say "standard-readme," ask for the compliance badge, or are publishing an npm library and want the ecosystem-standard format).

## Required section order

Sections that are present must appear in this order. Optional ones may be skipped, but present sections must not be reordered:

1. **Title** — no heading needed beyond `# Title`
2. Banner *(optional)*
3. Badges *(optional)*
4. **Short Description** *(required)*
5. Long Description *(optional)*
6. **Table of Contents** *(required if the README is 100+ lines; optional below that)*
7. Security *(optional)*
8. Background *(optional)*
9. **Install** *(required, unless it's a documentation-only repo with no code)*
10. **Usage** *(required, unless it's a documentation-only repo with no code)*
11. Extra Sections *(optional — any number of freeform sections go here, after Usage and before API)*
12. API *(optional)*
13. Maintainer(s) *(optional)*
14. Thanks *(optional)*
15. **Contributing** *(required)*
16. **License** *(required, and must be the last section)*

## Per-section rules

| Section | Rule |
|---|---|
| Title | Must match the repo, folder, and package-manager name. If it's a different, more readable title, put the actual name next to it in italics: `# Standard Readme Style _(standard-readme)_`. If names genuinely differ, explain why in Long Description. |
| Banner | No heading of its own. Must link to a locally-hosted image (not hotlinked). Must appear directly after the title. |
| Badges | No heading of its own. Newline-delimited. Prefer locally-hosted static badges over external services when avoiding tracking/requests matters. |
| Short Description | No heading of its own. **Under 120 characters.** Must not start with `> `. Must match the `package.json` `description` field and the GitHub repo description, if both exist. |
| Long Description | No heading of its own. If Title names diverge from repo/folder/package name, explain why here. |
| Table of Contents | Must link to every top-level (`##`) section. Starts with the section *after* the title/ToC itself — don't link to the Title or the ToC heading. |
| Install | Code block showing install. Add an `### Dependencies` subsection if there are unusual manual dependencies. |
| Usage | Code block showing common usage. If it's a CLI, add a `### CLI` subsection. If it's importable, show both the import and a usage call. |
| Extra Sections | No required heading — this is a catch-all label for "everything else," not a literal section name to use. |
| Maintainer(s) | Heading must be exactly `Maintainer` or `Maintainers`. List names with a contact method (GitHub handle or email). |
| Thanks | Heading must be exactly `Thanks`, `Credits`, or `Acknowledgements`. |
| Contributing | Must state where to ask questions, whether PRs are accepted, and any contribution requirements (e.g. commit sign-off). Link to `CONTRIBUTING.md` and a Code of Conduct if they exist. |
| License | Must state the license (SPDX identifier, or `UNLICENSED`, or `SEE LICENSE IN <file>`) and the license owner. Must be the last section in the file. |

## Other rules (not about section order)

- Filename must be `README` with the correct extension for the format (`README.md`, `README.org`, `README.html`, ...). Capitalize `README`.
- For translated READMEs, use a BCP 47 language tag: `README.de.md`. If there's only one README and it's not in English, plain `README.md` is fine without a tag; once multiple languages exist, `README.md` is reserved for English.
- No broken links.
- Code examples should be linted the same way the rest of the codebase is linted.
- The compliance badge is optional, not a requirement for compliance itself:
  ```markdown
  [![standard-readme compliant](https://img.shields.io/badge/readme%20style-standard-brightgreen.svg?style=flat-square)](https://github.com/RichardLitt/standard-readme)
  ```

## Where this conflicts with the Mark Allen checklist

These two sources disagree on some things. When running standard-readme compliance mode, standard-readme's rules win for structure; don't silently blend the two.

- **Order rigidity.** Mark Allen has no opinion on strict section order beyond "description, then install, then usage, then dev setup." standard-readme mandates a full fixed order, ending in License. If both are in play, tell the user which one you're optimizing for.
- **No dedicated Local Dev Setup section.** Mark Allen treats "clone → install → run" for contributors as its own named section, distinct from end-user Install. standard-readme has no slot for this — it would have to live inside `Install` itself or as an `Extra Sections` entry, which loses the install-vs-develop distinction.
- **No dedicated Publish/Deploy section.** Same issue: standard-readme would fold this into `Extra Sections` or `Maintainers`-adjacent content, not treat it as a first-class section.
- **Short Description byte-matching.** standard-readme requires the README's short description to literally match `package.json` and GitHub's repo description. This is an npm/GitHub-specific constraint; it doesn't apply to non-npm ecosystems and Mark Allen's post has no equivalent rule.
- **Contributing and License are hard-required by standard-readme** even for tiny personal projects; Mark Allen frames contribution guidance as more of a "signal you're open to help," optional in spirit for closed or non-collaborative projects.

## Reporting format

Report compliance as pass/fail per rule, not a 0–5 score:

| Rule | Status | Note |
|---|---|---|
| Title matches repo/package name | ✅ Pass | — |
| Short Description < 120 chars | ❌ Fail | 143 chars, also doesn't match `package.json` |
| Table of Contents present (file is 140 lines) | ❌ Fail | Missing |
| Install section with code block | ✅ Pass | — |
| Usage section with code block | ✅ Pass | — |
| Contributing states PR/question policy | ⚠️ Partial | Says "PRs welcome," no mention of where to ask questions |
| License stated and last section | ❌ Fail | License section exists but Thanks section follows it |

Summarize with a compliant/non-compliant verdict and the specific rules to fix for full compliance.
