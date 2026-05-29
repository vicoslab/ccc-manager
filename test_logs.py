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


if __name__ == '__main__':
    unittest.main()
