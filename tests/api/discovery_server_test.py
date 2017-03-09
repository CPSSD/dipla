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

    @patch("dipla.api.urlopen")
    def test_conflict_error_handled(self, mock_urlopen):
        mock_urlopen.return_value = self.UrlResponseMock({
            "success": False,
            "error": "409: oh h*ck"
        })
        with self.assertRaises(DiscoveryConflict):
            Dipla.inform_discovery_server("http://a.com", "b", "c", "d")

    @patch("dipla.api.urlopen")
    def test_bad_request_error_handler(self, mock_urlopen):
        mock_urlopen.return_value = self.UrlResponseMock({
            "success": False,
            "error": "400: you've done me a frighten"
        })
        with self.assertRaises(DiscoveryBadRequest):
            Dipla.inform_discovery_server("http://a.com", "b", "c", "d")

    @patch("dipla.api.urlopen")
    def test_misc_error_handler(self, mock_urlopen):
        mock_urlopen.return_value = self.UrlResponseMock({
            "success": False,
            "error": "418: bork bork the tea is ready"
        })
        with self.assertRaises(RuntimeError):
            Dipla.inform_discovery_server("http://a.com", "b", "c", "d")

    @patch("dipla.api.urlopen")
    def test_runs_with_no_error(self, mock_urlopen):
        mock_urlopen.return_value = self.UrlResponseMock({
            "success": True
        })
        try:
            Dipla.inform_discovery_server("http://a.com", "b", "c", "d")
        except:
            self.fail("Unhandled error while informing server")
