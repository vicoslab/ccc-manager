#! /usr/bin/env bash
envvars=('PORT_PASSWORD_FORMAT' 'GIT_USER_NAME' 'GIT_USER_EMAIL')

for e in ${envvars[@]}; do
    if [[ -z ${!e} ]]; then
        echo "Error: $e not found in the environment."
        exit 1
    fi
done

git config --global --add safe.directory /opt/ccc-inventory
git config --global user.name "$GIT_USER_NAME"
git config --global user.email "$GIT_USER_EMAIL"

if [[ -n $CCC_INVENTORY ]]; then
    git clone $CCC_INVENTORY /opt/ccc-inventory || exit 1
elif [[ ! -e /opt/ccc-inventory ]]; then
    echo "CCC_INVENTORY is empty and /opt/ccc-inventory was not provided. Exiting."
    exit 1
fi

exec streamlit run index.py
