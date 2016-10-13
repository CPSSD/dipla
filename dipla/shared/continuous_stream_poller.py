import time
from queue import Queue
from threading import Thread
from threading import Event
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
        self._stop_request = Event()

    # Override
    def run(self):
        self._logger.debug("ContinuousStreamPoller: about to run...")
        while not self._stop_request.isSet():
            self._read_from_stream()
            self._push_result_onto_queue()
            self._sleep_for_interval()

    # Override
    def join(self, timeout=None):
        self._logger.debug("ContinuousStreamReader: about to join thread...")
        self._stop_request.set()
        super().join(timeout)


    def _read_from_stream(self):
        self._logger.debug("ContinuousStreamPoller is about to read from stream...")
        self._line = self._stream.readline().strip()
        self._logger.debug("ContinuousStreamPoller has finished reading from stream.")

    def _push_result_onto_queue(self):
        if self._line:
            self._logger.debug("ContinuousStreamPoller is appending %s onto queue." % self._line)
            self._queue.put(self._line)

    def _sleep_for_interval(self):
        time.sleep(self._interval)

