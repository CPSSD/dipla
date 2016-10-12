import io
import queue
import time
import unittest
from dipla.shared.stream import TextCollector


class TextCollectorTest(unittest.TestCase):

    def tearDown(self):
        self.text_collector.stop()

    def test_that_the_stream_is_shared_by_the_text_collector(self):
        self.given_collecting_text_from_an_empty_stream()
        self.given_applying_output_to_empty_queue()
        self.when_we_start_the_text_collector()
        self.then_the_stream_will_be_shared()

    def test_that_the_queue_is_shared_by_the_text_collector(self):
        self.given_collecting_text_from_an_empty_stream()
        self.given_applying_output_to_empty_queue()
        self.when_we_start_the_text_collector()
        self.then_the_queue_will_be_shared()

    def test_that_no_text_is_collected_from_an_empty_stream(self):
        self.given_collecting_text_from_an_empty_stream()
        self.given_applying_output_to_empty_queue()
        self.when_we_start_the_text_collector()
        self.and_we_wait_a_little_big()
        self.then_nothing_will_have_been_collected()

    def test_that_text_is_collected_from_non_empty_stream(self):
        self.given_collecting_text_from_a_stream_with("Foo")
        self.given_applying_output_to_empty_queue()
        self.when_we_start_the_text_collector()
        self.and_we_wait_a_little_big()
        self.then_we_will_have_collected("Foo")

    def test_that_multiple_lines_can_be_collected_from_stream(self):
        self.given_collecting_text_from_a_stream_with("Foo\nBar")
        self.given_applying_output_to_empty_queue()
        self.when_we_start_the_text_collector()
        self.and_we_wait_a_little_big()
        self.then_we_will_have_collected("Foo")
        self.then_we_will_have_collected("Bar")

    def given_collecting_text_from_an_empty_stream(self):
        self.stream = io.StringIO()

    def given_collecting_text_from_a_stream_with(self, text):
        self.stream = io.StringIO(text)

    def given_applying_output_to_empty_queue(self):
        self.queue = queue.Queue()

    def when_we_start_the_text_collector(self):
        self.text_collector = TextCollector(self.stream, self.queue)
        self.text_collector.start()

    def then_the_stream_will_be_shared(self):
        local_stream_id = id(self.stream)
        foreign_stream_id = id(self.text_collector._stream)
        self.assertTrue(local_stream_id, foreign_stream_id)

    def then_the_queue_will_be_shared(self):
        local_queue_id = id(self.queue)
        foreign_queue_id = id(self.text_collector._queue)
        self.assertTrue(local_queue_id, foreign_queue_id)

    def and_we_wait_a_little_big(self):
        time.sleep(0.03)

    def then_nothing_will_have_been_collected(self):
        self.assertTrue(self.queue.empty())

    def then_we_will_have_collected(self, expected):
        self.assertEqual(expected, self.queue.get_nowait())


if __name__ == "__main__":
    unittest.main()
