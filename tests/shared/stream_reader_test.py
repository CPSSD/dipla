import time
import unittest
from io import StringIO
from queue import Queue
from threading import Thread
from timeout_decorator import timeout
from dipla.shared.continuous_stream_poller import ContinuousStreamPoller
from dipla.shared.stream_reader import StreamReader


class StreamReaderTest(unittest.TestCase):

    @timeout(10)
    def test_that_thread_does_not_get_blocked_when_reading_from_an_empty_stream_without_waiting(self):
        self.given_the_stream()
        self.when_we_read_without_waiting()
        self.and_we_wait_a_bit()
        self.then_it_will_not_be_reading()

    @timeout(10)
    def test_that_thread_does_not_get_blocked_when_reading_from_a_populated_stream_without_waiting(self):
        self.given_the_stream("CONTENT")
        self.when_we_read_without_waiting()
        self.and_we_wait_a_bit()
        self.then_it_will_not_be_reading()

    @timeout(10)
    def test_that_thread_does_not_get_blocked_when_reading_from_a_populated_stream_with_waiting(self):
        self.given_the_stream("CONTENT")
        self.when_we_read_with_waiting()
        self.and_we_wait_a_bit()
        self.then_it_will_not_be_reading()

    @timeout(10)
    def test_that_thread_gets_blocked_when_reading_from_an_empty_stream(self):
        self.given_the_stream()
        self.when_we_read_with_waiting()
        self.and_we_wait_a_bit()
        self.and_we_close_it()
        self.and_we_wait_a_bit()
        self.then_it_will_be_reading()
   
    @timeout(10)
    def test_that_reading_without_wait_returns_nothing_from_empty_stream(self):
        self.given_the_stream()
        self.when_we_read_without_waiting()
        self.and_we_wait_a_bit()
        self.then_the_result_will_be(None)

    @timeout(10)
    def test_that_reading_without_wait_returns_correct_result_from_populated_stream(self):
        self.given_the_stream("CONTENT\nHERE")
        self.when_we_read_without_waiting()
        self.and_we_wait_a_bit()
        self.then_the_result_will_be("CONTENT")

    @timeout(10)
    def test_that_reading_with_wait_returns_correct_result_from_populated_stream(self):
        self.given_the_stream("CONTENT\nHERE")
        self.when_we_read_with_waiting()
        self.and_we_wait_a_bit()
        self.then_the_result_will_be("CONTENT")

    def given_the_stream(self, contents=""):
        self.stream = StringIO(contents)
        self.stream_reader = StreamReader(self.stream)

    def when_we_read_without_waiting(self):
        self.operation = NonBlockingStreamReadOperation(self.stream_reader)
        self.operation.start()

    def when_we_read_with_waiting(self):
        self.operation = BlockingStreamReadOperation(self.stream_reader)
        self.operation.start()

    def and_we_wait_a_bit(self):
        time.sleep(0.1)

    def and_we_close_it(self):
        self.stream_reader.close()

    def then_it_will_not_be_reading(self):
        reading = self.stream_reader._reading
        self.assertTrue(not reading)

    def then_it_will_be_reading(self):
        reading = self.stream_reader._reading
        self.assertTrue(reading)

    def then_the_result_will_be(self, expected):
        self.assertEqual(expected, self.operation.result)

    def tearDown(self):
        self.operation.join()


class NonBlockingStreamReadOperation(Thread):

    def __init__(self, stream_reader):
        super().__init__()
        self._stream_reader = stream_reader

    def run(self):
        self._stream_reader.open()
        self.result = self._stream_reader.read_line_without_waiting()
        self._stream_reader.close()


class BlockingStreamReadOperation(Thread):
    
    def __init__(self, stream_reader):
        super().__init__()
        self._stream_reader = stream_reader

    def run(self):
        self._stream_reader.open()
        self.result = self._stream_reader.read_line_with_waiting()
        self._stream_reader.close()

if __name__ == "__main__":
    unittest.main()
