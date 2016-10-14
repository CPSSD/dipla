from subprocess import Popen, PIPE
from ..shared.logutils import get_logger
import os


class BinaryRunner(object):

    def __init__(self):
        self._logger = get_logger(__name__)
        self._process = None
        self._running = False

    def run(self, command):
        arguments = command.split(" ")
        filepath = arguments[0]
        self._logger.debug("BinaryRunner: about to run binary at '%s'" % filepath)
        if not os.path.exists(filepath):
            raise FileNotFoundError
        else:
            self._process = Popen(arguments, shell=False, stdin=PIPE, stdout=PIPE)
            self._running = True

    def send_stdin(self, message):
        self._process.stdin.write(message.encode("utf-8"))
        self._process.stdin.flush()

    def is_running(self):
        
#        p = self._process
#        print(p.stdout.read())
#        print(p.poll())


        self.running = self._process.poll() == None
        return self._running
