#!/usr/bin/env bash
# discover-node-repos.sh — Enumerate local Node subprojects and optionally check remote GitHub repos.

set -euo pipefail

WORKSPACE="${1:-$HOME/projects}"
INCLUDE_REMOTE=false

for arg in "$@"; do
  if [ "$arg" = "--include-remote" ]; then
    INCLUDE_REMOTE=true
  fi
done

if [ ! -d "$WORKSPACE" ]; then
  echo "Error: Workspace directory '$WORKSPACE' does not exist." >&2
  exit 1
fi

echo "==> Scanning local Node subprojects in: $WORKSPACE"
find "$WORKSPACE" -maxdepth 5 -name "package.json" \
  -not -path "*/node_modules/*" \
  -not -path "*/.git/*" \
  -not -path "*/dist/*" \
  -not -path "*/.astro/*" \
  -not -path "*/.site-e2e-*" \
  | sort | while read -r pkg; do
    subproject_dir="$(dirname "$pkg")"
    rel_dir="${subproject_dir#"$WORKSPACE"/}"
    repo_name="${rel_dir%%/*}"
    repo_root="$WORKSPACE/$repo_name"

    lock_type="none"
    [ -f "$subproject_dir/package-lock.json" ] && lock_type="npm (package-lock.json)"
    [ -f "$subproject_dir/pnpm-lock.yaml" ] && lock_type="pnpm (pnpm-lock.yaml)"
    [ -f "$subproject_dir/yarn.lock" ] && lock_type="yarn (yarn.lock)"
    [ -f "$subproject_dir/bun.lockb" ] || [ -f "$subproject_dir/bun.lock" ] && lock_type="bun"

    git_branch="-"
    if [ -d "$repo_root/.git" ]; then
      git_branch="$(git -C "$repo_root" rev-parse --abbrev-ref HEAD 2>/dev/null || echo "-")"
    fi

    printf "  %-42s | lock: %-24s | branch: %s\n" "$rel_dir" "$lock_type" "$git_branch"
done

if [ "$INCLUDE_REMOTE" = true ]; then
  echo ""
  echo "==> Checking remote GitHub repositories via 'gh repo list' (not cloned locally)"
  if command -v gh >/dev/null 2>&1; then
    gh repo list --limit 100 --json name,isArchived,pushedAt,primaryLanguage \
      --jq '.[] | select(.isArchived == false) | "\(.name)\t\(.primaryLanguage.name // "-")\t\(.pushedAt)"' \
      | sort | while IFS=$'\t' read -r name lang pushed; do
        if [ ! -d "$WORKSPACE/$name" ]; then
          printf "  [remote-only] %-28s | lang: %-12s | pushed: %s\n" "$name" "$lang" "$pushed"
        fi
      done
  else
    echo "  Warning: 'gh' CLI not found; skipping remote check." >&2
  fi
fi
