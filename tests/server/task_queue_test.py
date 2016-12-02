import unittest
from dipla.server import task_queue
from dipla.server.task_queue import Task, TaskQueueNode, DataSource
from dipla.server.task_queue import TaskQueueEmpty
from dipla.server.task_queue import DataStreamerEmpty


class TaskQueueTest(unittest.TestCase):

    def setUp(self):
        self.queue = task_queue.TaskQueue()

    def test_push_task(self):
        # Tasks depending on iterables are always active
        sample_task = Task("foo", "sample task")
        sample_task.add_data_source(
            DataSource.create_source_from_iterable([1, 2, 3], "baz"))
        self.queue.push_task(sample_task)
        self.assertEqual({"foo"}, self.queue.get_active_tasks())
        self.assertEqual({"foo"}, self.queue.get_nodes().keys())

        # Tasks depending on other tasks need to wait before activating
        sample_task2 = Task("bar", "sample task 2")
        sample_task2.add_data_source(
            DataSource.create_source_from_task(sample_task, "foobar"))
        self.queue.push_task(sample_task2)
        self.assertEqual({"foo"}, self.queue.get_active_tasks())
        self.assertEqual({"foo", "bar"}, self.queue.get_nodes().keys())

    def test_add_result_to_task_with_default_checker(self):
        # Test task is marked as open on any result if no check provided
        sample_task = Task("foo", "")
        sample_task.add_data_source(
            DataSource.create_source_from_iterable([], "bar"))
        self.queue.push_task(sample_task)
        self.queue.add_result("foo", "test result")
        self.assertTrue(self.queue.is_task_open("foo"))

    def test_add_result_to_user_defined_check(self):
        # Test task is marked as open once a "done" result is received
        def check_result_says_done(result):
            return result == "done"

        sample_task = Task("bar", "", check_result_says_done)
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
        root_task = Task("root", "root task")
        root_task.add_data_source(
            DataSource.create_source_from_iterable([], "foo"))
        self.queue.push_task(root_task)

        next_task = Task("next", "next task")
        next_task.add_data_source(
            DataSource.create_source_from_task(root_task, "bar"))
        self.queue.push_task(next_task)

        # "next" is added as an active task id once the "root" task
        # has some values to pass on
        self.assertEquals({"root"}, self.queue.get_active_tasks())

        self.queue.add_result("root", 100)

        self.assertEquals({"root", "next"}, self.queue.get_active_tasks())

    def test_activate_missing_task(self):
        with self.assertRaises(KeyError):
            self.queue.activate_new_tasks({"foo"})

    def test_pop_task_input_depending_on_iterable(self):
        # Test default reading all values from data source
        sample_task = Task("foo", "sample task")
        sample_task.add_data_source(
            DataSource.create_source_from_iterable([1, 2, 3], "foo"))
        self.queue.push_task(sample_task)

        popped = self.queue.pop_task_input()
        self.assertEqual("foo", popped.task_uid)
        self.assertEqual("sample task", popped.task_instructions)
        self.assertEqual({"foo": [1, 2, 3]}, popped.values)

    def test_pop_task_input_using_defined_read_function(self):
        # Test reading data source using specified function
        sample_task = Task("bar", "sample task")

        def read_single_values(stream, location):
            return stream.pop(0)
        sample_task.add_data_source(DataSource.create_source_from_iterable(
                [1, 2], "foo", read_single_values))
        self.queue.push_task(sample_task)

        popped = self.queue.pop_task_input()
        self.assertEqual("bar", popped.task_uid)
        self.assertEqual("sample task", popped.task_instructions)
        self.assertEqual({"foo": 1}, popped.values)

        popped = self.queue.pop_task_input()
        self.assertEqual("bar", popped.task_uid)
        self.assertEqual("sample task", popped.task_instructions)
        self.assertEqual({"foo": 2}, popped.values)

    def test_pop_task_depending_on_task(self):
        # Test reading data source from another task
        def completion_check(result):
            return result == 2
        first_task = Task("baz", "first task", completion_check)
        self.queue.push_task(first_task)
        self.queue.add_result("baz", 1)
        self.queue.add_result("baz", 2)

        second_task = Task("foobar", "second task")
        second_task.add_data_source(
            DataSource.create_source_from_task(first_task, "foo"))
        self.queue.push_task(second_task)

        popped = self.queue.pop_task_input()
        self.assertEqual("foobar", popped.task_uid)
        self.assertEqual("second task", popped.task_instructions)
        self.assertEqual({"foo": [1, 2]}, popped.values)

    def test_pop_task_from_empty_dependency(self):
        # Test that popping data from empty task throws error
        sample_task3 = Task("foobaz", "sample task 3")
        sample_task3.add_data_source(
            DataSource.create_source_from_iterable([], "foo"))
        self.queue.push_task(sample_task3)

        with self.assertRaises(TaskQueueEmpty):
            self.queue.pop_task_input()

    def test_has_next_input(self):
        # Test empty task queue returns false
        self.assertFalse(self.queue.has_next_input())

        # Test queue with a task with no input returns false
        sample_task = Task("foo", "sample task")
        sample_task.add_data_source(
            DataSource.create_source_from_iterable([], "bar"))
        self.queue.push_task(sample_task)

        self.assertFalse(self.queue.has_next_input())

        # Test queue with two tasks, one with input returns true
        sample_task2 = Task("bar", "sample task 2")
        sample_task2.add_data_source(
            DataSource.create_source_from_iterable([1], "baz"))
        self.queue.push_task(sample_task2)

        self.assertTrue(self.queue.has_next_input())

    def test_node_has_next_input_on_single_available_input(self):
        # Task with input returns true
        sample_task = Task("foo", "sample task")
        sample_task.add_data_source(
            DataSource.create_source_from_iterable([1], "bar"))

        sample_node = TaskQueueNode(sample_task)
        self.assertTrue(sample_node.has_next_input())

    def test_node_has_next_input_on_empty_input(self):
        # Task without input returns false
        sample_task = Task("bar", "sample task")
        sample_task.add_data_source(
            DataSource.create_source_from_iterable([], "foo"))

        sample_node = TaskQueueNode(sample_task)
        self.assertFalse(sample_node.has_next_input())

    def test_node_has_next_input_on_some_empty_inputs(self):
        # Task with two inputs, but one is empty returns false
        sample_task = Task("baz", "sample task")
        sample_task.add_data_source(
            DataSource.create_source_from_iterable([1], "foo"))
        sample_task.add_data_source(
            DataSource.create_source_from_iterable([], "bar"))

        sample_node = TaskQueueNode(sample_task)
        self.assertFalse(sample_node.has_next_input())

    def test_node_has_next_input_on_defined_read_function(self):
        # Task with one input value in a stream, but requires two
        # returns false
        sample_task = Task("foobar", "sample task")

        def require_2_values(stream, location):
            print(len(stream))
            return len(stream) >= 2
        sample_task.add_data_source(DataSource.create_source_from_iterable(
            [1], "foo", availability_check=require_2_values))

        sample_node = TaskQueueNode(sample_task)
        self.assertFalse(sample_node.has_next_input())

    def test_node_next_input_depending_on_iterable(self):
        # Task with input returns correct values
        sample_task = Task("foo", "sample task")
        sample_task.add_data_source(
            DataSource.create_source_from_iterable([1], "bar"))

        sample_node = TaskQueueNode(sample_task)
        self.assertTrue([1], sample_node.next_input().values)

    def test_node_next_input_depending_on_empty_iterable(self):
        # Task with no input raises error
        sample_task = Task("bar", "sample task")
        sample_task.add_data_source(
            DataSource.create_source_from_iterable([], "foo"))

        sample_node = TaskQueueNode(sample_task)
        with self.assertRaises(DataStreamerEmpty):
            sample_node.next_input()

    def test_node_next_input_on_defined_function(self):
        # Task with custom reader returns correct value
        def read_individual_values(stream, location):
            return stream.pop(0)
        sample_task = Task("baz", "sample task")
        sample_task.add_data_source(DataSource.create_source_from_iterable(
            [1, 2], "bar", read_individual_values))

        sample_node = TaskQueueNode(sample_task)
        self.assertEqual({"bar": 1}, sample_node.next_input().values)

    def test_is_task_open_on_missing_task(self):
        with self.assertRaises(KeyError):
            self.queue.is_task_open("foo")
