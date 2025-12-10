import requests
import json
import asyncio
import httpx

def parse_endpoints(content):
    servers = {}
    for endpoint in json.loads(content):
        id = endpoint['Id']
        name = endpoint['Name']

        assert len(endpoint['Snapshots']) == 1
        containers = { c['Names'][0][1:]: c for c in endpoint['Snapshots'][0]['DockerSnapshotRaw']['Containers'] }

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

def fetch_logs(base_url, token, endpoint, containers):
    params = { 'stdout': 1, 'stderr': 1 }
    headers = { 'X-API-Key': token }
    url = f'{base_url}/api/endpoints/{endpoint}/docker/containers/%s/logs'
    
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    limits = httpx.Limits(max_connections=10)
    client = httpx.AsyncClient(limits = limits)

    tasks = [client.get(url % c, params=params, headers=headers, timeout=60) for c in containers]
    responses = loop.run_until_complete(asyncio.gather(*tasks))
    loop.run_until_complete(client.aclose())

    return [parse_log(r.content) if r.status_code == 200 else None for r in responses]

def _format_line(line):
    id, message = line
    message = message.strip()
    if id == 2:
        return f'<span style="color: orange;">{message}</span>'
    return f'<span style="color: gray;">{message}</span>'

def format_html(lines):
    return '''
        <style>
        pre {
            overflow: auto;
            counter-reset: line;
        }
        pre span:before {
            counter-increment: line;
            content: counter(line);
            display: inline-block;
            border-right: 1px solid;
            margin-right: .5em;
            width: 3em;
        }
        </style><pre>%s</pre>''' % '\n'.join(map(_format_line, lines))