import time
import unittest
from timeout_decorator import timeout
from io import StringIO
from queue import Queue
from queue import Empty
from threading import Thread
from dipla.shared.continuous_stream_poller import ContinuousStreamPoller


class ContinuousStreamPollerTest(unittest.TestCase):

    def setUp(self):
        self.stream_poller = None

    def tearDown(self):
        self.stream_poller.join()

    def test_that_the_stream_is_shared_by_the_continuous_stream_poller(self):
        self.given_collecting_text_from_an_empty_stream()
        self.when_we_start_the_stream_poller()
        self.then_the_stream_will_be_shared()

    def test_that_the_queue_is_shared_by_the_continuous_stream_poller(self):
        self.given_collecting_text_from_an_empty_stream()
        self.when_we_start_the_stream_poller()
        self.then_the_queue_will_be_shared()

#    def test_that_no_text_is_collected_from_an_empty_stream(self):
#        self.given_collecting_text_from_an_empty_stream()
#        self.when_we_start_the_continuous_stream_poller()
#        self.and_we_wait_a_little_big()
#        self.then_nothing_will_have_been_collected()
#
#    def test_that_text_is_collected_from_non_empty_stream(self):
#        self.given_collecting_text_from_a_stream_with("Foo")
#        self.when_we_start_the_continuous_stream_poller()
#        self.and_we_wait_a_little_big()
#        self.then_we_will_have_collected("Foo")
#
#    def test_that_multiple_lines_can_be_collected_from_stream(self):
#        self.given_collecting_text_from_a_stream_with("Foo\nBar")
#        self.when_we_start_the_continuous_stream_poller()
#        self.and_we_wait_a_little_big()
#        self.then_we_will_have_collected("Foo")
#        self.then_we_will_have_collected("Bar")
#
#    def test_that_it_will_not_be_left_reading_once_stopped(self):
#        self.given_collecting_text_from_an_empty_stream()
#        self.when_we_start_the_continuous_stream_poller()
#        self.and_we_stop_the_continuous_stream_poller()
#        self.and_we_wait_a_little_big()
#        self.then_the_stream_poller_will_not_currently_be_reading()
#
#    def test_that_it_will_still_be_running_when_not_stopped(self):
#        self.given_collecting_text_from_an_empty_stream()
#        self.when_we_start_the_continuous_stream_poller()
#        self.and_we_wait_a_little_big()
#        self.then_the_stream_poller_will_still_be_running()

    def given_collecting_text_from_an_empty_stream(self):
        self.stream = StringIO()

    def given_collecting_text_from_a_stream_with(self, text):
        self.stream = StringIO(text)

    def when_we_start_the_stream_poller(self):
        self.queue = Queue()
        self.stream_poller = ContinuousStreamPoller(self.stream, self.queue)
        self.stream_poller.start()

    def and_we_stop_the_stream_poller(self):
        self.stream_poller.join()

    def then_the_stream_will_be_shared(self):
        local_stream_id = id(self.stream)
        foreign_stream_id = id(self.stream_poller._stream)
        self.assertEqual(local_stream_id, foreign_stream_id)

    def then_the_queue_will_be_shared(self):
        local_queue_id = id(self.queue)
        foreign_queue_id = id(self.stream_poller._queue)
        self.assertEqual(local_queue_id, foreign_queue_id)

    def and_we_wait_a_little_big(self):
        time.sleep(0.03)

    def then_nothing_will_have_been_collected(self):
        self.assertTrue(self.queue.empty())

    def then_we_will_have_collected(self, expected):
        try:
            self.assertEqual(expected, self.queue.get_nowait())
        except Empty:
            self.fail("Queue is unexpectedly empty")


class ContinuousStreamPollerThreadedTest(unittest.TestCase):

    @timeout(10)
    def test_that_stream_poller_stops_when_stopped_directly_from_the_main_thread(self):
        self.given_a_running_stream_poller_nested_in_a_thread()
        self.and_we_wait_a_bit()
        self.when_we_stop_the_stream_poller_directly()
        self.and_we_wait_a_bit()
        self.then_the_stream_poller_will_not_be_running()

    @timeout(10)
    def test_that_stream_poller_stops_when_stopped_through_the_intermediate_thread(self):
        self.given_a_running_stream_poller_nested_in_a_thread()
        self.and_we_wait_a_bit()
        self.when_we_stop_the_stream_poller_through_the_intermediate_thread()
        self.and_we_wait_a_bit()
        self.then_the_stream_poller_will_not_be_running()

    def given_a_running_stream_poller_nested_in_a_thread(self):
        empty_stream = StringIO()
        empty_queue = Queue()
        self.stream_poller = ContinuousStreamPoller(empty_stream, empty_queue, interval=0.1)
        self.intermediate_thread = IntermediateStreamPollerThread(self.stream_poller)
        self.intermediate_thread.start()

    def when_we_stop_the_stream_poller_directly(self):
        self.stream_poller.join()

    def when_we_stop_the_stream_poller_through_the_intermediate_thread(self):
        self.intermediate_thread.stream_poller.join()

    def and_we_wait_a_bit(self):
        time.sleep(0.1)

    def then_the_stream_poller_will_not_be_running(self):
        running = self.intermediate_thread.stream_poller.isAlive()
        self.assertTrue(not running)


class IntermediateStreamPollerThread(Thread):

    def __init__(self, stream_poller):
        super().__init__()
        self.stream_poller = stream_poller

    def run(self):
        self.stream_poller.start()


if __name__ == "__main__":
    unittest.main()
