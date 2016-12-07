import unittest
from dipla.api import Dipla


class DiplaAPITest(unittest.TestCase):

    def test_read_data_input(self):
        input_data = ["1", "2", "3", "4", "5"]

        def data_source_function(input_value):
            return int(input_value) * 2

        promised = Dipla.read_data_source(input_data, data_source_function)
        self.assertIsNotNone(promised.task_uid)

    def test_apply_distributable_with_immediate_values(self):
        @Dipla.distributable
        def func(input_value):
            return input_value

        input_data = [1,2,3,4,5]
        promised = Dipla.apply_distributable(func, input_data)
        self.assertIsNotNone(promised.task_uid)
