import time
from queue import Queue
from threading import Thread
from threading import Event
from nonblock import nonblock_read
from .logutils import get_logger
from .continuous_stream_poller import ContinuousStreamPoller


class StreamReader(object):

    def __init__(self, stream):
        self._logger = get_logger(__name__)
        self._stream = stream 
        self._queue = Queue()
        self._stream_poller = ContinuousStreamPoller(self._stream, self._queue)
        self._reading = False
        self._stop_request = Event()

    def open(self):
        self._logger.debug("StreamReader: about to open...")
        self._stream_poller.start()
       
    def read_line_without_waiting(self):
        self._reading = True
        self._reading = False

    def read_line_with_waiting(self):
        self._reading = True
        start_time = time.time()
        while not self._stop_request.isSet():
            if not self._queue.empty():
                self._reading = False
                return


    def close(self):
        self._logger.debug("StreamReader: about to close...")
        self._stop_request.set()
        self._stream_poller.join()
