import time
from queue import Queue
from threading import Thread
from nonblock import nonblock_read
from .logutils import get_logger


#
# This class continually reads from a text stream on its own thread.
# It pushes each line of text it discovers to a queue.
# 
# Just specify...
# 1. The stream to read from.
# 2. The queue to write to.
# 3. (Optional) The time interval (in seconds) between each read operation."
#
class ContinuousStreamPoller(Thread):

    def __init__(self, stream, queue, interval=0.005):
        super().__init__()
        self._logger = get_logger(__name__)
        self._stream = stream
        self._queue = queue
        self._interval = interval
        self._running = False
        self._reading = False

    def run(self):
        self._logger.debug("Started running ContinuousStreamPoller.")
        self._running = True
        while self._running:
            self._read_from_stream()
            self._push_result_onto_queue()
            self._sleep()

    def currently_running(self):
        return self._running

    def currently_reading(self):
        return self._reading

    def _read_from_stream(self):
        self._logger.debug("ContinuousStreamPoller is about to read from stream...")
        self._reading = True
        self._line = self._stream.readline().strip()
        self._reading = False
        self._logger.debug("ContinuousStreamPoller has finished reading from stream.")

    def _push_result_onto_queue(self):
        if self._line:
            self._logger.debug("ContinuousStreamPoller is appending %s onto queue." % self._line)
            self._queue.put(self._line)

    def _sleep(self):
        time.sleep(self._interval)

    def stop(self):
        self._logger.debug("ContinuousStreamPoller has stopped.")
        self._running = False
        self.join()
