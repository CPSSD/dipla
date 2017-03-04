import unittest
from unittest.mock import Mock
from dipla.server.server_services import ServerServices, ServiceParams, ServiceError
from dipla.server.server import BinaryManager
from dipla.server.worker_group import Worker, WorkerGroup
from dipla.shared import statistics
from dipla.shared.error_codes import ErrorCodes


class WorkerGroupTest(unittest.TestCase):

    def setUp(self):
        self.server_services = ServerServices(BinaryManager())

        mock_server = Mock()
        mock_server.verify_inputs = {}

        stats = {
            "num_total_workers": 0,
            "num_idle_workers": 0
        }
        stat_updater = statistics.StatisticsUpdater(stats)
        mock_server.worker_group = WorkerGroup(stat_updater)
        mock_server.password = None
        mock_server.min_worker_correctness = 0.99
        self.mock_server = mock_server

        foo_worker = Worker("foo_worker", None, quality=1)
        foo_worker.correctness_score = 1
        mock_server.worker_group.add_worker(foo_worker)
        self.foo_worker = foo_worker

        # Lease the mock worker, like it would be in the real situation
        mock_server.worker_group.lease_worker()

    def test_handle_get_binaries_throws_error_if_no_binary(self):
        service = self.server_services.get_service('get_binaries')
        self.foo_worker._quality = None
        message = {
          'quality': 1,
          'platform': 'non-existant'
        }

        with self.assertRaises(ServiceError) as context:
            service(message, ServiceParams(self.mock_server, self.foo_worker))
        self.assertEquals(
            ErrorCodes.invalid_binary_key, context.exception.code)

    def test_handle_get_binaries_throws_error_if_no_password(self):
        service = self.server_services.get_service('get_binaries')
        self.foo_worker._quality = None
        self.mock_server.password = "FOOpassword"
        message = {
          'quality': 1,
          'platform': 'non-existant'
        }

        with self.assertRaises(ServiceError) as context:
            service(message, ServiceParams(self.mock_server, self.foo_worker))
        self.assertEquals(ErrorCodes.password_required, context.exception.code)

    def test_handle_get_binaries_throws_error_if_wrong_password(self):
        service = self.server_services.get_service('get_binaries')
        self.foo_worker._quality = None
        self.mock_server.password = "FOOpassword"
        message = {
          'quality': 1,
          'platform': 'non-existant',
          'password': 'BARpassword'
        }

        with self.assertRaises(ServiceError) as context:
            service(message, ServiceParams(self.mock_server, self.foo_worker))
        self.assertEquals(ErrorCodes.invalid_password, context.exception.code)

    def test_handle_binary_received_throws_error_if_user_id_taken(self):
        service = self.server_services.get_service('binaries_received')

        self.mock_server.worker_group.add_worker(
            Worker("foo", None, quality=1))
        with self.assertRaises(ServiceError) as context:
            service(None, ServiceParams(self.mock_server, self.foo_worker))
        self.assertEquals(
            ErrorCodes.user_id_already_taken, context.exception.code)

    def test_handle_client_result_sends_verify_message(self):
        service = self.server_services.get_service('client_result')
        message = {
            "task_uid": "bar_task",
            "results": ["foo", "bar", "nod"],
        }

        expected_socket = Mock()

        self.mock_server.worker_group.add_worker(
            Worker("bar_worker", expected_socket, quality=1))
        self.mock_server.verify_inputs = {
            "foo_worker-bar_task": {
                "task_instructions": "foobar",
                "inputs": [1, 2, 3, 4],
            }
        }

        service(message, ServiceParams(self.mock_server, self.foo_worker))
        self.mock_server.send.assert_called_once_with(
            expected_socket,
            "verify_inputs",
            {
                "task_uid": "bar_task",
                "task_instructions": "foobar",
                "arguments": [1, 2, 3, 4]
            })

    def test_handle_client_result_verify_wont_crash_if_no_other_workers(self):
        service = self.server_services.get_service('client_result')
        message = {
            "task_uid": "bar_task",
            "results": ["foo", "bar", "nod"],
        }

        service(message, ServiceParams(self.mock_server, self.foo_worker))

    def test_handle_verify_inputs_detect_mismatch(self):
        service = self.server_services.get_service('verify_inputs_result')

        self.mock_server.verify_inputs = {
            "foo_worker-foo_task": {
                "original_worker_uid": "bar_worker",
                "results": [3, 2, 1]
            }
        }

        message = {
            "task_uid": "foo_task",
            "results": [1, 2, 3]
        }
        bar_worker = Worker("bar_worker", None, quality=1)
        self.mock_server.worker_group.add_worker(bar_worker)

        service(message, ServiceParams(self.mock_server, self.foo_worker))
        self.assertFalse(
            "bar_worker" in self.mock_server.worker_group.worker_uids())

    def test_handle_verify_inputs_wont_remove_worker_above_min_score(self):
        service = self.server_services.get_service('verify_inputs_result')

        self.mock_server.verify_inputs = {
            "foo_worker-foo_task": {
                "original_worker_uid": "bar_worker",
                "results": [3, 2, 1]
            }
        }

        message = {
            "task_uid": "foo_task",
            "results": [1, 2, 3]
        }

        self.mock_server.min_worker_correctness = 0.90

        bar_worker = Worker("bar_worker", None, quality=1)
        self.mock_server.worker_group.add_worker(bar_worker)

        service(message, ServiceParams(self.mock_server, self.foo_worker))
        self.assertTrue(
            "bar_worker" in self.mock_server.worker_group.worker_uids())

    def test_handle_verify_inputs_returns_worker_on_verification(self):
        service = self.server_services.get_service('verify_inputs_result')

        self.mock_server.verify_inputs = {
            "foo_worker-foo_task": {
                "original_worker_uid": "bar_worker",
                "results": [3, 2, 1]
            }
        }

        message = {
            "task_uid": "foo_task",
            "results": [3, 2, 1]
        }
        bar_worker = Worker("bar_worker", None, quality=1)
        self.mock_server.worker_group.add_worker(bar_worker)

        service(message, ServiceParams(self.mock_server, self.foo_worker))
        self.assertTrue(
            "bar_worker" in self.mock_server.worker_group.worker_uids())
