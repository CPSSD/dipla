from subprocess import Popen, PIPE
from ..shared.logutils import get_logger
from ..shared.stream_reader import StreamReader
from ..shared.stream_writer import StreamWriter
import os
import shlex


class BinaryRunner(object):

    def __init__(self):
        self._logger = get_logger(__name__)
        self._process = None
        self._stdout_reader = None
        self._running = False

    def run(self, command):
        arguments = shlex.split(command)
        log_message = "BinaryRunner: about to run binary with args {}"
        self._logger.debug(log_message.format(arguments))
        filepath = arguments[0]
        if not os.path.exists(filepath):
            raise FileNotFoundError
        else:
            self._process = Popen(command, shell=True, stdin=PIPE, stdout=PIPE)
#            self._stdout_reader = StreamReader(self._process.stdout)
#            self._stdout_reader.open()
            self._running = True

    def send_stdin(self, message):
        message = message.encode("utf-8")
        self._logger.debug("BinaryRunner: sending '%s' to stdin" % message)
        stream_writer = StreamWriter(self._process.stdin, message)
        stream_writer.start()

    def read_stdout_without_waiting(self, message):
        output = self._stdout_reader.read_line_without_waiting()
        return output

    def read_stdout_with_waiting(self, message):
        output = self._stdout_reader.read_line_with_waiting()
        return output

    def is_running(self):
        log_message = "BinaryRunner: checking if binary is running..."
        log_return_code = "BinaryRunner: return code of binary is {}"
        log_poll_result = "BinaryRunner: poll_result is {}"
        self._logger.debug(log_message)
        poll_result = self._process.poll()
        self._running = poll_result is None
        self._logger.debug(log_return_code.format(self._process.returncode))
        self._logger.debug(log_poll_result.format(poll_result))
        return self._running
