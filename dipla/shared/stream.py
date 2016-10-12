import time
from queue import Queue
from threading import Thread
from nonblock import nonblock_read
from .logutils import get_logger


"""
This class continually reads from a text stream on its own thread.
It pushes each line of text it discovers to a queue.

Just specify...
1. The stream to read from.
2. The queue to write to.
3. (Optional) The time interval (in seconds) between each read operation.
"""


class TextCollector(Thread):

    def __init__(self, stream, queue, interval=0.005):
        super().__init__()
        self._logger = get_logger(__name__)
        self._stream = stream
        self._queue = queue
        self._interval = interval
        self._running = False

    def run(self):
        self._logger.debug("Started running TextCollector.")
        self._running = True
        while self._running:
            self._read_from_stream()
            self._push_result_onto_queue()
            self._sleep()

    def _read_from_stream(self):
        self._logger.debug("TextCollector is about to read from stream...")
        # self._stream_content = nonblock_read(self._stream)
        self._stream_content = self._stream.readline()
        self._logger.debug("TextCollector has finished reading from stream.")

    def _push_result_onto_queue(self):
        for line in self._stream_content.split("\n"):
            if line:
                self._logger.debug("TextCollector is appending %s onto queue." % line)
                self._queue.put(line)

    def _sleep(self):
        time.sleep(self._interval)

    def stop(self):
        self._logger.debug("TextCollector is has stopped.")
        self._running = False
