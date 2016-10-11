import unittest
import os
from dipla.client.binary import BinaryRunner
from dipla.environment import PROJECT_DIRECTORY


class BinaryRunnerTest(unittest.TestCase):

    def test_that_error_is_raised_when_running_non_existent_binary(self):
        self.given_the_binary("~/fake_binary")
        self.then_running_the_binary_will_raise_a_FileNotFoundError()

    def test_that_no_error_is_raised_when_running_existing_binary(self):
        self.given_the_binary(PROJECT_DIRECTORY + "tests/example_binary/builds/example_binary_ARM")
        self.then_running_the_binary_will_not_raise_any_exceptions()

    def given_the_binary(self, filepath):
        self.filepath = filepath

    def when_the_binary_is_run(self):
        self.binary_runner = BinaryRunner()
        self.binary_runner.run(self.filepath)

    def then_running_the_binary_will_raise_a_FileNotFoundError(self):
        self.assertRaises(FileNotFoundError, self.when_the_binary_is_run)

    def then_running_the_binary_will_not_raise_any_exceptions(self):
        try:
            self.when_the_binary_is_run()
        except:
            self.fail("Running the binary raised an exception when it shouldn't have")

