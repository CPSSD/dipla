from logging import getLogger
from subprocess import Popen, PIPE
from os.path import isfile


class CommandLineBinaryRunner(object):

    def __init__(self):
        self._logger = getLogger(__name__)

    def run(self, filepath, arguments):
        if self._binary_exists(filepath):
            return self._run_binary(filepath, arguments)
        else:
            error_message = "Could not locate binary: '{}'".format(filepath)
            self._logger.error(error_message)
            raise FileNotFoundError(error_message)

    def _binary_exists(self, filepath):
        return isfile(filepath)

    def _run_binary(self, filepath, arguments):
        self._logger.debug("About to run binary %s" % filepath)
        process = Popen(
            args=[filepath] + arguments,
            stdin=PIPE,
            stdout=PIPE,
            stderr=PIPE,
            shell=False
        )
        process_output = process.communicate(None)[0]
        return process_output.strip().decode()
