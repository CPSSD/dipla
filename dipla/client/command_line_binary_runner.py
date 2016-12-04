from logging import getLogger
from subprocess import Popen, PIPE
from os.path import isfile


class CommandLineBinaryRunner(object):

    def __init__(self):
        self._logger = getLogger(__name__)

    def run(self, filepath, arguments_order, arguments_values):
        if self._binary_exists(filepath):
            # Run at least once. If arguments were provided, work out
            # how many sets of inputs were provided
            expected_runs = 1
            if len(arguments_order) > 0:
                expected_runs = len(arguments_values[arguments_order[0]])
            # Check all the rest of the arguments have the same number of
            # values as the first
            for argument in arguments_order[1:]:
                if not len(arguments_values[argument]) == expected_runs:
                    raise InvalidArgumentsError(
                        "Non-uniform number of values supplied to run binary")

            results = []
            for input_index in range(expected_runs):
                # Collect the i'th value for each argument
                next_values = []
                for argument in arguments_order:
                    next_values.append(
                        arguments_values[argument][input_index])
                # Run the next set of input values
                results.append(self._run_binary(filepath, next_values))
            return results
        else:
            error_message = "Could not locate binary: '{}'".format(filepath)
            self._logger.error(error_message)
            raise FileNotFoundError(error_message)

    def _binary_exists(self, filepath):
        return isfile(filepath)

    def _run_binary(self, filepath, arguments):
        self._logger.debug("About to run binary %s" % filepath)
        process = Popen(
            args=[filepath] + [str(x) for x in arguments],
            stdin=PIPE,
            stdout=PIPE,
            stderr=PIPE,
            shell=False
        )
        process_output = process.communicate(None)[0]
        return process_output.strip().decode()


class InvalidArgumentsError(Exception):
    """
    An exception raised when the invalid arguments are supplied for
    running a binary
    """
    pass
