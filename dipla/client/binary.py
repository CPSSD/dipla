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
        self._logger.debug("BinaryRunner: about to run binary with args " +
                           "{}".format(arguments))
        filepath = arguments[0]
        if not os.path.exists(filepath):
            raise FileNotFoundError
        else:
            self._process = Popen(command, shell=True, stdin=PIPE, stdout=PIPE)
            #self._stdout_reader = StreamReader(self._process.stdout)
            #self._stdout_reader.open()
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
        self._logger.debug("BinaryRunner: checking if binary is running...")
        poll_result = self._process.poll()
        self._running = poll_result == None
        self._logger.debug("BinaryRunner: return code of binary is {}".format(self._process.returncode))
        self._logger.debug("BinaryRunner: poll_result is {}".format(poll_result))
        return self._running
