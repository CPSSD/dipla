from unittest import TestCase
from dipla.client.command_line_binary_runner import CommandLineBinaryRunner
from dipla.client.client_services import BinaryRunnerService


class BinaryRunnerServiceTest(TestCase):

    def test_that_binary_runner_receives_arguments_through_service(self):
        self.given_sample_json_data()
        self.given_a_binary_runner_service()
        self.when_the_service_is_executed()
        self.then_the_binary_runner_will_receive_the_correct_arguments()
        self.and_the_binary_runner_will_not_have_received_invalid_arguments()

    def given_sample_json_data(self):
        self.json_data = {
            "filepath": "foo",
            "arguments": "bar"
        }

    def given_a_binary_runner_service(self):
        self.mock_binary_runner = MockBinaryRunner()
        self.service = BinaryRunnerService(self.mock_binary_runner)

    def when_the_service_is_executed(self):
        self.service.execute(self.json_data)

    def then_the_binary_runner_will_receive_the_correct_arguments(self):
        correct_filepath = self.json_data["filepath"]
        correct_arguments = self.json_data["arguments"]
        runner = self.mock_binary_runner
        self.assertTrue(runner.received(correct_filepath, correct_arguments))

    def and_the_binary_runner_will_not_have_received_invalid_arguments(self):
        runner = self.mock_binary_runner
        self.assertFalse(runner.received("incorrect_param", "incorrect_param"))


class MockBinaryRunner(CommandLineBinaryRunner):

    def run(self, filepath, arguments):
        self.filepath = filepath
        self.arguments = arguments

    def received(self, filepath, arguments):
        filepaths_match = self.filepath == filepath
        arguments_match = self.arguments == arguments
        return filepaths_match and arguments_match
