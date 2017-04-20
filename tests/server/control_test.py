from unittest import TestCase
from unittest.mock import MagicMock
from pocketmock import create_mock_object
from dipla.server.server import Server
from dipla.server.control import start_server, stop_server


class ControlTest(TestCase):

    def test_start_server(self):
        mock_server = create_mock_object(Server)
        start_server(mock_server)
        self.assertTrue(mock_server.should_distribute_tasks)

    def test_stop_server(self):
        mock_exit_function = MagicMock()
        stop_server(mock_exit_function)
        self.assert_called_once(mock_exit_function)

    def assert_called_once(self, function):
        self.assertEquals(1, function.call_count)
