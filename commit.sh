#! /usr/bin/env bash

if [[ -z $1 ]]; then
    echo 'Commit message not provided' >&2
    exit 1
fi

cd /opt/ccc-inventory/inventory/group_vars/ccc-cluster/

git add user-list.yml user-containers.yml
git commit -m "$1" &> /dev/null

git pull --rebase &> /dev/null
STATUS=$?
if [[ $STATUS -ne 0 ]]; then
    echo 'Rebase not successful' >&2
    git diff --diff-filter=U --color
    git rebase --abort
    git reset --hard HEAD~1 &> /dev/null
    exit 1
fi

git push
