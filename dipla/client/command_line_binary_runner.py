import json
from logging import getLogger
from subprocess import Popen, PIPE
from os.path import isfile


class CommandLineBinaryRunner(object):

    def __init__(self):
        self._logger = getLogger(__name__)

    def run(self, file_path, arguments):
        if self._binary_exists(file_path):
            # Run at least once. If arguments were provided, work out
            # how many sets of inputs were provided
            expected_runs = 1
            if len(arguments) > 0:
                expected_runs = len(arguments[0])
            # Check all the rest of the arguments have the same number of
            # values as the first
            for argument_values in arguments[1:]:
                if not len(argument_values) == expected_runs:
                    raise InvalidArgumentsError(
                        "Non-uniform number of values supplied to run binary")
            results = []
            for input_index in range(expected_runs):
                # Collect the i'th value for each argument
                next_values = []
                for argument_values in arguments:
                    next_values.append(
                        argument_values[input_index])
                # Run the next set of input values
                results.append(self._run_binary(file_path, next_values))
            return results
        else:
            error_message = "Could not locate binary: '{}'".format(file_path)
            self._logger.error(error_message)
            raise FileNotFoundError(error_message)

    def _binary_exists(self, file_path):
        return isfile(file_path)

    def _run_binary(self, file_path, arguments):
        self._logger.debug("About to run binary %s" % file_path)
        process = Popen(
            args=[file_path] + [json.dumps(arguments)],
            stdin=PIPE,
            stdout=PIPE,
            stderr=PIPE,
            shell=False
        )
        process_output = process.communicate(None)[0]
        cleaned_output = process_output.strip().decode()
        if cleaned_output:
            return json.loads(cleaned_output)['data']
        return ''


class InvalidArgumentsError(Exception):
    """
    An exception raised when the invalid arguments are supplied for
    running a binary
    """
    pass
