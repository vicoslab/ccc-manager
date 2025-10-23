#! /usr/bin/env bash
lockfile=/opt/ccc-manager/commit.lock

function error() {
    echo $1
    rm -f $lockfile
    exit 1
}

if [[ -e $lockfile ]]; then
    error 'Could not acquire lock. Try again.'
fi
touch $lockfile

patchfile=$1
sed -e 's/\x1b\[[0-9;]*m//g' -i $patchfile

if [[ -z $2 ]]; then
    error 'Commit message not provided'
fi

cd /opt/ccc-inventory/

git apply $patchfile || error 'Patch failed'
git add inventory/group_vars/ccc-cluster/{user-list,user-containers}.yml
git commit -m "$2"

git pull --rebase
STATUS=$?
if [[ $STATUS -ne 0 ]]; then
    git diff --diff-filter=U --color
    git rebase --abort
    git reset --hard HEAD~1
    error 'Rebase not successful'
fi

git push
rm $lockfile
