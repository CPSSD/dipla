import unittest
from unittest.mock import call, Mock

from dipla.api import Dipla, UnsupportedInput
from dipla.server.task_queue import Task
from dipla.shared import uid_generator


class DiplaAPITest(unittest.TestCase):

    class TaskWithNSources(Task):
        def __init__(self, n):
            super().__init__(Mock(), Mock(), Mock())
            self.n = n

        def __eq__(self, other):
            print("Num other sources:", len(other.data_instructions))
            return len(other.data_instructions) == self.n

    def setUp(self):
        self.mock_task_queue = Mock()
        Dipla.task_queue = self.mock_task_queue
        uid_generator.generate_uid = Mock()

    def test_read_data_input(self):
        # TODO Test that these add tasks to the task queue
        input_data = ["1", "2", "3", "4", "5"]

        def data_source_function(input_value):
            return int(input_value) * 2

        promised = Dipla.read_data_source(input_data, data_source_function)
        self.assertIsNotNone(promised.task_uid)

    def test_apply_distributable_with_immediate_values(self):
        @Dipla.distributable()
        def func(input_value):
            return input_value

        input_data = [1, 2, 3, 4, 5]
        promised = Dipla.apply_distributable(func, input_data)
        self.assertIsNotNone(promised.task_uid)

    def test_apply_distributable_with_multiple_immediate_arguments(self):
        @Dipla.distributable()
        def func(input_value):
            return input_value

        input_data = [1, 2, 3, 4, 5]
        other_data = [5, 4, 3, 2, 1]
        promised = Dipla.apply_distributable(func, input_data, other_data)
        self.assertIsNotNone(promised.task_uid)
        self.mock_task_queue.push_task.assert_called_with(
            DiplaAPITest.TaskWithNSources(2))

    def test_apply_distributable_with_multiple_task_arguments(self):
        input_data = ["1", "2", "3", "4", "5"]
        other_data = ["2", "3", "4", "5", "1"]

        @Dipla.data_source
        def data_source_function(input_value):
            return int(input_value) * 2

        promised_a = Dipla.read_data_source(input_data, data_source_function)
        promised_b = Dipla.read_data_source(other_data, data_source_function)

        @Dipla.distributable()
        def func(input_value):
            return input_value

        promised = Dipla.apply_distributable(func, promised_a, promised_b)
        self.assertIsNotNone(promised.task_uid)
        self.mock_task_queue.push_task.assert_called_with(
            DiplaAPITest.TaskWithNSources(2))

    def test_apply_distributable_twice_on_same_task(self):
        @Dipla.distributable()
        def func(input_value):
            return input_value

        input_data = ["1", "2", "3", "4", "5"]
        other_data = ["2", "3", "4", "5", "1"]

        promised = Dipla.apply_distributable(func, input_data)
        promised = Dipla.apply_distributable(func, other_data)
        self.assertIsNotNone(promised.task_uid)

    def test_apply_distributable_handles_bad_value(self):
        @Dipla.distributable()
        def func(input_value):
            return input_value

        input_data = -42
        self.assertRaises(UnsupportedInput,
                          Dipla.apply_distributable,
                          func,
                          input_data)

    def test_apply_distributable_with_dependent_tasks(self):
        @Dipla.distributable()
        def func1(input_value):
            return input_value*2

        @Dipla.distributable()
        def func2(input_value):
            return input_value//2

        @Dipla.distributable()
        def add(a, b):
            return a+b

        inputs1 = [1, 2, 3, 4, 5]
        inputs2 = [6, 7, 8, 9, 10]
        result1 = Dipla.apply_distributable(func1, inputs1)
        result2 = Dipla.apply_distributable(func2, inputs2)
        promise = Dipla.apply_distributable(add, result1, result2)
        self.assertIsNotNone(promise.task_uid)

    def test_apply_distributable_raises_error_if_no_count_for_scoped_distributable(self):  # nopep8
        with self.assertRaises(NotImplementedError):
            @Dipla.scoped_distributable
            def func(input_value, index, count):
                return input_value+1

    def test_apply_scoped_distributable_with_multiple_immediate_arguments(self):  # nopep8
        @Dipla.scoped_distributable(count=1)
        def func(input_value, interval, count):
            return input_value

        input_data = [1, 2, 3, 4, 5]
        other_data = [5, 4, 3, 2, 1]
        promised = Dipla.apply_distributable(func, input_data, other_data)
        self.assertIsNotNone(promised.task_uid)
        # Two extra sources (arguments) here for interval and count
        self.mock_task_queue.push_task.assert_called_with(
            DiplaAPITest.TaskWithNSources(4))

    def test_apply_scoped_distributable_with_multiple_task_arguments(self):  # nopep8
        input_data = ["1", "2", "3", "4", "5"]
        other_data = ["2", "3", "4", "5", "1"]

        @Dipla.data_source
        def data_source_function(input_value, interval, count):
            return int(input_value) * 2

        promised_a = Dipla.read_data_source(input_data, data_source_function)
        promised_b = Dipla.read_data_source(other_data, data_source_function)

        @Dipla.scoped_distributable(count=3)
        def func(input_value, interval, count):
            return input_value

        promised = Dipla.apply_distributable(func, promised_a, promised_b)
        self.mock_task_queue.push_task.assert_called_with(
            DiplaAPITest.TaskWithNSources(4))

    def test_apply_distributable_raises_error_if_non_decorated_funcion_supplied(self):  # nopep8
        def func():
            return True

        self.assertRaises(KeyError,
                          Dipla.apply_distributable,
                          func,
                          [1, 2, 3])

    def test_explorer_adds_signal_to_created_task(self):
        @Dipla.explorer()
        @Dipla.distributable()
        def funky():
            pass

        Dipla.apply_distributable(funky, [1, 2, 3])

        class TaskWithDiscoveredSignal(Task):
            def __init__(self):
                super().__init__(Mock(), Mock(), Mock())

            def __eq__(self, other):
                print(other.signals.keys())
                return "DISCOVERED" in other.signals

        self.mock_task_queue.push_task.assert_called_with(
            TaskWithDiscoveredSignal())

    def test_apply_chasing_distributable_with_multiple_immediate_arguments(self):  # nopep8
        @Dipla.chasing_distributable(count=3, chasers=3)
        def func(input_value, interval, count):
            return input_value

        input_data = [1, 2, 3, 4, 5]
        other_data = [5, 4, 3, 2, 1]
        promised = Dipla.apply_distributable(func, input_data, other_data)
        self.assertIsNotNone(promised.task_uid)
        calls = self.mock_task_queue.push_task.mock_calls
        self.assertEqual(3, len(calls))
        self.assertEqual([call(DiplaAPITest.TaskWithNSources(4))]*3, calls)

    def test_apply_distributable_twice_on_same_task(self):
        @Dipla.data_source
        def read(input_value):
            return input_value + " "

        @Dipla.distributable()
        def func(input_value):
            return input_value

        input_data = ["1", "2", "3", "4", "5"]

        promise = Dipla.read_data_source(func, input_data)
        result = promise.distribute(func)
        self.assertIsNotNone(result.task_uid)

    def test_apply_distributable_with_dependent_tasks(self):
        @Dipla.data_source
        def func1(input_value):
            return input_value*2

        @Dipla.data_source
        def func2(input_value):
            return input_value//2

        @Dipla.distributable()
        def add(a, b):
            return a+b

        inputs1 = [1, 2, 3, 4, 5]
        inputs2 = [6, 7, 8, 9, 10]
        result1 = Dipla.read_data_source(func1, inputs1)
        result2 = Dipla.read_data_source(func2, inputs2)
        promise = result1.distribute(add, result2)
        self.assertIsNotNone(promise.task_uid)

    def tearDown(self):
        Dipla._task_creators = dict()
