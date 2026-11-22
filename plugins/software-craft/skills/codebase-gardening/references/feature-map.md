# Feature map shape

Adapted from pstack `create-verification-skill` (MIT). Keep the map in the repo, for example `docs/features/` or inside a project-local `verify-<app>` skill. Write it from the user's point of view. Leave implementation details out.

## Index (`README.md`)

- **Baseline preconditions:** launch command, disposable data dir, seed data, and the `doctor` check to run first.
- **Driving conventions:** stable handles (ARIA roles and names, data attributes, prompt strings, routes) over CSS selectors or coordinates. Restore seeded data after a mutation.
- **Proof rules:** capture the action and the resulting state, not only the final screen. For a mutation, confirm the stored value from a second, read-only view. CLI proof is the command, stdout, stderr, and exit code.
- **Features:** one line per feature, linking to its file.

## One file per feature

```markdown
# Create a note

One paragraph: what the user can do and see.

## Sub-features
- `create-save` persists a title and body.
- `create-cancel` discards an unfinished draft.

## How to get to it (user POV)
- Choose `New note` in the toolbar.
- Press `n` outside a text field.
- Run `notes create --title <t> --body <b>`.

## Driving it with <driver>
Preconditions: app healthy, no note titled `Release checklist`.
- **Save note.** Run `verify browser click --role button --name "Save note"`. A status `Note saved` appears.
- **Confirm persistence.** Reopen the note from `All notes`. Both values show.

## Gotchas
- Pressing `n` inside a text box types the letter.
- A save status alone is not proof. Reopen the note.
```

Rules:

- Cover every entry point a user has. A proof through one convenient path does not verify the others.
- If seed data lacks a precondition, report the journey as failed and note why in `Gotchas`. Never weaken the journey to make it pass.
- Update the map in the same change that adds, renames, or removes a feature.
