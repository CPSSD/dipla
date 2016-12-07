import unittest
from dipla.api import Dipla, UnsupportedInput


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

        input_data = [1, 2, 3, 4, 5]
        promised = Dipla.apply_distributable(func, input_data)
        self.assertIsNotNone(promised.task_uid)

    def test_apply_distributable_handles_bad_value(self):
        @Dipla.distributable
        def func(input_value):
            return input_value

        input_data = -42
        self.assertRaises(UnsupportedInput,
                          Dipla.apply_distributable,
                          func,
                          input_data)

    def test_apply_distributable_with_dependent_tasks(self):
        @Dipla.distributable
        def func1(input_value):
            return input_value*2

        @Dipla.distributable
        def func2(input_value):
            return input_value//2

        @Dipla.distributable
        def add(a, b):
            return a+b

        inputs1 = [1, 2, 3, 4, 5]
        inputs2 = [6, 7, 8, 9, 10]
        result1 = Dipla.apply_distributable(func1, inputs1)
        result2 = Dipla.apply_distributable(func2, inputs2)
        promise = Dipla.apply_distributable(add, result1, result2)
        self.assertIsNotNone(promise.task_uid)
