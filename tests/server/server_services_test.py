import unittest
from unittest.mock import Mock
from dipla.server.server import ServerServices, ServiceParams
from dipla.server.worker_group import Worker, WorkerGroup


class WorkerGroupTest(unittest.TestCase):

    def setUp(self):
        self.server_services = ServerServices(None)
        print("setUp called")

        mock_server = Mock()
        mock_server.verify_inputs = {}
        mock_server.worker_group = WorkerGroup()
        self.mock_server = mock_server

        mock_worker = Mock()
        mock_worker.uid = "foo"
        mock_server.worker_group.add_worker(mock_worker)
        self.mock_worker = mock_worker

        # Lease the mock worker, like it would be in the real situation
        mock_server.worker_group.lease_worker()

    def test_handle_client_result_sends_verify_message(self):
        service = self.server_services.get_service('client_result')
        message = {
            "task_uid": "bar",
            "results": ["foo", "bar", "nod"],
        }

        expected_socket = Mock()

        def mock_send(socket, label, data):
            self.assertEquals(expected_socket, socket)
            self.assertEquals("verify_inputs", label)
            self.assertEquals({
                    "task_uid": "bar",
                    "task_instructions": "foobar",
                    "arguments": [1, 2, 3, 4]
                }, data)
        self.mock_server.send = mock_send
        self.mock_server.worker_group.add_worker(
            Worker("bar", expected_socket))
        self.mock_server.verify_inputs = {
            "foo-bar": {
                "task_instructions": "foobar",
                "inputs": [1, 2, 3, 4],
            }}

        service(message, ServiceParams(self.mock_server, self.mock_worker))

    def test_handle_client_result_verify_wont_crash_if_no_other_workers(self):
        service = self.server_services.get_service('client_result')
        message = {
            "task_uid": "bar",
            "results": ["foo", "bar", "nod"],
        }

        service(message, ServiceParams(self.mock_server, self.mock_worker))
