# ccc-manager
This is a simple [Streamlit](https://streamlit.io/) web interface made for use with the Conda Compute Cluster.

> [!WARNING]
> Although it is designed to manage the `ccc-inventory`, its current form has some hard-coded logic that makes it incompatible out of the box with the [ccc-sample-inventory](https://github.com/vicoslab/ccc-sample-inventory). The changed code deals primarily with splitting the users based on comments and inserting new entries at those locations.

## Installation
```bash
git clone https://github.com/vicoslab/ccc-manager
cd ccc-manager

docker build -t ccc-manager .
```

## Running
First you need to create an environment file that will contain your configuration/secrets:
```
PORT_PASSWORD_FORMAT={0}_{rand:5.5}
GIT_USER_NAME=ccc-manager WebUI
GIT_USER_EMAIL=email@example.com

# sample inventory doesn't work out of the box
#CCC_INVENTORY=https://github.com/vicoslab/ccc-sample-inventory
```

| Name | Value |
|------|-------|
| PORT_PASSWORD_FORMAT | Python format string for user's default HTTP port password. Positional arguments contain lowercase ascii formated user name, and named arguments contain `rand` which is a 32 characters long randomly generated hex string (you can truncate it - see example). |
| GIT_USER_NAME | Name used for AUTHOR of commits |
| GIT_USER_EMAIL | Email used for AUTHOR of commits |
|||
|**Optional**||
| CCC_INVENTORY | Git repository used as the inventory. If not provided (alongside CCC_INVENTORY_BRANCH), a repository is expected to be mounted in `/opt/ccc-inventory`.|
| CCC_INVENTORY_BRANCH | Git branch from repository. If not provided (alongside CCC_INVENTORY), a repository is expected to be mounted in `/opt/ccc-inventory`.|
| CCC_INVENTORY_SSHKEY | Authentication with ssh key is also possible, in which case the provided remote must be a ssh url. |

```
docker run \
    -v .:/opt/ccc-manager \
    -v /path/to/ccc-inventory:/opt/ccc-inventory \
    --user 1000 \
    -p 8080:8501 \
    --env-file .env \
    ccc-manager
```
For hot reloads, `ccc-manager` is mounted into the directory (the production build should copy `ccc-manager` files into the image).

### Local remote
You can also test things with a local directory as your git remote. This is great if you're rebasing/reseting/pushing often.

```bash
# make a copy of your repo
git clone ccc-inventory ccc-inventory-remote

# set remote 
cd ccc-inventory
git remote set-url origin file:///path/to/ccc-inventory-remote

# remove remote from the remote (probably not needed)
cd ../ccc-inventory-remote
git remote remove origin
```

In your `docker run`, you need to add a mount for the remote as well, since it will try to access it by the file:// url: `-v /path/to/ccc-inventory-remote:/path/to/ccc-inventory-remote`.
