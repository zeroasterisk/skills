---
name: headless-fork-pr
description: Execute upstream issue creation, git fork synchronization (upstream vs origin), and pull request submission in headless or sandbox environments where SSH keys require passphrases or GitHub OAuth tokens lack workflow scope.
license: Apache-2.0
compatibility: Requires git, gh (GitHub CLI with admin:public_key scope), and ssh-keygen.
metadata:
  author: ghchinoy
  version: "1.0.0"
---

# Headless Fork Synchronization & Cross-Remote PR Workflow (`headless-fork-pr`)

This skill provides a reliable workflow for filing upstream issues, synchronizing diverged GitHub forks, and opening pull requests from non-interactive/headless agent containers and sandboxes.

## Problem Context: Two Common Headless Git Traps

When working in a headless container or remote sandbox, standard `git push` operations to a fork often fail due to two environmental constraints:

1. **GitHub OAuth `workflow` Scope Rejection (HTTPS Push)**:
   When syncing `main` from an upstream repository that modified `.github/workflows/*`, pushing over HTTPS with a standard `gh` OAuth token fails:
   > `! [remote rejected] main -> main (refusing to allow an OAuth App to create or update workflow .github/workflows/... without workflow scope)`
2. **Passphrase-Protected SSH Keys (SSH Push)**:
   When switching remotes to `git@github.com:...`, existing user SSH keys (`~/.ssh/id_ed25519`) prompt interactively for a passphrase (`Enter passphrase for key ...`), causing background agent tasks to hang indefinitely.

## Bundled Helper Script

- [`scripts/ephemeral-ssh-git.sh`](scripts/ephemeral-ssh-git.sh) — Wraps any `git` remote command (`push`, `fetch`, `pull`) using an unencrypted ephemeral SSH key registered via `gh ssh-key add` (`admin:public_key` scope) and **unconditionally deletes the key from GitHub and disk via `trap EXIT`**.

---

## Step-by-Step Workflow

### Step 1: Normalize Remotes (`upstream` vs `origin`)

Ensure `upstream` points to the canonical repository and `origin` points to the user's fork using SSH URLs:

```bash
# If origin currently points to upstream, rename it:
git remote rename origin upstream
git remote add origin git@github.com:<your-username>/<repo>.git

# Verify remote topology:
git remote -v
```

### Step 2: File the Upstream Issue First

Create the tracking issue in the upstream repository before creating your feature branch so the branch name and commit trailer can reference the issue number:

```bash
gh issue create -R <upstream-owner>/<repo> \
  --title "fix(scope): concise description of the defect" \
  --body "## Problem\n...\n## Proposed Fix\n..."
```

### Step 3: Synchronize Fork `main` with Upstream `main`

Fetch `upstream/main`, rebase local `main`, and push to `origin/main` using `scripts/ephemeral-ssh-git.sh` to bypass both HTTPS `workflow` scope errors and SSH passphrases:

```bash
git checkout main
scripts/ephemeral-ssh-git.sh fetch upstream
git rebase upstream/main
scripts/ephemeral-ssh-git.sh push --force-with-lease origin main
```

### Step 4: Create Feature Branch, Implement Fix, and Verify

1. Create a branch referencing the issue number:
   ```bash
   git checkout -b fix/<short-slug>-<issue-number>
   ```
2. Implement the fix and add unit test coverage.
3. Run targeted verification (e.g., `go test`, `go vet`, linter) and ensure `git status` shows no untracked scratch artifacts.

### Step 5: Commit, Push via Ephemeral SSH, and Open PR

1. Commit with the upstream issue reference and any required environment trailers at the bottom of the commit description:
   ```bash
   git commit -m "fix(scope): concise summary of fix

Detailed explanation of root cause and resolution.

Fixes <upstream-owner>/<repo>#<issue-number>"
   ```
2. Push the feature branch to `origin`:
   ```bash
   scripts/ephemeral-ssh-git.sh push -u origin fix/<short-slug>-<issue-number>
   ```
3. Open the pull request against the target repository (`--repo <target-owner>/<repo>`):
   ```bash
   gh pr create --repo <target-owner>/<repo> \
     --base main \
     --head fix/<short-slug>-<issue-number> \
     --title "fix(scope): concise summary of fix" \
     --body "## Summary\n- Resolves <upstream-owner>/<repo>#<issue-number>\n- ..."
   ```
