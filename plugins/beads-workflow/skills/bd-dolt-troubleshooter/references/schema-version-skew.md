# Schema Version Skew in beads (bd)

This guide covers troubleshooting and recovery runbooks for beads (`bd`) schema version skew across versions, multi-agent environments, and development builds.

---

## Schema Version Skew (remote-backed database migration block)

**Symptom:** A newer bd version (e.g., a watcher app, agent tool, or second machine)
fails to open the database with:
```
Failed to open beads database: failed to initialize schema: refusing to auto-apply
N pending schema migrations to a remote-backed database (vX -> vY):
migrating clones independently forks the schema (#4259)
```
Simultaneously, `dolt-server.log` fills with recurring errors like:
```
error running query ... error="column "content_hash" could not be found in any table in scope"
```

**Root-cause:**

bd added schema migrations (new columns, tables, etc.) between the version the
database was last migrated on and the version the new client was built against.
The new client refuses to apply those migrations automatically because the
database has a Dolt **remote** configured (`bd dolt show` shows a remote URL).
Applying migrations locally without pushing would leave the remote at the old
schema, so any other clone pulling from the remote would get mismatched data —
a schema fork.

The old server (the running `dolt sql-server`) continues serving the old schema.
Any client querying for columns from the new schema (like `content_hash`) gets
SQL errors on every poll.

**Before touching anything, take a filesystem-level backup.** During an active
skew, `bd`'s own safety nets are unreliable: `bd export --all` frequently hits
the *same* missing-column error as `bd list` (it doesn't go through the gate,
it just runs the failing query), and `bd vc status` / `bd dolt commit` hit the
gate itself (see the dirty-working-set trap below). Don't trust either as a
pre-migration backup:
```bash
cp -R .beads/dolt /tmp/bd-raw-snapshot-$(date +%Y%m%d-%H%M%S)
```

**Fix — apply once on primary, push, then pull on all clones:**

```bash
# 1. On the machine with the running bd server (primary):
#    The exact gate-bypass flag/subcommand has moved between bd versions —
#    check `bd migrate --help` for your build. As of bd 1.1.x it's a
#    top-level flag: `bd migrate --force` (equivalent to setting
#    BD_ALLOW_REMOTE_MIGRATE=1). Older builds instead required
#    `BD_ALLOW_REMOTE_MIGRATE=1 bd migrate schema`. Without one of these,
#    the gate fires first and reports "Schema already at vX" even though
#    nothing was applied. Note `--force` cannot be combined with `--dry-run`
#    (opening the store with the gate overridden applies the migration
#    before any preview could run).
bd migrate --force                            # applies vX → vY (bd 1.1.x+)
# BD_ALLOW_REMOTE_MIGRATE=1 bd migrate schema # equivalent on older builds
bd migrate --inspect       # confirm Schema Version is now vY
bd dolt push               # push migrated schema + data to remote

# 2. On every other clone (including the machine running the watcher):
bd dolt pull               # pull the migrated schema from remote

# 3. Restart the watcher / newer-version bd client
#    It will now open successfully at the new schema version.
```

**Trap: migration blocked by a dirty working set (chicken-and-egg with `bd
dolt commit`).** If the `issues` table (or any table) has uncommitted Dolt
changes, `bd migrate --force` fails instead of migrating:
```
Error: failed to open database: failed to initialize schema: schema
migration: pending schema migrations alter pre-existing dirty tables: issues;
run 'bd dolt commit' to commit the working set at the current schema, then
re-run the migration (gastownhall/beads#4566)
```
The suggested fix doesn't work as stated: `bd dolt commit` *also* opens the
database through the same gated path and fails with the identical "refusing
to auto-apply" gate error — it can't get past the gate to do the very commit
it's telling you to do. `BD_ALLOW_REMOTE_MIGRATE=1 bd dolt commit` hits the
exact same wall.

**Workaround — commit the working set with the raw `dolt` CLI, bypassing bd's
schema gate entirely.** This talks straight to the already-running
`dolt sql-server` (bd's Go-level gate lives in the `bd` binary, not the
server), so it isn't subject to the check:
```bash
# 1. Confirm what's dirty and that it's a DATA change, not a schema change
#    (a dirty schema change here would mean something already touched the
#    table structure outside a migration — investigate before committing).
dolt --data-dir .beads/dolt sql -q "use <dolt_database>; select * from dolt_status"
dolt --data-dir .beads/dolt sql -q \
  "use <dolt_database>; select * from dolt_diff_summary('HEAD','WORKING','<table>')"
#    schema_change must be 0 to proceed safely.

# 2. Commit the working set at the CURRENT (pre-migration) schema
dolt --data-dir .beads/dolt sql -q \
  "use <dolt_database>; CALL DOLT_COMMIT('-a', '-m', 'chore(bd): commit working set before schema migration');"

# 3. Verify clean, then retry the bd migration
dolt --data-dir .beads/dolt sql -q "use <dolt_database>; select * from dolt_status"  # empty
bd migrate --force
```
`<dolt_database>` is the name from `bd dolt show` (`Database:` field), e.g.
`eldamo_server`. Find it and the data dir with `bd dolt show`; the data dir is
almost always `.beads/dolt` in server mode.

**Verify the migration landed:**
```bash
bd migrate --inspect        # Schema Version should match the new bd binary version (e.g. 1.2.2)
bd doctor                   # should pass schema checks with 0 errors
```

**Note on the version numbers you'll see:** 
The gate error message uses internal sequential migration counter IDs (e.g. `(v62 -> v65)`), whereas `bd migrate --inspect` reports the semver release stamp (`Schema Version: 1.2.2, Registered Migrations: 0`), and `bd doctor` may report a third semantic-looking scale ("Database: version 1.0.5 (CLI: 1.2.2)"). These all describe the same underlying schema delta — do not be thrown by the different version scales.

---

### The `unreadable-remote-state` Gate & Which Clone Migrates

**Symptom:**
When `bd` cannot read or query the remote's schema state directly (e.g., git remote lacks an active Dolt server endpoint, or network/ref skew occurs), the migration gate returns a structured error:
```json
{
  "error": "refusing to auto-apply N pending schema migrations to a remote-backed database (vX -> vY): migrating clones independently forks the schema (#4259)",
  "hint": "Coordination decision required: only ONE clone may migrate a shared remote...",
  "remote_migrate_gate": {
    "fallback_reason": "unreadable-remote-state",
    "human_decision_required": true,
    "options": [
      {
        "id": "migrate",
        "commands": ["bd migrate --force", "bd dolt push"],
        "when": "you are the single designated migrator (only ONE machine, confirmed with the operator) and no other clone has migrated yet"
      },
      {
        "id": "adopt",
        "commands": ["bd bootstrap"],
        "when": "another machine has already migrated and pushed"
      }
    ]
  }
}
```

**Decision Rule:**
Only **one clone** may migrate a shared remote. If two clones migrate independently, their internal Dolt commit graphs fork and become unrecoverable without manual database surgery.

1. **Check with the human operator**: Ask if another machine has already performed the migration.
2. **Preflight pull**: Run `bd dolt pull`. If this pulls in an already-migrated schema from another clone, choose **adopt** (`bd bootstrap`).
3. **If this machine is the designated migrator**:
   ```bash
   # 1. Take a safe pre-migration backup of the JSONL export
   cp .beads/issues.jsonl /tmp/beads-premigrate.jsonl
   bd export -o /tmp/beads-export-backup.jsonl 2>/dev/null || true

   # 2. Force the migration
   bd migrate --force

   # 3. Verify
   bd migrate --inspect
   bd doctor

   # 4. Publish to remote so all other clones can adopt
   bd dolt push
   ```
4. **On all other clones**: Do NOT run `--force`. Simply run `bd dolt pull` (or `bd bootstrap` if re-cloning).

**Why the watcher error recurs every 30s:** The watcher is likely running a
keep-alive or polling loop. Each iteration hits the missing-column SQL error and
logs it. The errors stop once the migration is applied and the watcher is
restarted.

**Prevention:**

- Before upgrading bd on any machine that has a watcher, agent, or second-machine
  clone reading the same Dolt remote: apply `bd migrate schema && bd dolt push`
  on the primary first, then update the secondary.
- Add `bd migrate --inspect` to CI/release gates to catch schema drift before it
  reaches clones.
- Keep all bd clients (CLI, watcher, agent) on the same version, or upgrade in
  primary-first order.

---

## Schema Version Skew — Client BEHIND the Database (the inverse case)

The section above is a *newer* client blocked from migrating an *older* DB.
This is the mirror image, and it is the more likely one in a multi-agent
setup: your bd binary is **older** than a database another agent/machine
already migrated **forward**.

**Symptom:**
```
Warning: schema skew ignored — database (v54) is ahead of binary (v53); some queries may fail
```
or in `bd doctor`:
```
  ⚠ ... schema version mismatch: database is at v54, binary knows up to v53
    (1 migrations ahead)
```
Reads mostly succeed (with the warning under `--ignore-schema-skew`), but **every write fails**:
```
Error updating <id>: failed to record event: record event in events:
Error 1105 (HY000): Field 'id' doesn't have a default value
```
`scripts/diagnose.sh` shows the Dolt-vs-JSONL check reporting `dolt=?` for
issues (the old binary cannot read the newer schema, so status comes back
unknown while JSONL still has the real state).

**Root cause (a multi-agent coordination hazard):** bd auto-migrates a
shared Dolt database forward the first time a newer client touches it. Once
that happens, every *older* client on the same DB is stranded — it can read
past the skew but cannot write against the changed schema (e.g., the `events`
table's `id` column changed between versions). This is not corruption and it
is not fixable with `bd migrate` on the old binary: a v49 binary cannot
apply — or write against — a v53 schema it doesn't know.

**The CLI Error Recommendation Trap (`@latest` vs. `@main` & `CGO_ENABLED=0`):**
When `bd` hits schema skew, its terminal error prompt instructs you to run `CGO_ENABLED=0 go install ...@latest`. **Do NOT follow this advice in multi-agent environments:**
1. **`@latest` vs. `@main` Trap:** Installing `@latest` simply re-downloads an older published release tag (e.g., `v1.1.0`), leaving your client behind a database that was migrated forward by an agent running `@main` development builds.
2. **`CGO_ENABLED=0` Trap:** Rebuilding in pure-Go mode bypasses native ICU header linking (`unicode/regex.h`), but silently disables embedded database inspection engines, causing 15+ checks in `bd doctor` to degrade with `Skipped: requires CGO`.

1. **Identify what the installed binary actually is** — `bd --version` is not
   enough. A dev build shows the same version string as a published tag but may
   be commits ahead. `(dev)` in the version string is a red flag. Use:
   ```bash
   go version -m "$(which bd)"
   # Look for the `mod` line — a pseudo-version
   # (v1.x.x-0.YYYYMMDDHHMMSS-<hash>) means it was built from an untagged commit.
   ```
   Then find the target (the version that migrated the DB) by checking `go version -m`
   on the binary that triggered the migration, or the latest tag/pseudo-version:
   ```bash
   go list -m -versions github.com/steveyegge/beads   # tagged releases
   go list -m github.com/steveyegge/beads@main         # main-tip pseudo-version
   ```
2. Reinstall bd from source at that version, or run the automated restoration script:
   ```bash
   # Automated rebuild against @main with CGO + ICU support, disk check, and auto-sync PATH:
   scripts/restore-bd.sh --migrate

   # Or inspect module revisions across multiple installed binaries:
   scripts/inspect-binary.sh
   ```
   If building manually:
   ```bash
   ICU="$(brew --prefix icu4c)"        # or icu4c@<N>, e.g. icu4c@78
   CGO_CFLAGS="-I$ICU/include" CGO_CPPFLAGS="-I$ICU/include" \
   CGO_LDFLAGS="-L$ICU/lib" \
     go install github.com/steveyegge/beads/cmd/bd@main
   ```
   Recent bd also requires a newer Go toolchain (it auto-switches, e.g. to
   go1.26.x, if `go >= 1.26.2` is declared).
3. **Sync or link every copy of the binary on your PATH.** `go install` writes to
   `~/go/bin`; if your active PATH `bd` is elsewhere (e.g. `~/.local/bin/bd`),
   replace the shadowed copy with a symlink (`ln -sf ~/go/bin/bd ~/.local/bin/bd && hash -r`)
   or remove it if `~/go/bin` is already in PATH (`rm ~/.local/bin/bd && hash -r`).
   Using a symlink permanently prevents the upgrade trap where subsequent `go install`
   commands leave the active binary stale. A stale second copy is a classic "I upgraded
   but it's still the old version" trap — `bd` itself will warn: `Warning: multiple 'bd' binaries found in PATH`.
   Verify all installed copies using `scripts/inspect-binary.sh` or manually via `which -a bd && go version -m "$(which bd)"`.
4. Verify: `bd doctor` no longer reports the mismatch, and a real write
   (`bd update <id> --append-notes "..."`) succeeds. After the new binary
   applies any pending migration it may prompt `Run bd dolt push` — push so
   other clones converge.

For manual macOS Homebrew / Linux package manager instructions, version revision inspection (`go version -m`), and deep-dive schema coordination rules, refer to **`references/cgo-and-schema-drift.md`**.

**Read-only stopgap** if you cannot upgrade immediately: the global flag
`--ignore-schema-skew` ("proceed despite forward schema drift; some queries
may fail") lets the old binary read the newer DB. It does **not** fix writes
(the `events` schema mismatch still bites) — it only buys time to read.

**Prevention (multi-agent):** all agents/machines sharing one bd database
MUST run compatible bd binaries. Before an agent migrates a shared DB forward,
confirm the others can be upgraded to match; otherwise you strand them. A
session preflight of `bd doctor` catches the skew before you rely on writes.

### Preflight: confirm a newer *release* actually exists before upgrading

The fix above assumes `go install …@latest` gets you a binary that knows the
DB's schema version. **Verify this before running it** — if the DB was
migrated forward by someone running an unreleased/branch build (the case
below), `@latest` resolves to the same old tag you already have and changes
nothing:

```bash
go list -m -versions github.com/steveyegge/beads   # highest tagged release
go list -m github.com/steveyegge/beads@main         # main-tip pseudo-version
```

Compare the two. Pseudo-versions sort as `vX.Y.Z-0.<timestamp>-<hash>`; if the
`@main` pseudo-version's base (`vX.Y.Z`) is *lower than or equal to* the
highest tag, `main` has not yet been released — a plain `@latest` install
will **not** advance your schema knowledge past the tag's max version. If
your binary is already on the latest tag and the DB is still ahead, skip
straight to the next section.

---

## Schema Version Skew — DB Migrated by an Unreleased Build (no newer release exists)

This is a variant of "Client BEHIND the Database" above, but the standard fix
(upgrade to `@latest`) is a no-op: **you already have the latest tagged
release, and the database is still ahead of it.** This happens when another
agent, teammate, or CI job ran a `bd` built from `main` (or a feature branch)
that contains migrations not yet in any tag, and that binary auto-migrated
the shared DB forward.

**Symptom:** identical to the standard case (`bd doctor` reports "database is
at vN, binary knows up to vM"), but the preflight above shows no newer
release exists — `@main`'s pseudo-version does not exceed your current tag.

**Confirm it conclusively — don't guess.** Match the DB's applied migrations
against a fresh clone of `main` by content hash, not just version number
(version numbers alone don't prove the *content* came from `main` rather
than, say, a different fork):

```bash
# 1. Get the DB's applied migration ledger (versions + content hashes)
dolt --data-dir .beads/dolt sql -q \
  "use <dolt_database>; select * from schema_migrations order by version desc limit 15;"

# 2. Clone the source and list the highest migration files it ships
git clone --depth 1 https://github.com/steveyegge/beads.git /tmp/bd-src-check
ls /tmp/bd-src-check/internal/storage/schema/migrations/*.up.sql | xargs -n1 basename | sort -t_ -k1 -n | tail -10

# 3. For each migration version present in the DB but missing from your
#    installed binary's release tag, sha256 the corresponding file on main
#    and compare to the DB's content_hash for that version:
shasum -a 256 /tmp/bd-src-check/internal/storage/schema/migrations/00NN_*.up.sql
```

A byte-identical `content_hash` match against `main`'s migration files
proves the DB was walked forward by a `main`-derived binary — not corruption,
not a different fork, not a hand-edited ledger. Tell-tale new tables in
`show tables` (e.g. `leases` as a standalone table, `wisp_*` variants, a
`federation_peers` table) are a fast first signal that recent, unreleased
feature work touched the schema before you dig into hashes.

**Fix — install the exact commit that owns the migrations, not `@latest`:**

```bash
# Identify the commit: match the migration content hash to a specific commit,
# or use the latest main HEAD if you have no other lead.
git -C /tmp/bd-src-check log -1 --format="%H %ci %s"

# Pin to that commit (reproducible) rather than a moving `@main` target —
# especially important for a database other agents/machines will keep
# migrating; a floating @main pin means your schema cap can silently drift
# again on the next `go install`.
CGO_ENABLED=0 go install -tags gms_pure_go \
  github.com/steveyegge/beads/cmd/bd@<full-commit-hash>

# Sync every PATH copy (see the shadowed-binary trap above), then verify:
cp ~/go/bin/bd "$(command -v bd)" && hash -r
bd doctor        # schema skew warning should be gone
bd update <id> --append-notes "verify write path"   # real write must succeed
```

**Note on `CGO_ENABLED=0 -tags gms_pure_go`:** this sidesteps the ICU/CGO
build requirement (SKILL.md's CGO/ICU gotcha above) at the cost of disabling
several `bd doctor` checks that need CGO (`Dolt Locks`, `Orphaned
Dependencies`, `Duplicate Issues`, and others report "Skipped: requires
CGO"). This is an acceptable tradeoff to unblock writes; if those checks
matter, build with CGO and the ICU headers instead.

**Why this is a distinct case from the standard fix:** the standard fix's
entire premise is "install the newer release." When no newer release exists,
the stranded client isn't behind an upstream *version* — it's behind an
upstream *commit* that was never tagged. Treating this as "just run
`@latest`" wastes a cycle reinstalling the same binary and produces the
confusing symptom of the skew warning persisting after an "upgrade."

**Prevention:** in any multi-agent setup where agents may run bd built from
`main` or feature branches (not just tagged releases), a session preflight
should compare *commit*, not just semantic version — `go version -m` on every
active binary — since two binaries can report the same `bd --version` string
while being schema-incompatible dev builds from different points on `main`.

---

## Schema Version Skew — Accidental Release Downgrade (e.g. v1.2.0/v1.2.1 -> v1.2.2 Cursor Rollback)

**Symptom:** Upstream published an accidental or untested release (e.g. `v1.2.0`/`v1.2.1`) that advanced database schemas forward (e.g. from `v53` up to `v65`). When upgrading to a stabilized release that returns to a tested branch (e.g. `v1.2.2` returning to `v1.1.2` speaking schema `v53`), `bd` commands abort:
```
schema version mismatch: database is at v65, binary knows up to v53 (12 migrations ahead)
  This database was migrated by the accidental, untested v1.2.0/v1.2.1 release.
```

**Root cause:** Because the intermediate schema additions were strictly additive (no dropped or renamed tables/columns), no destructive data migration is needed. Rolling the migration ledger cursor back in Dolt aligns the metadata with the supported binary.

**Recovery Runbook (~2 minutes):**

1. **Stop servers and snapshot:**
   ```bash
   bd dolt stop
   cp -a .beads .beads.backup-pre-recovery-$(date +%s)
   ```

2. **Revive chunk journal (if corrupted by crashes):**
   If `dolt-server.log` reports `corrupted journal` or `invalid journal record length`:
   ```bash
   cd .beads/dolt/<database>   # or .beads/embeddeddolt/<database>
   dolt fsck --revive-journal-with-data-loss
   dolt fsck                   # verify: "No problems found."
   ```

3. **Roll back the schema cursor to v53:**
   ```bash
   cd .beads/dolt/<database>   # or .beads/embeddeddolt/<database>
   dolt sql -q "DELETE FROM schema_migrations WHERE version > 53; CALL DOLT_ADD('schema_migrations'); CALL DOLT_COMMIT('-m', 'recovery: roll schema cursor back to v53 (accidental v1.2.1)', '--author', 'bd recovery <recovery@beads.invalid>');"
   ```

4. **Verify and export:**
   ```bash
   bd list
   # Re-export JSONL, ensuring agent memories are preserved:
   bd export --include-memories -o .beads/issues.jsonl
   ```
