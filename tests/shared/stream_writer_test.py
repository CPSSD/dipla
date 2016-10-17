import time
import os
from unittest import TestCase
from dipla.shared.stream_writer import StreamWriter


class StreamWriterFileStreamTest(TestCase):

    FILENAME = "DELETE_ME.txt"

    def test_that_thread_finishes_when_writing_to_stream(self):
        self.given_a_file_stream()
        self.when_we_write_to_it("Foo")
        self.and_we_wait_a_bit()
        self.then_the_thread_will_be_finished()

    def test_that_stream_writer_successfully_writes_text(self):
        self.given_a_file_stream()
        self.when_we_write_to_it("Bar")
        self.and_we_wait_a_bit()
        self.then_the_contents_will_be("Bar")

    def given_a_file_stream(self):
        filename = StreamWriterFileStreamTest.FILENAME
        self.file_stream = open(filename, "wt")

    def when_we_write_to_it(self, message):
        self.stream_writer = StreamWriter(self.file_stream, message)
        self.stream_writer.start()
        self.file_stream.close()

    def and_we_wait_a_bit(self):
        time.sleep(0.3)

    def then_the_thread_will_be_finished(self):
        thread_running = self.stream_writer.isAlive()
        self.assertFalse(thread_running)

    def then_the_contents_will_be(self, expected):
        filename = StreamWriterFileStreamTest.FILENAME
        with open(filename) as stream:
            stream_contents = stream.read()
        self.assertEqual(expected, stream_contents)

    def tearDown(self):
        filename = StreamWriterFileStreamTest.FILENAME
        os.remove(filename) 
