from logging import getLogger
from subprocess import *
from os.path import isfile


class CommandLineBinaryRunner(object):

    def __init__(self):
        self._logger = getLogger(__name__)

    def run(self, filepath, arguments):
        if self._binary_exists(filepath):
            return self._run_binary(filepath, arguments)
        else:
            self._logger.error("Cannot run binary: %s not found" % filepath)
            raise FileNotFoundError

    def _binary_exists(self, filepath):
        return isfile(filepath)

    def _run_binary(self, filepath, arguments):
        process = Popen(
            args=[filepath] + arguments,
            stdin=PIPE,
            stdout=PIPE,
            stderr=PIPE,
            shell=False
        )
        return process.communicate(None)[0].strip().decode()
