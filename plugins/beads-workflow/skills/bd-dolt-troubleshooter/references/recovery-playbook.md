# Recovery Playbook (Harder Cases)

Use this when the standard repair (`scripts/repair-corrupt-backup.sh`) isn't
enough — e.g. Dolt and JSONL have genuinely diverged, or writes were lost.

## Case A: Dolt is correct, JSONL is stale

The Dolt DB has your latest changes (`bd show` is right) but `issues.jsonl`
is behind.

```bash
bd export -o .beads/issues.jsonl
# verify, then commit
```

This is the common case. The export regenerates JSONL from the authoritative
Dolt state.

## Case B: JSONL is correct, Dolt is stale/reverted

A write was lost in Dolt but `issues.jsonl` still reflects the intent (rare),
or you want to reset Dolt to match the committed JSONL.

```bash
bd dolt stop
# bd re-imports issues.jsonl into the working DB on next command
bd dolt start
bd list --status open   # triggers import; confirm state
```

If Dolt still doesn't match, re-apply the specific mutations and verify each
with `bd show` *before* exporting.

## Case C: Both diverged — reconcile by intent

Neither layer is fully right. Treat your **intended** end-state as truth.

1. Repair the backup first (`scripts/repair-corrupt-backup.sh`) so writes stop
   reverting.
2. For each affected issue, set the intended state explicitly:
   ```bash
   bd close <id> --reason "..."      # or
   bd update <id> --priority N --title "..."
   ```
3. After **each** write, verify it landed in Dolt:
   ```bash
   bd show <id> --json | python3 -c "import json,sys;d=json.load(sys.stdin);i=d[0] if isinstance(d,list) else d;print(i['status'],i['priority'])"
   ```
4. Once all are correct in Dolt, export once and diff:
   ```bash
   bd export -o .beads/issues.jsonl
   git diff .beads/issues.jsonl
   ```

## Case D: Restore from a bd backup snapshot

If the Dolt DB is unrecoverable:

```bash
bd backup list                 # see available snapshots
bd backup restore <snapshot>   # restore the DB
bd export -o .beads/issues.jsonl
```

Note: `bd backup` snapshots are distinct from the `.beads/backup/` Dolt backup
target that causes the corruption — don't confuse them.

## Case E: Engine mode mismatch (embedded when server data exists)

`bd dolt show` reports `Mode: embedded` but `.beads/dolt/` contains an existing
server-mode database. bd won't start properly, or throws "hyphens are not allowed
in embedded mode" errors.

1. Find the existing database name and configured port:
   ```bash
   ls .beads/dolt/                        # directory name = database name
   grep "port:" .beads/dolt/config.yaml   # server port
   ```

2. Re-init into server mode, preserving all server data:
   ```bash
   bd init --server --reinit-local \
     --database <db-name> \
     --server-port <port> \
     --non-interactive \
     --skip-hooks --skip-agents
   ```
   bd will auto-start a Dolt server pointed at the existing `.beads/dolt/` data.
   If it picks a different port than configured, pin it afterward:
   ```bash
   # find the new port
   bd dolt status
   # optionally pin it in config.yaml for team consistency
   # dolt: port: <N>
   ```

3. If a repo ID mismatch remains (daemon-error still present):
   ```bash
   bd migrate --update-repo-id --yes
   ```

4. Clean up the stale daemon-error file:
   ```bash
   rm -f .beads/daemon-error
   ```

5. Verify all issues are accessible:
   ```bash
   bd list --all
   bd dolt show   # should report Mode: per-project and ✓ Server connection OK
   ```

## Case F: Multiple `dolt sql-server` processes — lock contention across projects

**Symptom.** `bd dolt start` (or auto-start) fails with:
```
server started (PID N) but not accepting connections on port … : timeout
```
and `.beads/dolt-server.log` shows repeated:
```
database "dolt" is locked by another dolt process; either clone the database to
run a second server, or stop the dolt process which currently holds an exclusive
write lock on the database
```
Dolt takes a **single exclusive filesystem write lock** per data directory. This
bites in two situations:
- **Bind-mounted `.beads/` shared between two machines** (e.g. a host + a
  container both mounting the same workspace): only ONE server may run against it,
  on *either* machine. bd's per-project auto-start is not cross-machine-aware.
- **One machine running many projects at once**: each project has its own
  `dolt sql-server`, so you must not blanket-kill them — killing another project's
  server disrupts that project's bd state.

**Do NOT `kill` all `dolt sql-server` processes.** Isolate the one bound to *this*
project's `.beads/` directory. The reliable discriminator is each server's
**current working directory (CWD)**, not its port (ports here are ephemeral).

### 1. Identify the server that owns THIS project (prints PID + path together)

macOS / BSD (`lsof`):
```bash
for pid in $(pgrep -f "dolt sql-server"); do
  cwd=$(lsof -a -p "$pid" -d cwd -Fn 2>/dev/null | sed -n 's/^n//p')
  printf 'PID %s\t%s\n' "$pid" "$cwd"
done
```
Linux (`/proc`, no lsof needed):
```bash
for pid in $(pgrep -f "dolt sql-server"); do
  printf 'PID %s\t%s\n' "$pid" "$(readlink -f /proc/$pid/cwd)"
done
```
The target is the PID whose path is under **this repo's** `.beads/`. A bundled
helper does exactly this and highlights the match:
```bash
scripts/find-dolt-server.sh            # lists all; marks the one for CWD's repo
```

### 2. Stop only that server (prefer the scoped command)

From the project root, `bd dolt stop` acts on **this project's** server only —
it will not touch other projects' servers:
```bash
bd dolt stop
```
Re-run the PID+path loop to confirm no remaining process points at this repo's
`.beads/`. Only if a truly orphaned process survives, `kill <that-PID>` — the
*specific* PID you identified, never a blanket kill.

> **Trap: `bd dolt stop` can report "server is not running" while the process is
> still alive.** When the server was auto-started (or started outside bd's
> management) and this shell has `BEADS_DOLT_AUTO_START=false`, bd does not treat
> it as *its* managed server, so `bd dolt stop` prints
> `Error: dolt server is not running` **even though the `dolt sql-server` process
> is still holding the lock.** Do not trust that message — **always re-verify by
> PID** (`pgrep -af 'dolt sql-server'` or the PID+path loop) and `kill` the
> specific orphan. Observed live: an auto-started server survived `bd dolt stop`
> and only died on `kill <PID>` (SIGTERM was sufficient; escalate to `kill -9`
> only if it persists). After killing, `pgrep`'s own command line may match the
> pattern — confirm you're not seeing a false positive from the grep/pgrep itself.

### 3. Clear stale runtime files and start the single owner immediately

These are machine-local and never committed (safe to remove). Include `dolt-server-config.yaml` when resetting ephemeral port state:
```bash
rm -f .beads/dolt-server.lock .beads/dolt-server.port \
      .beads/dolt-server.info .beads/dolt-server.pid \
      .beads/dolt-server-config.yaml
bd dolt start
bd dolt status
```

> **Trap: Auto-start race with other `bd` commands.** Almost every `bd` subcommand (even `bd hooks install --force`) silently auto-starts a background `dolt sql-server` if `.beads/dolt-server.port` is missing. **Always run `bd dolt start` FIRST immediately after `rm -f .beads/dolt-server*`** — never chain another `bd` command ahead of `bd dolt start`, or the first command will spawn a background server and `bd dolt start` will immediately collide with `database "dolt" is locked by another dolt process`.

### Cross-machine coordination (bind-mount case)

If the `.beads/` is bind-mounted into a container, don't run a second server
there — pick ONE owner (usually the host) and make the other side Dolt-free
(`BEADS_DOLT_AUTO_START=false`), reading issues from `.beads/issues.jsonl`
directly. See the project's `AGENTS.md` for the full host/container runbook.

---

## Case G: Schema version skew — remote-backed database refuses auto-migration

A newer bd binary (watcher, agent, second machine) cannot open the database
because pending schema migrations exist but the database has a Dolt remote, so
auto-applying would fork the schema across clones.

Error signature:
```
refusing to auto-apply N pending schema migrations to a remote-backed database
(vX -> vY): migrating clones independently forks the schema (#4259)
```
Secondary symptom in `dolt-server.log` — recurring every poll interval:
```
error running query ... error="column "<col>" could not be found in any table in scope"
```

**Recovery:**

0. **Back up first, and don't trust `bd export` to do it.** During active skew,
   `bd export --all` typically fails with the same missing-column error `bd
   list` does (it runs the failing query directly rather than hitting the
   gate). Take a raw filesystem copy instead:
   ```bash
   cp -R .beads/dolt /tmp/bd-raw-snapshot-$(date +%Y%m%d-%H%M%S)
   ```

1. On the **primary** host (where the main bd server runs):
   ```bash
   # In bd 1.3.x+, `bd migrate --force` alone updates Dolt metadata without
   # applying SQL table migrations (0054-0066). Always run `bd migrate schema --force`
   # FIRST, followed by `bd migrate --force`, then commit any dirty config rows:
   bd migrate schema --force                     # apply SQL table migrations (vX → vY)
   bd migrate --force                            # update Dolt metadata version stamp
   bd vc commit -m "chore(bd): commit config working set" 2>/dev/null || true
   bd migrate --inspect                          # confirm Schema Version is now vY
   bd dolt push                                  # push to remote
   ```

2. On **every other clone** (including the watcher machine):
   ```bash
   bd dolt pull               # pull migrated schema
   ```

3. Restart the watcher / newer-version bd client. The SQL errors stop and the
   client opens successfully.

**If migration fails with "pending schema migrations alter pre-existing dirty
tables: `<table>`; run 'bd dolt commit' ..."** — a table has uncommitted Dolt
changes. The suggested `bd dolt commit` does **not** work: it opens the
database through the same gated path and fails with the identical "refusing
to auto-apply" error (chicken-and-egg — `BD_ALLOW_REMOTE_MIGRATE=1 bd dolt
commit` hits the same wall). Bypass bd entirely and commit via the raw `dolt`
CLI talking directly to the already-running server:
```bash
# Get the database name from `bd dolt show` (Database: field)
DB=<dolt_database>   # e.g. eldamo_server

# 1. Confirm the dirty change is DATA-only, not a schema change
dolt --data-dir .beads/dolt sql -q "use $DB; select * from dolt_status"
dolt --data-dir .beads/dolt sql -q \
  "use $DB; select * from dolt_diff_summary('HEAD','WORKING','<table>')"
#    schema_change must be 0 — if it's 1, stop and investigate first.

# 2. Commit the working set at the current (pre-migration) schema
dolt --data-dir .beads/dolt sql -q \
  "use $DB; CALL DOLT_COMMIT('-a', '-m', 'chore(bd): commit working set before schema migration');"

# 3. Verify clean (empty result), then retry
dolt --data-dir .beads/dolt sql -q "use $DB; select * from dolt_status"
bd migrate --force
```

**If `bd migrate` itself fails for other reasons** (the server is stuck or the
schema is partially applied):
```bash
bd dolt stop
bd dolt start
bd migrate --force --verbose   # retry with detail
```

**Upgrade order rule:** always migrate-and-push on the primary before updating
any secondary client to a newer bd version.

---

## Case H: Schema version skew — client binary is BEHIND the database (inverse of G)

The mirror image of Case G, and the more common one in a multi-agent setup:
another agent/machine already migrated the shared database **forward**, and
your bd binary is now **older** than the schema. bd auto-migrates a shared DB
on first touch by a newer client, which strands every older client on it.

Error signature (`bd doctor`):
```
schema version mismatch: database is at v53, binary knows up to v49
(4 migrations ahead)
```
Reads succeed with a warning; **writes fail**:
```
failed to record event: record event in events:
Error 1105 (HY000): Field 'id' doesn't have a default value
```
`scripts/diagnose.sh` reports the Dolt-vs-JSONL check as `dolt=?` (the old
binary can't read the newer schema).

**Recovery — upgrade the stranded client to match the DB (never downgrade the DB):**

> **THE CLI RECOMMENDATION TRAP:** When `bd` encounters schema version skew, its terminal error output instructs you to run `CGO_ENABLED=0 go install ...@latest`. **Do NOT set `CGO_ENABLED=0`** — pure-Go mode cripples embedded database inspection engines, causing 15+ tests in `bd doctor` to degrade with `Skipped: requires CGO`. In addition, if another agent migrated the database using an unreleased `@main` build, `@latest` will only fetch the latest published tag and leave you behind; verify first whether `@latest` or `--main` is needed.

1. **Automated Restoration (Recommended):**
   Execute the bundled restoration script from the skill directory. It automatically handles macOS/Linux ICU dependency discovery, compiles with `CGO_ENABLED=1`, and symlinks shadowed binary installations in your PATH:
   ```bash
   scripts/restore-bd.sh           # Rebuild against @latest (safe default across sibling repos)
   scripts/restore-bd.sh --main    # Use ONLY when DB was migrated past all published tags
   ```

2. **Manual Investigation & Compilation:**
   For manual version inspection (`go version -m "$(which bd)"`) or custom package setup commands across macOS (Homebrew `icu4c`) and Linux distributions (`libicu-dev`, `icu-dev`, `pkg-config`), consult the comprehensive reference runbook:
   * **See:** `references/cgo-and-schema-drift.md`

3. **Verify + converge:**
   ```bash
   bd doctor                       # mismatch and 'Skipped: requires CGO' warnings resolved
   bd update <id> --append-notes "skew fixed"   # real write succeeds against upgraded schema
   bd dolt push                    # if the new binary applied a pending migration
   ```

**Do NOT** run `bd migrate` on the old binary — it cannot apply (or write
against) a schema version it doesn't know.

**Read-only stopgap** if you can't upgrade yet: `bd --ignore-schema-skew <cmd>`
lets the old binary *read* the newer DB; it does not fix writes.

**Prevention (multi-agent):** all agents/machines sharing one bd database must
run compatible binaries. Before migrating a shared DB forward, confirm the
others can upgrade to match, or you strand them. Add `bd doctor` as a session
preflight so the skew surfaces before you rely on writes.

---

## Case I: Fresh clone in server mode — `database "<name>" not found on Dolt server` & `bd bootstrap` `embeddeddolt/` quirk

**Symptom.** On a fresh git clone (or new machine) of a repo whose `.beads/metadata.json` configures `"dolt_mode": "server"` and `"dolt_database": "<name>"`, every `bd` command fails:
```
Error: failed to open database: database "<name>" not found on Dolt server at 127.0.0.1:<port>
```
Simultaneously, `bd doctor` reports 3 errors and 6 cascading Federation warnings (`Federation remotesapi: remotesapi port 8080 not accessible`, `Peer Connectivity`, `Sync Staleness`, etc.) even when the project does not use federation.

**Root cause (two-part):**
1. `.beads/dolt/` is gitignored runtime state. On first invocation on a new clone, `bd` auto-starts `dolt sql-server` against an empty `.beads/dolt/` directory (which exposes only a default empty `dolt` database, not `<name>`).
2. In `bd v1.3.x`, running `bd bootstrap --yes` when importing from git-tracked `.beads/issues.jsonl` first retries 3 times against the running server (`10s + 20s + 40s` = **70s wait**) and then **imports the JSONL into `.beads/embeddeddolt/<name>` instead of `.beads/dolt/<name>`**. Because `dolt sql-server` serves `.beads/dolt/`, subsequent `bd` commands *still* fail with `database "<name>" not found` immediately after `Imported N issues`!

**Recovery (automated via `scripts/repair.sh`, or step-by-step):**

```bash
# 1. Configure local role if unset (prevents beads.role warning in bd doctor)
git config beads.role maintainer

# 2. Bootstrap from .beads/issues.jsonl (allow >=180s timeout for the 70s retry backoff)
bd bootstrap --yes

# 3. If bd placed the database under .beads/embeddeddolt/<name>, relocate it into .beads/dolt/<name>:
DB=$(sed -n 's/.*"dolt_database"[[:space:]]*:[[:space:]]*"\([^"]*\)".*/\1/p' .beads/metadata.json)
if [ -d ".beads/embeddeddolt/$DB" ] && [ ! -d ".beads/dolt/$DB" ]; then
  bd dolt stop
  # Verify no orphan dolt sql-server remains bound to this repo (Case F)
  scripts/find-dolt-server.sh
  mkdir -p .beads/dolt
  mv ".beads/embeddeddolt/$DB" ".beads/dolt/$DB"
  rm -rf .beads/embeddeddolt
  rm -f .beads/dolt-server.lock .beads/dolt-server.port \
        .beads/dolt-server.info .beads/dolt-server.pid \
        .beads/dolt-server-config.yaml
  # Start server FIRST before any other bd command (avoids auto-start lock race)
  bd dolt start
fi

# 4. Backfill local repo fingerprint & project_id metadata, commit Dolt working set, and verify
bd doctor --fix --yes
bd vc commit -m "chore(bd): commit metadata after bootstrap"
bd doctor          # should pass with 0 warnings, 0 errors
```

### Sub-case I.2: Unreachable `sync.remote` (e.g., GCS 403 / offline) with git-tracked `.beads/issues.jsonl`

When `.beads/config.yaml` configures a GCS federation remote (`sync.remote: "gs://..."`) that this machine cannot authenticate to (e.g., HTTP `403 AccessDenied` under a different ADC account), `bd bootstrap --yes` fails without falling back to `.beads/issues.jsonl`. Running `bd init --server --reinit-local` directly also fails with exit code `10`:
```
! could not verify refs/dolt/data on gs://... (git: 'remote-gs' is not a git command); treating remote as having Dolt history
bd init refuses: remote 'origin' already has Dolt history (refs/dolt/data).
```

If you want to restore a working local database from `.beads/issues.jsonl` while keeping `sync.remote` intact (without touching or pushing to GCS):

```bash
# 1. Record current HEAD and back up config.yaml; temporarily strip `sync:` so bd init does not probe gs://
BASE_HEAD=$(git rev-parse HEAD)
cp -f .beads/config.yaml /tmp/bd-config.yaml.bak
sed -i.bak '/^sync:/,$d' .beads/config.yaml && rm -f .beads/config.yaml.bak

# 2. Stop scoped server, clear empty .beads/dolt, and re-init local server DB (preserves metadata.json project_id)
bd dolt stop || true
rm -rf .beads/dolt .beads/dolt-server.* .beads/dolt.gate.lock
bd init --server --reinit-local --prefix <prefix> --database <db> --non-interactive --skip-agents --skip-hooks

# 3. Import authoritative JSONL and repair blocked flags
bd import .beads/issues.jsonl
bd recompute-blocked --json

# 4. Replace bd init's auto-wired git+ssh:// Dolt remote with the original GCS remote
REMOTE=$(sed -En 's/^[[:space:]]*remote:[[:space:]]*"?([^"[:space:]]+)"?.*/\1/p' /tmp/bd-config.yaml.bak | head -1)
bd dolt remote remove origin
[ -n "$REMOTE" ] && bd dolt remote add origin "$REMOTE"
bd dolt remote list    # confirm with remote list (bd dolt show may print Remotes: (none) in server mode)

# 5. Undo the 3 implicit git auto-commits (bd init, clear sync.remote, update sync.remote) and restore config.yaml
git reset --mixed "$BASE_HEAD"
git checkout -- .beads/config.yaml
rm -f /tmp/bd-config.yaml.bak

# 6. Verify
bd doctor
```

> **Do not run `bd dolt push` / `bd sync` against GCS from this locally-imported DB:** its Dolt commit graph has a different root commit than the existing GCS remote. Use local `bd` commands + `bd export -o .beads/issues.jsonl` + `git push` until you have GCS credentials; once authenticated, move `.beads/dolt` aside and run `bd bootstrap --yes` to adopt the shared remote history cleanly.

---

## Case J: Cross-Era Legacy Dolt Server Workspace (`bd v0.55–v0.62` → `bd v1.3+`)

**Symptom:** Every `bd` command (`bd dolt show`, `bd migrate --inspect`, `bd doctor`, `bd list`) immediately refuses with:
```
Error: legacy Dolt server workspace from bd 0.60.0 detected; explicit migration is required before this bd version can open or modify the workspace. Preserve .beads unchanged and follow docs/getting-started/upgrading.md#cross-era-upgrades
```

**Root cause:** `bd v1.3+` refuses workspaces whose `.beads/metadata.json` selects `dolt_mode: server` alongside a pre-v1 `.beads/.local_version` witness (`v0.55.4`–`v0.62.0`) or missing witness with `.beads/dolt/` present. Running `scripts/repair.sh` directly will fail because `bd migrate` and `bd export` are blocked by the cross-era guard.

### 1. Inspect the legacy Dolt DB vs committed `.beads/issues.jsonl` first

Before downloading an old `bd` binary, inspect the legacy Dolt DB directly with the raw `dolt` CLI (read-only) to see whether it holds any issues missing from `.beads/issues.jsonl`:

```bash
# Confirm no dolt sql-server is running for this repo
scripts/find-dolt-server.sh

# Check row count & commit history in the legacy Dolt DB
DB=$(python3 -c "import json; print(json.load(open('.beads/metadata.json'))['dolt_database'])")
dolt --data-dir .beads/dolt sql -q "use $DB; select count(*) from issues; select commit_hash, date, message from dolt_log limit 10;"
wc -l .beads/issues.jsonl
```

- **If the legacy Dolt DB contains unexported issues** not in `.beads/issues.jsonl`: snapshot `.beads/`, copy it to a disposable workspace, export with the verified historical `bd` binary (`v0.60.x`), and import that export into a fresh `v1.3+` workspace (per upstream `docs/getting-started/upgrading.md#cross-era-upgrades`).
- **Fast path (common on freshly synced clones):** If the legacy Dolt DB has **0 issues** (e.g., an empty initial `bd init` from months ago) or is strictly older than `.beads/issues.jsonl` committed in git, `.beads/issues.jsonl` is already your authoritative export.

### 2. Snapshot, re-initialize in `v1.3+`, and import `.beads/issues.jsonl`

Keep the git staging area clean first (both `bd init` and `bd dolt remote remove` auto-commit staged changes to git):

```bash
# 1. Full filesystem snapshot before touching anything
cp -R .beads "/tmp/bd-cross-era-backup-$(date +%s)"

# 2. Remove legacy untracked local DB and runtime state (preserves metadata.json & issues.jsonl)
rm -rf .beads/dolt .beads/backup .beads/.local_version .beads/dolt-server.* .beads/dolt-monitor.pid.lock

# 3. Re-initialize per-project server mode in bd v1.3+ (preserves existing project_id)
bd init --server --reinit-local --prefix <prefix> --database <db> --non-interactive --skip-agents

# 4. Import authoritative JSONL and repair blocked flags (bd v1.3.x #7037)
bd import .beads/issues.jsonl
bd recompute-blocked --json

# 5. Upgrade legacy git hooks (v0.60 -> v1.3+)
bd hooks install --force
```

### 3. Clean up post-init side effects and verify

```bash
# Untrack sensitive credential key if it was tracked in legacy commits
git ls-files --error-unmatch .beads/.beads-credential-key >/dev/null 2>&1 \
  && git rm --cached .beads/.beads-credential-key

# Resolve auto-wired git-origin Dolt remote conflict (see Golden Rule 12 for GCS federation)
# If local + git issues.jsonl only (no GCS federation):
bd dolt remote remove origin
# Then remove any leftover empty `sync:` block in .beads/config.yaml

# Verify health and write persistence
bd migrate --inspect
bd doctor
scripts/diagnose.sh --probe

# Inspect git log — bd init and bd dolt remote remove create auto-commits;
# squash into one clean commit before pushing.
git log --oneline -n 5
```

---

## Prevention checklist

- [ ] `.beads/backup/` is **not** in `git ls-files`
- [ ] `.beads/dolt-server.*` and `.beads/.beads-credential-key` are **not** in `git ls-files`
- [ ] `.beads/.gitignore` contains `backup/`, `dolt-server.pid`, `dolt-server.port`, `dolt-server.lock`, `*.corrupt.backup/`, `.beads-credential-key`
- [ ] CI/agents run `bd export -o .beads/issues.jsonl` before committing bd changes
- [ ] After bulk bd operations, diff `issues.jsonl` before `git commit`
- [ ] On any machine that must stay Dolt-free (the non-owning side of a
      bind-mounted `.beads/`, e.g. a container), `BEADS_DOLT_AUTO_START=false` is
      exported **in the current shell**, not just in `/etc/environment`. A `bd`
      command in a shell that missed the env var can auto-start a server and steal
      the lock. Set it explicitly: `export BEADS_DOLT_AUTO_START=false` before
      running `bd`, and prefer reading state from `.beads/issues.jsonl` directly.
- [ ] All agents/machines sharing one bd database run compatible bd versions —
      "compatible" means the same release tag (`v1.3.4`) or module pseudo-version hash,
      verified with `go version -m "$(which bd)"` (note: `go install …@vX.Y.Z` always
      prints `(dev)` in `bd --version` because module zips omit `.git` metadata; check
      the `mod` line in `go version -m` instead)
- [ ] Routine client upgrades target `@latest` (`scripts/restore-bd.sh`), reserving
      `--main` for databases already migrated past all published tags
- [ ] `bd doctor` is run as a session preflight (catches schema skew before writes)
