import unittest
from unittest.mock import Mock, patch

import logs


class LogsPortainerEndpointTests(unittest.TestCase):
    def test_parse_endpoints_accepts_missing_snapshots(self):
        servers = logs.parse_endpoints(b'[{"Id": 7, "Name": "node-a"}]')

        self.assertEqual(servers, {'node-a': (7, {})})

    def test_parse_endpoints_reads_legacy_snapshot_containers(self):
        servers = logs.parse_endpoints(b'''
            [
                {
                    "Id": 7,
                    "Name": "node-a",
                    "Snapshots": [
                        {
                            "DockerSnapshotRaw": {
                                "Containers": [
                                    {"Id": "abc", "Names": ["/alice"]},
                                    {"Id": "def", "Names": ["bob"]}
                                ]
                            }
                        }
                    ]
                }
            ]
        ''')

        self.assertEqual(set(servers['node-a'][1]), {'alice', 'bob'})
        self.assertEqual(servers['node-a'][1]['alice']['Id'], 'abc')

    @patch('logs.requests.get')
    def test_init_fetches_containers_when_endpoint_snapshots_are_not_returned(self, get):
        endpoints_response = Mock(ok=True)
        endpoints_response.json.return_value = [{'Id': 7, 'Name': 'node-a'}]
        containers_response = Mock(ok=True)
        containers_response.json.return_value = [{'Id': 'abc', 'Names': ['/alice']}]
        get.side_effect = [endpoints_response, containers_response]

        servers = logs.init('https://portainer.example', 'token')

        self.assertEqual(servers['node-a'][0], 7)
        self.assertEqual(servers['node-a'][1]['alice']['Id'], 'abc')
        get.assert_any_call(
            'https://portainer.example/api/endpoints/7/docker/containers/json',
            headers={'X-API-Key': 'token'},
            params={'all': 'true'},
            timeout=60,
        )

    @patch('logs.requests.get')
    def test_init_reports_authentication_failures(self, get):
        response = Mock(ok=False, status_code=401, text='Invalid API key')
        get.return_value = response

        with self.assertRaisesRegex(logs.PortainerAPIError, 'PORTAINER_TOKEN is a valid API key'):
            logs.init('https://portainer.example', 'expired-token')

    @patch('logs.requests.get')
    def test_init_skips_unreachable_endpoint_and_continues(self, get):
        endpoints_response = Mock(ok=True)
        endpoints_response.json.return_value = [
            {'Id': 1, 'Name': 'node-down'},
            {'Id': 2, 'Name': 'node-up'},
        ]
        down_response = Mock(ok=False, status_code=502, text='{"message":"Proxy failure"}')
        up_response = Mock(ok=True)
        up_response.json.return_value = [{'Id': 'abc', 'Names': ['/alice']}]
        get.side_effect = [endpoints_response, down_response, up_response]

        servers = logs.init('https://portainer.example', 'token')

        _, down_containers = servers['node-down']
        self.assertEqual(down_containers, {})
        _, up_containers = servers['node-up']
        self.assertEqual(up_containers['alice']['Id'], 'abc')

    @patch('logs.requests.get')
    def test_init_skips_endpoint_on_network_error_and_continues(self, get):
        import requests as req
        endpoints_response = Mock(ok=True)
        endpoints_response.json.return_value = [
            {'Id': 1, 'Name': 'node-down'},
            {'Id': 2, 'Name': 'node-up'},
        ]
        up_response = Mock(ok=True)
        up_response.json.return_value = [{'Id': 'def', 'Names': ['/bob']}]
        get.side_effect = [endpoints_response, req.exceptions.ConnectionError('dial failed'), up_response]

        servers = logs.init('https://portainer.example', 'token')

        _, down_containers = servers['node-down']
        self.assertEqual(down_containers, {})
        _, up_containers = servers['node-up']
        self.assertEqual(up_containers['bob']['Id'], 'def')


class LogsParseLogTests(unittest.TestCase):
    def test_parse_log_replaces_invalid_utf8_bytes_instead_of_raising(self):
        header = (1).to_bytes(1, 'big') + b'\x00\x00\x00' + (1).to_bytes(4, 'big')
        content = header + b'invalid \xe3 byte'

        lines = logs.parse_log(content)

        self.assertEqual(len(lines), 1)
        type_, message = lines[0]
        self.assertEqual(type_, 1)
        self.assertIn('invalid', message)
        self.assertIn('\ufffd', message)


class LogsContainerStatusIconTests(unittest.TestCase):
    def test_container_status_icon_reports_stopped_containers_as_red(self):
        self.assertEqual(logs.container_status_icon({'State': 'exited'}, []), '🔴')

    def test_container_status_icon_reports_running_without_logs_as_white(self):
        self.assertEqual(logs.container_status_icon({'State': 'running'}, None), '⚪')

    def test_container_status_icon_reports_running_without_start_marker_as_purple(self):
        self.assertEqual(logs.container_status_icon({'State': 'running'}, [(1, 'service output')]), '🟣')

    def test_container_status_icon_reports_preservice_as_yellow(self):
        lines = [(1, 'Starting pre-service scripts in /etc/runit_init.d')]

        self.assertEqual(logs.container_status_icon({'State': 'running'}, lines), '🟡')

    def test_container_status_icon_reports_welcome_message_as_green(self):
        lines = [
            (1, 'Starting pre-service scripts in /etc/runit_init.d'),
            (1, 'running /etc/runit_init.d/99_welcome_msg.sh'),
        ]

        self.assertEqual(logs.container_status_icon({'State': 'running'}, lines), '🟢')

    def test_container_status_icon_reports_legacy_welcome_message_as_green(self):
        lines = [
            (1, 'Starting pre-service scripts in /etc/runit_init.d'),
            (1, '*** Running: /etc/runit_init.d/10_welcome_msg'),
        ]

        self.assertEqual(logs.container_status_icon({'State': 'running'}, lines), '🟢')


if __name__ == '__main__':
    unittest.main()
