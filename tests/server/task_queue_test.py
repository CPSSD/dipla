import unittest
from unittest.mock import MagicMock, Mock
from dipla.server import task_queue
from dipla.server.task_queue import Task, TaskQueueNode
from dipla.server.task_queue import DataSource, DataStreamer
from dipla.server.task_queue import MachineType
from dipla.server.task_queue import TaskQueueEmpty, DataStreamerEmpty


class TaskQueueTest(unittest.TestCase):

    def setUp(self):
        self.queue = task_queue.TaskQueue()

    def test_push_task(self):
        # Tasks depending on iterables are always active
        sample_task = Task("foo", "sample task", MachineType.client)
        sample_task.add_data_source(
            DataSource.create_source_from_iterable([1, 2, 3], "baz"))
        self.assertFalse(self.queue.has_next_input())
        self.queue.push_task(sample_task)
        self.assertTrue(self.queue.has_next_input())

    def test_add_result_to_task_with_default_checker(self):
        # Test task is marked as open on any result if no check provided
        sample_task = Task("foo", "", MachineType.client)
        sample_task.add_data_source(
            DataSource.create_source_from_iterable([], "bar"))
        self.queue.push_task(sample_task)
        self.queue.add_result("foo", "test result")
        self.assertTrue(self.queue.is_task_open("foo"))

    def test_add_result_to_user_defined_check(self):
        # Test task is marked as open once a "done" result is received
        def check_result_says_done(result):
            return result == "done"

        sample_task = Task(
            "bar", "", MachineType.client, check_result_says_done)
        sample_task.add_data_source(
            DataSource.create_source_from_iterable([], "foo"))
        self.queue.push_task(sample_task)
        self.queue.add_result("bar", "test result")
        self.assertFalse(self.queue.is_task_open("bar"))
        self.queue.add_result("bar", "done")
        self.assertTrue(self.queue.is_task_open("bar"))

    def test_add_result_for_missing_task(self):
        with self.assertRaises(KeyError):
            self.queue.add_result("bar", "result")

    def test_activate_new_tasks(self):
        root_task = Task("root", "root task", MachineType.client)

        def consume_reader(stream, location):
            return stream.pop(0)

        root_task.add_data_source(DataSource.create_source_from_iterable(
            [1], "foo", consume_reader, location_changer=None))
        self.queue.push_task(root_task)

        self.assertTrue(self.queue.has_next_input())
        self.queue.pop_task_input()
        self.assertFalse(self.queue.has_next_input())

        next_task = Task("next", "next task", MachineType.client)
        next_task.add_data_source(
            DataSource.create_source_from_task(root_task, "bar"))
        self.queue.push_task(next_task)

        # "next" is added as an active task id once the "root" task
        # has some values to pass on
        self.assertFalse(self.queue.has_next_input())

        self.queue.add_result("root", 100)

        self.assertTrue(self.queue.has_next_input())

    def test_activate_missing_task(self):
        with self.assertRaises(KeyError):
            self.queue.activate_new_tasks({"foo"})

    def test_pop_task_input_depending_on_iterable(self):
        # Test default reading all values from data source
        sample_task = Task("foo", "sample task", MachineType.client)
        sample_task.add_data_source(
            DataSource.create_source_from_iterable([1, 2, 3], "foo"))
        self.queue.push_task(sample_task)

        popped = self.queue.pop_task_input()
        self.assertEqual("foo", popped.task_uid)
        self.assertEqual("sample task", popped.task_instructions)
        self.assertEqual([[1, 2, 3]], popped.values)

    def test_pop_task_input_using_defined_read_function(self):
        # Test reading data source using specified function
        sample_task = Task("bar", "sample task", MachineType.client)

        def read_single_values(stream, location):
            return stream.pop(0)
        sample_task.add_data_source(DataSource.create_source_from_iterable(
                [1, 2], "foo", read_single_values, location_changer=None))
        self.queue.push_task(sample_task)

        popped = self.queue.pop_task_input()
        self.assertEqual("bar", popped.task_uid)
        self.assertEqual("sample task", popped.task_instructions)
        self.assertEqual([[1]], popped.values)

        popped = self.queue.pop_task_input()
        self.assertEqual("bar", popped.task_uid)
        self.assertEqual("sample task", popped.task_instructions)
        self.assertEqual([[2]], popped.values)

    def test_pop_task_depending_on_task(self):
        # Test reading data source from another task
        def completion_check(result):
            return result == 2
        first_task = Task(
            "baz", "first task", MachineType.client, completion_check)
        self.queue.push_task(first_task)
        self.queue.add_result("baz", 1)
        self.queue.add_result("baz", 2)

        second_task = Task("foobar", "second task", MachineType.client)
        second_task.add_data_source(
            DataSource.create_source_from_task(first_task, "foo"))
        self.queue.push_task(second_task)

        popped = self.queue.pop_task_input()
        self.assertEqual("foobar", popped.task_uid)
        self.assertEqual("second task", popped.task_instructions)
        self.assertEqual([[1, 2]], popped.values)

    def test_pop_task_with_multiple_inputs(self):
        first_task = Task("foo", "first task", MachineType.client)
        self.queue.push_task(first_task)

        second_task = Task("bar", "second task", MachineType.client)
        self.queue.push_task(second_task)

        dependent_task = Task("baz", "dependent task", MachineType.client)
        self.queue.push_task(first_task)

        second_task = Task("bar", "second task", MachineType.client)
        self.queue.push_task(second_task)

        dependent_task = Task("baz", "dependent task", MachineType.client)
        dependent_task.add_data_source(
            DataSource.create_source_from_task(first_task, "foobar"))
        dependent_task.add_data_source(
            DataSource.create_source_from_task(second_task, "foobaz"))
        self.queue.push_task(dependent_task)

        self.assertFalse(self.queue.has_next_input())
        self.queue.add_result("foo", [1, 2])
        self.assertFalse(self.queue.has_next_input())
        self.queue.add_result("bar", [1, 2])
        self.assertTrue(self.queue.has_next_input())

    def test_pop_task_from_empty_dependency(self):
        # Test that popping data from empty task throws error
        sample_task3 = Task("foobaz", "sample task 3", MachineType.client)
        sample_task3.add_data_source(
            DataSource.create_source_from_iterable([], "foo"))
        self.queue.push_task(sample_task3)

        with self.assertRaises(TaskQueueEmpty):
            self.queue.pop_task_input()

    def test_has_next_input(self):
        # Test empty task queue returns false
        self.assertFalse(self.queue.has_next_input())

        # Test queue with a task with no input returns false
        sample_task = Task("foo", "sample task", MachineType.client)
        sample_task.add_data_source(
            DataSource.create_source_from_iterable([], "bar"))
        self.queue.push_task(sample_task)

        self.assertFalse(self.queue.has_next_input())

        # Test queue with two tasks, one with input returns true
        sample_task2 = Task("bar", "sample task 2", MachineType.client)
        sample_task2.add_data_source(
            DataSource.create_source_from_iterable([1], "baz"))
        self.queue.push_task(sample_task2)

        self.assertTrue(self.queue.has_next_input())

    def test_node_has_next_input_on_single_available_input(self):
        # Task with input returns true
        sample_task = Task("foo", "sample task", MachineType.client)
        sample_task.add_data_source(
            DataSource.create_source_from_iterable([1], "bar"))

        sample_node = TaskQueueNode(sample_task)
        self.assertTrue(sample_node.has_next_input())

    def test_node_has_next_input_on_empty_input(self):
        # Task without input returns false
        sample_task = Task("bar", "sample task", MachineType.client)
        sample_task.add_data_source(
            DataSource.create_source_from_iterable([], "foo"))

        sample_node = TaskQueueNode(sample_task)
        self.assertFalse(sample_node.has_next_input())

    def test_node_has_next_input_on_some_empty_inputs(self):
        # Task with two inputs, but one is empty returns false
        sample_task = Task("baz", "sample task", MachineType.client)
        sample_task.add_data_source(
            DataSource.create_source_from_iterable([1], "foo"))
        sample_task.add_data_source(
            DataSource.create_source_from_iterable([], "bar"))

        sample_node = TaskQueueNode(sample_task)
        self.assertFalse(sample_node.has_next_input())

    def test_node_has_next_input_on_defined_read_function(self):
        # Task with one input value in a stream, but requires two
        # returns false
        sample_task = Task("foobar", "sample task", MachineType.client)

        def require_2_values(stream, location):
            return len(stream) >= 2
        sample_task.add_data_source(DataSource.create_source_from_iterable(
            [1], "foo", availability_check=require_2_values))

        sample_node = TaskQueueNode(sample_task)
        self.assertFalse(sample_node.has_next_input())

    def test_node_next_input_depending_on_iterable(self):
        # Task with input returns correct values
        sample_task = Task("foo", "sample task", MachineType.client)
        sample_task.add_data_source(
            DataSource.create_source_from_iterable([1], "bar"))

        sample_node = TaskQueueNode(sample_task)
        self.assertTrue([1], sample_node.next_input().values)

    def test_node_next_input_depending_on_empty_iterable(self):
        # Task with no input raises error
        sample_task = Task("bar", "sample task", MachineType.client)
        sample_task.add_data_source(
            DataSource.create_source_from_iterable([], "foo"))

        sample_node = TaskQueueNode(sample_task)
        with self.assertRaises(DataStreamerEmpty):
            sample_node.next_input()

    def test_node_next_input_on_defined_function(self):
        # Task with custom reader returns correct value
        def read_individual_values(stream, location):
            return stream.pop(0)
        sample_task = Task("baz", "sample task", MachineType.server)
        sample_task.add_data_source(DataSource.create_source_from_iterable(
            [1, 2], "bar", read_individual_values, location_changer=None))

        sample_node = TaskQueueNode(sample_task)
        self.assertEqual([[1]], sample_node.next_input().values)

    def test_is_task_open_on_missing_task(self):
        with self.assertRaises(KeyError):
            self.queue.is_task_open("foo")

    def test_get_bad_task_by_id(self):
        with self.assertRaises(KeyError):
            self.queue.get_task_by_id('abcdefghijk')

    def test_get_good_task_by_id(self):
        given_task = Task("foo", "sample task", MachineType.client)
        self.queue.push_task(given_task)
        gotten_task = self.queue.get_task_by_id("foo")
        self.assertEqual(given_task.uid, gotten_task.uid)
        self.assertEqual(given_task.instructions, gotten_task.instructions)

    def test_task_queue_node_next_input_contains_task_signals(self):
        mock_task = MagicMock()
        mock_task.signals = ["FOO", "BAR"]
        mock_task.data_instructions = [MagicMock()]
        node = TaskQueueNode(mock_task)

        task_input = node.next_input()
        self.assertEqual(["FOO", "BAR"], task_input.signals)

    def test_push_task_input_adds_new_input_for_task_with_immediate_inputs(self):  # nopep8
        mock_task = MagicMock()
        mock_task.uid = "foo"

        # source_task_uid needs to be set to none because it would
        # return a Mock otherwise. Immediate sources should return None
        mock_source_a = Mock()
        mock_source_a.source_task_uid = None
        mock_source_b = Mock()
        mock_source_b.source_task_uid = None

        mock_task.data_instructions = [mock_source_a, mock_source_b]
        self.queue.push_task(mock_task)

        self.queue.push_task_input("foo", [[1, 2, 3], [4, 5, 6]])
        mock_source_a.data_streamer.add_inputs.assert_called_with([1, 2, 3])
        mock_source_b.data_streamer.add_inputs.assert_called_with([4, 5, 6])

    def test_data_streamer_add_inputs_adds_to_stream(self):
        mock_stream = Mock()

        data_streamer = DataStreamer(mock_stream, Mock(), Mock(), Mock())
        data_streamer.add_inputs([1, 2, 3])
        data_streamer.stream.extend.assert_called_with([1, 2, 3])

    def test_push_task_input_raises_error_if_task_id_unrecognised(self):
        with self.assertRaises(KeyError):
            self.queue.push_task_input("unrecognised", [[1, 2]])

    def test_push_task_input_raises_error_if_non_matching_num_arguments(self):
        mock_task = MagicMock()
        mock_task.uid = "foo"

        mock_source = Mock()
        mock_source.source_task_uid = None

        mock_task.data_instructions = [mock_source]

        self.queue.push_task(mock_task)

        with self.assertRaises(ValueError):
            self.queue.push_task_input("foo", [[1, 2], [1, 2]])

    def test_create_data_source_from_generator(self):
        def generator():
            yield [1, 2, 3]
            yield [2, 3, 4]

        data_source = DataSource.create_source_from_generator(
            generator(), "foo")

        self.assertEquals([1, 2, 3], data_source.data_streamer.read())
        self.assertEquals([2, 3, 4], data_source.data_streamer.read())
