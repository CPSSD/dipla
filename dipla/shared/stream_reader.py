import time
from queue import Queue
from threading import Thread
from .logutils import get_logger
from .continuous_stream_poller import ContinuousStreamPoller


class StreamReader(object):

    def __init__(self, continuous_stream_poller):
        self._logger = get_logger(__name__)
        self._stream_poller = continuous_stream_poller
        self._stream_queue = continuous_stream_poller._queue
        self._reading = False

    def open(self):
        self._logger.debug("StreamReader: about to open.")
        self._running = True
        self._stream_poller.start()
        self._logger.debug("StreamReader: opened.")

    def read_line_without_waiting(self):
        self._logger.debug("StreamReader: about to read without waiting.")
        self._reading = True
        pass
        self._reading = False
        self._logger.debug("StreamReader: finished read without waiting.")

    def read_line_with_waiting(self):
        self._logger.debug("StreamReader: about to read with waiting.")
        self._reading = True
        while self._running:
            if not self._stream_queue.empty():
                break
            self._logger.debug("StreamReader: stream queue is empty." +
                               "Sleeping for 0.1s before retrying...")
            time.sleep(0.1)
        self._reading = False
        self._logger.debug("StreamReader: finished read with waiting.")

    def close(self):
        self._logger.debug("StreamReader: about to close...")
        self._stream_poller.stop()
        self._running = False
        self._logger.debug("StreamReader: closed.")

    def currently_reading(self):
        return self._reading
