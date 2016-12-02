from unittest import TestCase
from dipla.environment import PROJECT_DIRECTORY
from dipla.client.command_line_binary_runner import CommandLineBinaryRunner


class CommandLineBinaryRunnerTest(TestCase):

    def setUp(self):
        self.filepath = ""
        self.arguments_order = []
        self.arguments_values = {}

    def test_that_exception_is_thrown_when_binary_doesnt_exist(self):
        self.given_a_non_existent_binary()
        self.when_attempting_to_run_binary()
        self.then_a_FileNotFoundError_will_be_thrown()

    def test_that_no_exception_is_thrown_when_binary_exists(self):
        self.given_an_existing_binary()
        self.when_attempting_to_run_binary()
        self.then_no_exceptions_will_be_thrown()

    def test_that_binary_produces_valid_output(self):
        self.given_a_sums_binary()
        self.given_summing("3", "5")
        self.when_the_binary_is_run()
        self.then_the_result_will_be(["8]")

    def test_that_binary_produces_valid_output_with_more_input(self):
        self.given_a_sums_binary()
        self.given_summing("1", "2")
        self.when_the_binary_is_run()
        self.then_the_result_will_be(["3"])

    def given_a_non_existent_binary(self):
        self.filepath = "/dont_exist/binary"

    def given_an_existing_binary(self):
        self.given_a_sums_binary()

    def given_a_sums_binary(self):
        self.filepath = PROJECT_DIRECTORY + \
            "tests/example_binaries/sums/sums.exe"

    def given_summing(self, num_a, num_b):
        self.arguments_order = ["a", "b"]
        self.arguments_values = {
            "a": [num_a],
            "b": [num_b]
        }

    def when_attempting_to_run_binary(self):
        pass

    def when_the_binary_is_run(self):
        self.runner = CommandLineBinaryRunner()
        self.result = self.runner.run(
            self.filepath, self.arguments_order, self.arguments_values)

    def then_a_FileNotFoundError_will_be_thrown(self):
        with self.assertRaises(FileNotFoundError):
            self.when_the_binary_is_run()

    def then_no_exceptions_will_be_thrown(self):
        self.when_the_binary_is_run()

    def then_the_result_will_be(self, expected):
        self.assertEqual(expected, self.result)


if __name__ == "__main__":
    unittest.main()
