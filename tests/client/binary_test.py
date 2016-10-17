import unittest
import time
import os
from dipla.client.binary import BinaryRunner
from dipla.environment import PROJECT_DIRECTORY


class BinaryRunnerTest(unittest.TestCase):

    EXAMPLE_BINARY_PATH = PROJECT_DIRECTORY + "tests/example_binaries/dynamic_web_count/builds/ARM"

    def test_that_error_is_raised_when_running_non_existent_binary(self):
        self.given_the_binary("~/fake_binary")
        self.then_running_the_binary_will_raise_a_FileNotFoundError()

    def test_that_no_error_is_raised_when_running_existing_binary(self):
        self.given_using_the_example_binary()
        self.then_running_the_binary_will_not_raise_any_exceptions()

#    def test_that_binary_stops_running_after_the_exit_command_is_given(self):
#        self.given_using_the_example_binary()
#        self.when_the_binary_is_run()
#        self.and_the_standard_input_is_injected("!")
#        self.and_we_wait_a_bit()
#        self.then_the_binary_will_not_be_running()

#    def test_that_binary_is_running_after_no_commands_have_been_given(self):
#        self.given_using_the_example_binary()
#        self.when_the_binary_is_run()
#        self.and_we_wait_a_bit()
#        self.then_the_binary_will_be_running()

#    def test_that_binary_is_running_after_an_arbitrary_command_has_been_given(self):
#        self.given_using_the_example_binary()
#        self.when_the_binary_is_run()
#        self.and_we_wait_a_bit()
#        self.and_the_standard_input_is_injected("arbitrary input")
#        self.and_we_wait_a_bit()
#        self.then_the_binary_will_be_running()

    def given_the_binary(self, filepath):
        self.filepath = filepath

    def given_using_the_example_binary(self):
        self.given_the_binary(BinaryRunnerTest.EXAMPLE_BINARY_PATH + " foo")

    def when_the_binary_is_run(self):
        self.binary_runner = BinaryRunner()
        self.binary_runner.run(self.filepath)

    def and_we_wait_a_bit(self):
        time.sleep(0.3)

    def and_the_standard_input_is_injected(self, command):
        self.binary_runner.send_stdin(command)

    def then_running_the_binary_will_raise_a_FileNotFoundError(self):
        self.assertRaises(FileNotFoundError, self.when_the_binary_is_run)

    def then_running_the_binary_will_not_raise_any_exceptions(self):
        try:
            self.when_the_binary_is_run()
        except:
            self.fail("Running the binary raised an exception" +
                      "when it shouldn't have")

    def then_the_binary_will_not_be_running(self):
        running = self.binary_runner.is_running()
        self.assertFalse(running)

    def then_the_binary_will_be_running(self):
        running = self.binary_runner.is_running()
        self.assertTrue(running)
