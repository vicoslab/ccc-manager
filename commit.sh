#! /usr/bin/env bash

if [[ -z $1 ]]; then
    echo 'Commit message not provided' >&2
    exit 1
fi

cd /opt/ccc-inventory/inventory/group_vars/ccc-cluster/

git add user-list.yml user-containers.yml
git commit -m "$1"
