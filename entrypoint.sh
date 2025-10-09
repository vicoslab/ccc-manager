#! /usr/bin/env bash
envvars=('CCC_INVENTORY' 'PORT_PASSWORD_FORMAT' 'GIT_USER_NAME' 'GIT_USER_EMAIL')

for e in ${envvars[@]}; do
    if [[ -z ${!e} ]]; then
        echo "Error: $e not found in the environment."
        exit 1
    fi
done

git config --global user.name "$GIT_USER_NAME"
git config --global user.email "$GIT_USER_EMAIL"

git clone $CCC_INVENTORY /opt/ccc-inventory

streamlit run index.py
