import os
import glob

PASSWORD_FORMAT = os.environ['PORT_PASSWORD_FORMAT']
INVENTORY_DIR = os.environ.get('CCC_INVENTORY_DIR', '../ccc-inventory')
PORTAINER_TOKEN = os.environ.get('PORTAINER_TOKEN', None)
PORTAINER_URL = os.environ.get('PORTAINER_URL', None)

nodes = glob.glob(f'{INVENTORY_DIR}/inventory/*.yml')[0]
users = f'{INVENTORY_DIR}/inventory/group_vars/ccc-cluster/user-list.yml'
containers = f'{INVENTORY_DIR}/inventory/group_vars/ccc-cluster/user-containers.yml'