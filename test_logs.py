import unittest
from unittest.mock import Mock, patch

import logs


class LogsPortainerEndpointTests(unittest.TestCase):
    def test_parse_endpoints_accepts_missing_snapshots(self):
        servers = logs.parse_endpoints(b'[{"Id": 7, "Name": "node-a"}]')

        self.assertEqual(servers, {'node-a': (7, {})})

    def test_parse_endpoints_reads_legacy_snapshot_containers(self):
        servers = logs.parse_endpoints(b'''[
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
        ]''')

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


if __name__ == '__main__':
    unittest.main()
