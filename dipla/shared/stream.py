import time
from queue import Queue
from threading import Thread


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
        self._stream = stream
        self._queue = queue
        self._interval = interval
        self._running = False

    def run(self):
        self._running = True
        while self._running:
            self._read_from_stream()
            self._push_result_onto_queue()
            self._sleep()

    def _read_from_stream(self):
        self._text = self._stream.readline().strip()

    def _push_result_onto_queue(self):
        if self._text:
            self._queue.put(self._text)

    def _sleep(self):
        time.sleep(self._interval)

    def stop(self):
        self._running = False
