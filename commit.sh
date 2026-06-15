#! /usr/bin/env bash
set -u

lockfile=/opt/ccc-manager/commit.lock
inventory_dir=${CCC_INVENTORY_DIR:-/opt/ccc-inventory}

function cleanup() {
    rm -f "$lockfile"
}

function error() {
    echo "$1"
    cleanup
    exit 1
}

function reset_worktree() {
    git rebase --abort >/dev/null 2>&1 || true
    git merge --abort >/dev/null 2>&1 || true
    git reset --hard HEAD >/dev/null 2>&1 || true
}

if [[ -e "$lockfile" ]]; then
    error 'Could not acquire lock. Try again.'
fi
touch "$lockfile"
trap cleanup EXIT

patchfile=$1
sed -e 's/\x1b\[[0-9;]*m//g' -i "$patchfile"

if [[ -z ${2:-} ]]; then
    error 'Commit message not provided'
fi

cd "$inventory_dir" || error "Inventory directory not found: $inventory_dir"

upstream=$(git rev-parse --abbrev-ref --symbolic-full-name '@{u}' 2>/dev/null || true)
if [[ -n "$upstream" ]]; then
    git fetch --prune || error 'Could not fetch remote changes'
    git rebase "$upstream" || {
        reset_worktree
        error 'Could not synchronize with remote before applying changes'
    }
else
    git pull --rebase || error 'Could not pull with rebase'
fi

git apply --3way "$patchfile" || {
    git diff --diff-filter=U --color || true
    reset_worktree
    error 'Patch failed'
}

git add inventory/group_vars/ccc-cluster/{user-list,user-containers}.yml
git commit -m "$2" || error 'Commit failed'

git pull --rebase
STATUS=$?
if [[ $STATUS -ne 0 ]]; then
    git diff --diff-filter=U --color || true
    git rebase --abort >/dev/null 2>&1 || true
    git reset --hard HEAD~1 >/dev/null 2>&1 || true
    error 'Rebase not successful'
fi

git push || error 'Push failed'
cleanup
trap - EXIT
