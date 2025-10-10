# ccc-manager
This is a simple [Streamlit](https://streamlit.io/) web interface mad for use with the Conda Compute Cluster.

> [!WARNING]
> Although it is designed to manage the [ccc-inventory](https://github.com/vicoslab/ccc-sample-inventory), its current form has some hard-coded logic that makes it incompatible out of the box. The changed code deals primarily with splitting the users based on comments and inserting new entries at those locations.

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
| PORT_PASSWORD_FORMAT | Python format string for password. Positional arguments contain lowercase ascii formated user name, and named arguments contain `rand` which is 32 characters long randomly generated hex string. |
| GIT_USER_NAME | Name used for AUTHOR of commits |
| GIT_USER_EMAIL | Email used for AUTHOR of commits |
|||
|**Optional**||
| CCC_INVENTORY | Git repository used as the inventory. If not provided, a repository is expected to be mounted in `/opt/ccc-inventory`.|

```
docker run \
    -v .:/opt/ccc-manager \
    -v /path/to/ccc-inventory:/opt/ccc-inventory \
    -p 8080:8501 \
    --env-file .env \
    ccc-manager
```
For hot reloads, `ccc-manager` is mounted into the directory (the production build should copy `ccc-manager` files into the image).