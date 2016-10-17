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
        command = [self._filepath] + self._arguments
        process = Popen(
            command,
            shell=False,
            stdin=PIPE,
            stdout=PIPE,
            stderr=PIPE
        )
        output = process.communicate(None)[0].strip().decode()
        return output
