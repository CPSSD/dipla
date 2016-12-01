import unittest
from dipla.api import Dipla

class DiplaAPITest(unittest.TestCase):

    def test_read_data_input(self):
        input_data = [1, 2, 3, 4, 5]
        promised = Dipla.read_data_source(input_data)
        self.assertIsNotNone(promised.uid)
        self.assertIsNotNone(promised.task_queue)
