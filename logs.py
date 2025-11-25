import requests
import json

def parse_endpoints(content):
    servers = {}
    for endpoint in json.loads(content):
        id = endpoint['Id']
        name = endpoint['Name']

        assert len(endpoint['Snapshots']) == 1
        containers = endpoint['Snapshots'][0]['DockerSnapshotRaw']['Containers']
        containers = [x['Names'][0][1:] for x in containers]

        servers[name] = id, containers
    return servers

def init(base_url, token):
    url = base_url + '/api/endpoints'
    headers = {'X-API-Key': token}
    r = requests.get(url, headers=headers)
    if r.ok:
        return parse_endpoints(r.content)
    return None

def parse_log(content):    
    lines = []
    for line in content.split(b'\n'):
        if len(line) > 8:
            # each line starts with 8 byte header (1 byte type (stdout=1, stderr=2), 3 bytes padding, 4 bytes length)
            type = int(line[0])
            message = line[8:].decode('utf-8')
            lines.append((type, message))
    return lines

def show_log(base_url, token, endpoint, container):
    url = f'{base_url}/api/endpoints/{endpoint}/docker/containers/{container}/logs'
    params = { 'stdout': 1, 'stderr': 1 }
    headers = {'X-API-Key': token}
    r = requests.get(url, headers=headers, params=params)
    if r.ok:
        return parse_log(r.content)
    return None
