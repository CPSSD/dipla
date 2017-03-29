import unittest
from unittest.mock import call, Mock
from dipla.server.result_verifier import ResultVerifier
from dipla.server.server import ServerServices, ServiceParams, ServiceError
from dipla.server.server import BinaryManager
from dipla.server.worker_group import Worker, WorkerGroup
from dipla.shared import statistics
from dipla.shared.error_codes import ErrorCodes


class ServerServicesTest(unittest.TestCase):

    def setUp(self):

        mock_server = Mock()
        mock_server.verify_inputs = {}
        mock_server.result_verifier = ResultVerifier()

        stats = {
            "num_total_workers": 0,
            "num_idle_workers": 0,
            "num_results_from_clients": 0
        }
        stat_updater = statistics.StatisticsUpdater(stats)
        self.server_services = ServerServices(BinaryManager(),
                                              stat_updater)
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

    def test_handle_client_result_runs_verifier(self):
        verify_inputs = []
        verify_outputs = []

        def verify_bar(i, o):
            verify_inputs.append(i[0])
            verify_outputs.append(o)
            print("returing true")
            return True
        self.mock_server.result_verifier.add_verifier('bar', verify_bar)

        test_inputs = [1, 2, 3]
        test_outputs = [-1, -2, -3]

        self.foo_worker.current_task_instr = 'bar'
        self.foo_worker.last_inputs = [test_inputs]

        message = {
            'task_uid': 'bar_task_uid',
            'results': test_outputs,
        }
        service = self.server_services.get_service('client_result')
        service(message, ServiceParams(self.mock_server, self.foo_worker))

        self.assertEquals(test_inputs, verify_inputs)
        self.assertEquals(test_outputs, verify_outputs)

    def test_handle_client_result_verification_affects_worker_score(self):
        self.mock_server.result_verifier.add_verifier('a', lambda a, b: False)
        self.foo_worker.current_task_instr = 'a'
        self.foo_worker.last_inputs = [[1, 2, 3]]
        self.foo_worker.correctness_score = 1
        message = {
            'task_uid': 'a_task_uid',
            'results': [-1, -2, -3],
        }
        service = self.server_services.get_service('client_result')
        service(message, ServiceParams(self.mock_server, self.foo_worker))

        self.assertLess(self.foo_worker.correctness_score, 1)

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

    def test_handle_client_results_calls_signal_function(self):
        service = self.server_services.get_service("client_result")

        message = {
            "task_uid": "foo_task",
            "results": [1, 2, 3],
            "signals": {"FOOBAR": [[[0, 0], [3, 3]]]}
        }

        mock_task = Mock()
        self.mock_server.task_queue.get_task.return_value = mock_task
        mock_task.signals = {"FOOBAR": Mock()}

        service(message, ServiceParams(self.mock_server, self.foo_worker))

        mock_task.signals["FOOBAR"].assert_called_with(
            "foo_task", [[0, 0], [3, 3]])

    def test_handle_client_result_does_not_add_invalid_results(self):
        service = self.server_services.get_service("client_result")

        message = {
            "task_uid": "foo_id",
            "results": [1, 2, 3]
        }

        service(message, ServiceParams(self.mock_server, self.foo_worker))

        verify = False

        def verify_every_second_value(task_instructions, input_value, result):
            verify = not verify
            print("Returning", verify)
            return verify

        original_verifier = self.mock_server.result_verifier
        self.mock_server.result_verifier.check_output =\
            verify_every_second_value
        self.mock_server.task_queue.add_result.assert_has_calls(
            [call("foo_id", 1), call("foo_id", 2), call("foo_id", 3)])
        self.mock_server_result_verifier = original_verifier
