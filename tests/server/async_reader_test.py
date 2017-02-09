import unittest
import sys
import asyncio
from dipla.server.async_reader import AsyncReader

class AsyncReaderTest(unittest.TestCase):

    def setUp(self):
        self.reader = AsyncReader(asyncio.get_event_loop(), sys.stdin)

    def test_create_async_input_connect_pipe(self):
        pass
