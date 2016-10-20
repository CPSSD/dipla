from subprocess import *
from os.path import isfile


class CommandLineBinaryRunner(object):

    def run(self, filepath, arguments):
        self._filepath = filepath
        self._arguments = arguments
        if self._binary_exists():
            return self._run_binary()
        else:
            raise FileNotFoundError

    def _binary_exists(self):
        return isfile(self._filepath)

    def _run_binary(self):
        process = Popen(
            args=[self._filepath] + self._arguments,
            stdin=PIPE,
            stdout=PIPE,
            stderr=PIPE,
            shell=False
        )
        return process.communicate(None)[0].strip().decode()
