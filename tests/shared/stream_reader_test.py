import time
from io import StringIO
from queue import Queue
from threading import Thread
from unittest import TestCase
from dipla.shared.continuous_stream_poller import ContinuousStreamPoller
from dipla.shared.stream_reader import StreamReader


class StreamReaderTest(TestCase):

#    def test_that_thread_does_not_get_blocked_when_reading_from_empty_stream_without_waiting(self):
#        self.given_reading_from_empty_stream()
#        self.when_we_read_without_waiting()
#        self.and_we_wait_a_bit()
#        self.then_the_operation_will_be_finished()

#    def test_that_thread_gets_blocked_when_reading_from_empty_stream_with_waiting(self):
#        self.given_reading_from_empty_stream()
#        self.when_we_read_with_waiting()
#        self.and_we_wait_a_bit()
#        self.then_the_operation_will_not_be_finished()

    def test_that_closing_stream_reader_which_is_reading_without_waiting_stops_internal_stream_poller(self):
        self.given_reading_from_empty_stream()
        self.when_we_read_without_waiting()
        self.and_we_close_the_stream_reader()
        self.and_we_wait_a_bit()
        self.then_the_internal_stream_poller_will_be_finished()

    def test_that_closing_stream_reader_which_is_reading_with_waiting_stops_internal_stream_poller(self):
        self.given_reading_from_empty_stream()
        self.when_we_read_with_waiting()
        self.and_we_close_the_stream_reader()
        self.and_we_wait_a_bit()
        self.then_the_internal_stream_poller_will_be_finished()

#    def test_that_thread_does_not_get_blocked_when_reading_from_populated_stream_with_waiting(self):
#        self.given_reading_from_populated_stream()
#        self.when_we_read_with_waiting()
#        self.and_we_wait_a_bit()
#        self.then_the_operation_will_be_finished()

    def given_reading_from_empty_stream(self):
        empty_stream = StringIO()
        self.given_reading_from(empty_stream)

    def given_reading_from_populated_stream(self):
        populated_stream = StringIO("CONTENT")
        self.given_reading_from(populated_stream)

    def given_reading_from(self, stream):
        empty_queue = Queue()
        stream_poller = ContinuousStreamPoller(stream, empty_queue)
        self.stream_reader = StreamReader(stream_poller)

    def when_we_read_without_waiting(self):
        self.operation = NonBlockingStreamReadOperation(self.stream_reader)
        self.operation.start()

    def when_we_read_with_waiting(self):
        self.operation = BlockingStreamReadOperation(self.stream_reader)
        self.operation.start()

    def and_we_close_the_stream_reader(self):
        self.stream_reader.close()

    def and_we_wait_a_bit(self):
        time.sleep(0.5)

    def then_the_operation_will_be_finished(self):
        stream_reader_not_reading = not self.stream_reader.currently_reading()
        self.assertTrue(stream_reader_not_reading)

    def then_the_operation_will_not_be_finished(self):
        stream_reader_reading = self.stream_reader.currently_reading()
        self.assertTrue(stream_reader_reading)

    def then_the_internal_stream_poller_will_be_finished(self):
        stream_poller = self.stream_reader._stream_poller
        reading = stream_poller.currently_reading()
        running = stream_poller.currently_running()
        self.assertTrue(not reading)
        self.assertTrue(not running)

class NonBlockingStreamReadOperation(Thread):

    def __init__(self, stream_reader):
        super().__init__()
        self._stream_reader = stream_reader

    def run(self):
        self._stream_reader.open()
        self._stream_reader.read_line_without_waiting()
        self._stream_reader.close()


class BlockingStreamReadOperation(Thread):
    
    def __init__(self, stream_reader):
        super().__init__()
        self._stream_reader = stream_reader

    def run(self):
        self._stream_reader.open()
        self._stream_reader.read_line_with_waiting()
        self._stream_reader.close()


if __name__ == "__main__":
    unittest.main()
