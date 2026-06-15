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

if [[ -e "$lockfile" ]]; then
    error 'Could not acquire lock. Try again.'
fi
touch "$lockfile"
trap cleanup EXIT

cd "$inventory_dir" || error "Inventory directory not found: $inventory_dir"

git rebase --abort >/dev/null 2>&1 || true
git merge --abort >/dev/null 2>&1 || true

upstream=$(git rev-parse --abbrev-ref --symbolic-full-name '@{u}' 2>/dev/null || true)
if [[ -z "$upstream" ]]; then
    branch=${CCC_INVENTORY_BRANCH:-$(git branch --show-current)}
    if [[ -z "$branch" ]]; then
        error 'Could not determine inventory branch to reset'
    fi
    upstream="origin/$branch"
fi

git fetch --prune || error 'Could not fetch remote changes'
git reset --hard "$upstream" || error "Could not reset inventory to $upstream"
git clean -fd || error 'Could not remove untracked inventory files'

echo "Inventory reset to $upstream"
cleanup
trap - EXIT
