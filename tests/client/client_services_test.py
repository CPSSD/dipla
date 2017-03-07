import functools
import os
from unittest.mock import MagicMock
from collections import namedtuple
from unittest import TestCase
from dipla.client.client_services import BinaryRunnerService
from dipla.client.client_services import BinaryReceiverService
from dipla.shared.services import ServiceError
from dipla.shared.error_codes import ErrorCodes


class BinaryRunnerServiceTest(TestCase):
    def setUp(self):
        self.binary_runner = namedtuple('MockObject', 'run')
        self.binary_runner.run = MagicMock()

    def test_binary_runner_is_called(self):
        self.given_the_binary_runner_will_return("ARBITRARY")
        self.given_the_binary_paths({"foo": "bar"})
        self.given_a_binary_runner_service()
        self.when_the_service_is_executed_with({
            'task_uid': 'baz',
            'task_instructions': 'foo',
            'arguments': [[1, 2, 3]]
        })
        self.then_the_binary_runner_will_execute_with(['bar', [[1, 2, 3]]])
        self.then_the_result_is({
            'label': 'binary_result',
            'data': {
                'task_uid': 'baz',
                'results': 'ARBITRARY'
            }
        })

    def test_binary_runner_throws_error_if_no_binaries(self):
        self.given_the_binary_paths({})
        self.given_a_binary_runner_service()
        self.when_attempting_to_execute_service_with({
            'task_instructions': None
        })
        self.then_a_ServiceError_is_thrown_with(ErrorCodes.no_binaries_present)

    def test_binary_runner_throws_error_if_binary_missing(self):
        self.given_the_binary_paths({"foo": "", "bar": ""})
        self.given_a_binary_runner_service()
        self.when_attempting_to_execute_service_with({
            'task_instructions': 'baz'
        })
        self.then_a_ServiceError_is_thrown_with(ErrorCodes.invalid_binary_key)

    def given_the_binary_runner_will_return(self, value):
        self.binary_runner.run = MagicMock(return_value=value)

    def given_the_binary_paths(self, binary_paths):
        self.binary_paths = binary_paths

    def given_a_binary_runner_service(self):
        self.service = BinaryRunnerService(self.binary_paths,
                                           self.binary_runner)

    def when_the_service_is_executed_with(self, data):
        self.result = self.service.execute(data)

    def then_the_binary_runner_will_execute_with(self, data):
        self.binary_runner.run.assert_called_with(data[0], data[1])

    def then_a_ServiceError_is_thrown_with(self, error_code):
        with self.assertRaises(ServiceError) as context:
            self.operation()
        self.assertEquals(error_code, context.exception.code)

    def when_attempting_to_execute_service_with(self, data):
        self.operation = functools.partial(self.service.execute, data)

    def then_the_result_is(self, result):
        self.assertEquals(result, self.result)


class BinaryReceiverServiceTest(TestCase):
    def setUp(self):
        self.message = b"banana"
        self.base_file_path = "tmp_"
        self.binary_name = "add"
        self.json_data = {"base64_binaries": {"add": "YmFuYW5h"}}
        self.binary_paths = {}
        self.service = BinaryReceiverService(self.base_file_path,
                                             self.binary_paths)

    def test_that_receiver_decodes_and_saves_to_file(self):
        self.service.execute(self.json_data)
        with open(self.base_file_path + self.binary_name, 'rb') as file_reader:
            data = file_reader.read()
            self.assertEqual(self.message, data)

    def tearDown(self):
        os.remove(self.base_file_path + self.binary_name)


class DummyClient:
    pass
