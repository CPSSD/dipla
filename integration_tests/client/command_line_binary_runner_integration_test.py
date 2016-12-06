from unittest import TestCase
from dipla.environment import PROJECT_DIRECTORY
from dipla.client.command_line_binary_runner import CommandLineBinaryRunner


class CommandLineBinaryRunnerIntegrationTest(TestCase):

    def setUp(self):
        self.filepath = ""
        self.arguments = []

    def test_that_exception_is_thrown_when_binary_doesnt_exist(self):
        self.given_a_non_existent_binary()
        self.when_attempting_to_run_binary()
        self.then_a_FileNotFoundError_will_be_thrown()

    def test_that_no_exception_is_thrown_when_binary_exists(self):
        self.given_an_existing_binary()
        self.when_attempting_to_run_binary()
        self.then_no_exceptions_will_be_thrown()

    def test_that_binary_produces_valid_output(self):
        self.given_a_web_count_binary()
        self.given_using_a_github_resource()
        self.given_searching_for("word")
        self.when_the_binary_is_run()
        self.then_the_result_will_be("3")

    def test_that_binary_produces_valid_output_with_another_url(self):
        self.given_a_web_count_binary()
        self.given_using_another_github_resource()
        self.given_searching_for("BLARG")
        self.when_the_binary_is_run()
        self.then_the_result_will_be("4")

    def given_a_non_existent_binary(self):
        self.filepath = "/dont_exist/binary"

    def given_an_existing_binary(self):
        self.given_a_web_count_binary()

    def given_a_web_count_binary(self):
        self.filepath = PROJECT_DIRECTORY + \
                        "tests/example_binaries/" + \
                        "web_count/web_count.exe"

    def given_using_a_github_resource(self):
        resource_url = github_resource("master/txt/word_count.txt")
        self.arguments.append(resource_url)

    def given_using_another_github_resource(self):
        resource_url = github_resource("master/txt/word_count_again.txt")
        self.arguments.append(resource_url)

    def given_searching_for(self, word):
        self.arguments.append(word)

    def when_attempting_to_run_binary(self):
        pass

    def when_the_binary_is_run(self):
        self.runner = CommandLineBinaryRunner()
        self.result = self.runner.run(self.filepath, self.arguments)

    def then_a_FileNotFoundError_will_be_thrown(self):
        with self.assertRaises(FileNotFoundError):
            self.when_the_binary_is_run()

    def then_no_exceptions_will_be_thrown(self):
        self.when_the_binary_is_run()

    def then_the_result_will_be(self, expected):
        self.assertEqual(expected, self.result)


def github_resource(resource_path):
    repo_url = "https://raw.githubusercontent.com/byxor/resources-for-testing/"
    return repo_url + resource_path
