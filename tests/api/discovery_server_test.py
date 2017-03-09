import json
from unittest import TestCase
from unittest.mock import patch, Mock
from dipla.api import Dipla, DiscoveryConflict, DiscoveryBadRequest


class InformDiscoveryServerTest(TestCase):

    class UrlResponseMock:
        def __init__(self, response_data):
            self.response_data = json.dumps(response_data)

        def read(self):
            return self.response_data.encode()

    @patch('dipla.api.urlopen')
    def test_conflict_error_handled(self, mock_urlopen):
        mock_urlopen.return_value = self.UrlResponseMock({
            "success": False,
            "error": "409: oh h*ck"
        })
        with self.assertRaises(DiscoveryConflict):
            Dipla.inform_discovery_server('http://a.com', 'b', 'c', 'd')

