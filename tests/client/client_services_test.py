import os
from unittest import TestCase
from dipla.client.command_line_binary_runner import CommandLineBinaryRunner
from dipla.client.client_services import BinaryRunnerService
from dipla.client.client_services import BinaryReceiverService


class BinaryRunnerServiceTest(TestCase):

    def test_that_binary_runner_receives_arguments_through_service(self):
        self.given_sample_json_data()
        self.given_a_binary_runner_service()
        self.when_the_service_is_executed()
        self.then_the_binary_runner_will_receive_the_correct_arguments()
        self.and_the_binary_runner_will_not_have_received_invalid_arguments()

    def given_sample_json_data(self):
        self.json_data = {
            'task_uid': 'bar',
            'task_instructions': 'foo',
            'arguments': [[1, 2, 3]]
        }

    def given_a_binary_runner_service(self):
        mock_client = DummyClient()
        self.path_that_should_be_run = 'test_path'
        mock_client.binary_paths = {'foo': self.path_that_should_be_run}
        self.mock_binary_runner = MockBinaryRunner()
        self.service = BinaryRunnerService(mock_client,
                                           self.mock_binary_runner)

    def when_the_service_is_executed(self):
        self.service.execute(self.json_data)

    def then_the_binary_runner_will_receive_the_correct_arguments(self):
        correct_filepath = self.path_that_should_be_run
        correct_arguments = self.json_data['arguments']
        runner = self.mock_binary_runner
        self.assertTrue(runner.received(correct_filepath, correct_arguments))

    def and_the_binary_runner_will_not_have_received_invalid_arguments(self):
        runner = self.mock_binary_runner
        self.assertFalse(runner.received("incorrect_param", "incorrect_param"))


class BinaryReceiverServiceTest(TestCase):

    def setUp(self):
        self.message = b"banana"
        self.base_filepath = "tmp_"
        self.binary_name = "add"
        self.json_data = {"base64_binaries": {"add": "YmFuYW5h"}}
        self.service = BinaryReceiverService(DummyClient(),
                                             base_filepath=self.base_filepath)

    def test_that_receiver_decodes_and_saves_to_file(self):
        self.service.execute(self.json_data)
        with open(self.base_filepath + self.binary_name, 'rb') as filereader:
            data = filereader.read()
            self.assertEqual(self.message, data)

    def tearDown(self):
        os.remove(self.base_filepath + self.binary_name)


class DummyClient:
    pass


class MockBinaryRunner(CommandLineBinaryRunner):

    def run(self, filepath, arguments):
        self.filepath = filepath
        self.arguments = arguments

    def received(self, filepath, arguments):
        filepaths_match = self.filepath == filepath
        arguments_match = self.arguments == arguments
        return filepaths_match and arguments_match
