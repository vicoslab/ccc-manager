import requests
import json
import asyncio
import httpx
from html import escape


class PortainerAPIError(RuntimeError):
    pass


def _portainer_headers(token):
    return {'X-API-Key': token}


def _raise_for_portainer_error(response, action):
    if response.ok:
        return

    detail = response.text.strip()[:200]
    message = f'Portainer API failed while {action}: HTTP {response.status_code}'
    if response.status_code in (401, 403):
        message += '; check that PORTAINER_TOKEN is a valid API key for this Portainer user'
    if detail:
        message += f' ({detail})'
    raise PortainerAPIError(message)


def _container_name(container):
    """Return the Docker container name used by the rest of the UI."""
    names = container.get('Names') or []
    if not names:
        return None

    name = names[0]
    if name.startswith('/'):
        return name[1:]
    return name


def _containers_by_name(containers):
    return {
        name: container
        for container in containers or []
        if (name := _container_name(container))
    }


def _snapshot_containers(endpoint):
    """Extract containers from the endpoint snapshot when Portainer includes it."""
    for snapshot in endpoint.get('Snapshots') or []:
        docker_snapshot = snapshot.get('DockerSnapshotRaw') or {}
        if 'Containers' in docker_snapshot:
            return docker_snapshot['Containers']
    return None


def parse_endpoints(content):
    servers = {}
    for endpoint in json.loads(content):
        id = endpoint['Id']
        name = endpoint['Name']
        containers = _snapshot_containers(endpoint)

        servers[name] = id, _containers_by_name(containers)
    return servers


def _fetch_endpoint_containers(base_url, token, endpoint_id):
    url = f'{base_url}/api/endpoints/{endpoint_id}/docker/containers/json'
    r = requests.get(url, headers=_portainer_headers(token), params={'all': 'true'}, timeout=60)
    _raise_for_portainer_error(r, f'listing containers for endpoint {endpoint_id}')
    return r.json()


def init(base_url, token):
    url = base_url + '/api/endpoints'
    r = requests.get(url, headers=_portainer_headers(token), timeout=60)
    _raise_for_portainer_error(r, 'listing endpoints')

    endpoints = r.json()
    servers = {}
    for endpoint in endpoints:
        id = endpoint['Id']
        name = endpoint['Name']
        containers = _snapshot_containers(endpoint)
        if containers is None:
            containers = _fetch_endpoint_containers(base_url, token, id)
        servers[name] = id, _containers_by_name(containers)
    return servers



def container_status_icon(info, lines):
    text = '🔴'
    if info['State'] == 'running':
        if lines is None:
            text = '⚪'
        else:
            try:
                start = len(lines) - 1 - lines[::-1].index((1, 'Starting pre-service scripts in /etc/runit_init.d'))
                text = '🟡'
                if any('/etc/runit_init.d/99_welcome_msg.sh' in x for _, x in lines[start:]):
                    text = '🟢'
            except ValueError:
                text = '🟣'
    return text

def parse_log(content):
    lines = []
    for line in content.split(b'\n'):
        if len(line) > 8:
            # each line starts with 8 byte header (1 byte type (stdout=1, stderr=2), 3 bytes padding, 4 bytes length)
            type = int(line[0])
            message = line[8:].decode('utf-8')
            lines.append((type, message))
    return lines


def fetch_logs(base_url, token, endpoint, containers, limit=None):
    params = { 'stdout': 1, 'stderr': 1 }
    if limit is not None:
        params['tail'] = limit
    headers = _portainer_headers(token)
    url = f'{base_url}/api/endpoints/{endpoint}/docker/containers/%s/logs'

    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    limits = httpx.Limits(max_connections=10)
    client = httpx.AsyncClient(limits = limits)

    tasks = [client.get(url % c, params=params, headers=headers, timeout=60) for c in containers]
    responses = loop.run_until_complete(asyncio.gather(*tasks, return_exceptions=True))
    loop.run_until_complete(client.aclose())

    return [parse_log(r.content) if isinstance(r, httpx.Response) and r.status_code == 200 else None for r in responses]


def _format_line(line):
    id, message = line
    message = escape(message.strip())
    if id == 2:
        return f'<span style="color: orange;">{message}</span>'
    return f'<span style="color: gray;">{message}</span>'


def format_html(lines):
    if lines is None:
        lines = [(2, 'Unable to fetch logs from Portainer for this container.')]

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
