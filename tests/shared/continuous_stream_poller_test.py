import io
import queue
import threading
import time
import unittest
from dipla.shared.continuous_stream_poller import ContinuousStreamPoller


class ContinuousStreamPollerTest(unittest.TestCase):

    def tearDown(self):
        self.continuous_stream_poller.stop()

    def test_that_the_stream_is_shared_by_the_continuous_stream_poller(self):
        self.given_collecting_text_from_an_empty_stream()
        self.given_applying_output_to_empty_queue()
        self.when_we_start_the_continuous_stream_poller()
        self.then_the_stream_will_be_shared()

    def test_that_the_queue_is_shared_by_the_continuous_stream_poller(self):
        self.given_collecting_text_from_an_empty_stream()
        self.given_applying_output_to_empty_queue()
        self.when_we_start_the_continuous_stream_poller()
        self.then_the_queue_will_be_shared()

    def test_that_no_text_is_collected_from_an_empty_stream(self):
        self.given_collecting_text_from_an_empty_stream()
        self.given_applying_output_to_empty_queue()
        self.when_we_start_the_continuous_stream_poller()
        self.and_we_wait_a_little_big()
        self.then_nothing_will_have_been_collected()

    def test_that_text_is_collected_from_non_empty_stream(self):
        self.given_collecting_text_from_a_stream_with("Foo")
        self.given_applying_output_to_empty_queue()
        self.when_we_start_the_continuous_stream_poller()
        self.and_we_wait_a_little_big()
        self.then_we_will_have_collected("Foo")

    def test_that_multiple_lines_can_be_collected_from_stream(self):
        self.given_collecting_text_from_a_stream_with("Foo\nBar")
        self.given_applying_output_to_empty_queue()
        self.when_we_start_the_continuous_stream_poller()
        self.and_we_wait_a_little_big()
        self.then_we_will_have_collected("Foo")
        self.then_we_will_have_collected("Bar")

    def test_that_it_will_not_be_left_reading_once_stopped(self):
        self.given_collecting_text_from_an_empty_stream()
        self.given_applying_output_to_empty_queue()
        self.when_we_start_the_continuous_stream_poller()
        self.and_we_stop_the_continuous_stream_poller()
        self.and_we_wait_a_little_big()
        self.then_the_continuous_stream_poller_will_not_currently_be_reading()

    def test_that_it_will_still_be_running_when_not_stopped(self):
        self.given_collecting_text_from_an_empty_stream()
        self.given_applying_output_to_empty_queue()
        self.when_we_start_the_continuous_stream_poller()
        self.and_we_wait_a_little_big()
        self.then_the_continuous_stream_poller_will_still_be_running()

    def given_collecting_text_from_an_empty_stream(self):
        self.stream = io.StringIO()

    def given_collecting_text_from_a_stream_with(self, text):
        self.stream = io.StringIO(text)

    def given_applying_output_to_empty_queue(self):
        self.queue = queue.Queue()

    def when_we_start_the_continuous_stream_poller(self):
        self.continuous_stream_poller = ContinuousStreamPoller(self.stream,
                                                               self.queue)
        self.continuous_stream_poller.start()

    def and_we_stop_the_continuous_stream_poller(self):
        self.continuous_stream_poller.stop()

    def then_the_stream_will_be_shared(self):
        local_stream_id = id(self.stream)
        foreign_stream_id = id(self.continuous_stream_poller._stream)
        self.assertTrue(local_stream_id, foreign_stream_id)

    def then_the_queue_will_be_shared(self):
        local_queue_id = id(self.queue)
        foreign_queue_id = id(self.continuous_stream_poller._queue)
        self.assertTrue(local_queue_id, foreign_queue_id)

    def and_we_wait_a_little_big(self):
        time.sleep(0.03)

    def then_nothing_will_have_been_collected(self):
        self.assertTrue(self.queue.empty())

    def then_we_will_have_collected(self, expected):
        try:
            self.assertEqual(expected, self.queue.get_nowait())
        except queue.Empty:
            self.fail("Queue is unexpectedly empty")

    def then_the_continuous_stream_poller_will_not_currently_be_reading(self):
        finished = not self.continuous_stream_poller.currently_running()
        not_reading = not self.continuous_stream_poller.currently_reading()
        self.assertTrue(finished and not_reading)

    def then_the_continuous_stream_poller_will_still_be_running(self):
        running = self.continuous_stream_poller.currently_running()
        self.assertTrue(running)


if __name__ == "__main__":
    unittest.main()
