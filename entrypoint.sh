#! /usr/bin/env bash
envvars=('PORT_PASSWORD_FORMAT' 'GIT_USER_NAME' 'GIT_USER_EMAIL')

for e in ${envvars[@]}; do
    if [[ -z ${!e} ]]; then
        echo "Error: $e not found in the environment."
        exit 1
    fi
done

git config --global user.name "$GIT_USER_NAME"
git config --global user.email "$GIT_USER_EMAIL"

if [[ -e /opt/ccc-inventory/.git ]]; then
    echo "Found provided /opt/ccc-inventory"
else
    if [[ -z $CCC_INVENTORY || -z $CCC_INVENTORY_BRANCH ]]; then
        echo 'When /opt/ccc-inventory is not provided, $CCC_INVENTORY and $CCC_INVENTORY_BRANCH must be set.'
        exit 1
    fi
    git clone -b $CCC_INVENTORY_BRANCH $CCC_INVENTORY /opt/ccc-inventory || exit 1
fi

cron
exec streamlit run index.py
