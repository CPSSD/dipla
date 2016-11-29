import unittest
from dipla.server import task_queue
from dipla.server.task_queue import Task, TaskQueueNode, DataSource
from dipla.server.task_queue import TaskQueueEmpty, NoTaskDependencyError


class TaskQueueTest(unittest.TestCase):

    def setUp(self):
        self.queue = task_queue.TaskQueue()

    def test_push_task(self):
        # Tasks depending on iterables are always active
        sample_task = Task("a", "sample task")
        sample_task.add_data_source(
            DataSource.create_source_from_iterable([1, 2, 3]))
        self.queue.push_task(sample_task)
        self.assertEqual({"a"}, self.queue.active_tasks)
        self.assertEqual({"a"}, self.queue.nodes.keys())

        # Tasks depending on other tasks need to wait before activating
        sample_task2 = Task("b", "sample task 2")
        sample_task2.add_data_source(
            DataSource.create_source_from_task(sample_task))
        self.queue.push_task(sample_task2)
        self.assertEqual({"a"}, self.queue.active_tasks)
        self.assertEqual({"a", "b"}, self.queue.nodes.keys())

        # Tasks without any dependencies should raise an error
        sample_task3 = Task("c", "sample task 3")
        with self.assertRaises(NoTaskDependencyError):
            self.queue.push_task(sample_task3)
    
    def test_add_result(self):
        # Test task is marked as open on any result if no check provided
        sample_task = Task("a", "")
        sample_task.add_data_source(
            DataSource.create_source_from_iterable([]))
        self.queue.push_task(sample_task)
        self.queue.add_result("a", "test result")
        self.assertTrue(self.queue.get_task_open("a"))

        # Test task is marked as open once a "done" result is received
        def check_result_says_done(result):
            return result == "done"

        sample_task2 = Task("b", "", check_result_says_done)
        sample_task2.add_data_source(
            DataSource.create_source_from_iterable([]))
        self.queue.push_task(sample_task2)
        self.queue.add_result("b", "test result")
        self.assertFalse(self.queue.get_task_open("b"))
        self.queue.add_result("b", "done")
        self.assertTrue(self.queue.get_task_open("b"))

    def test_activate_new_tasks(self):
        root_task = Task("root", "root task")
        root_task.add_data_source(
            DataSource.create_source_from_iterable([]))
        self.queue.push_task(root_task)

        next_task = Task("next", "next task")
        next_task.add_data_source(
            DataSource.create_source_from_task(root_task))
        self.queue.push_task(next_task)
        
        # "next" is added as an active task id once the "root" task
        # has some values to pass on
        self.assertEquals({"root"}, self.queue.active_tasks)

        self.queue.add_result("root", 100)

        self.assertEquals({"root", "next"}, self.queue.active_tasks)

    def test_pop_task_input(self):
        # Test default reading all values from data source
        sample_task = Task("a", "sample task")
        sample_task.add_data_source(
            DataSource.create_source_from_iterable([1, 2, 3]))
        self.queue.push_task(sample_task)

        popped = self.queue.pop_task_input()
        self.assertEqual("a", popped.task_uid)
        self.assertEqual("sample task", popped.task_instructions)
        self.assertEqual([1, 2, 3], popped.values)

        # Test reading data source using specified function
        self.queue = task_queue.TaskQueue()
        sample_task2 = Task("b", "sample task 2")

        def read_single_values(stream):
            return stream.pop(0)
        sample_task2.add_data_source(
            DataSource.create_source_from_iterable([1, 2], read_single_values))
        self.queue.push_task(sample_task2)

        popped = self.queue.pop_task_input()
        self.assertEqual("b", popped.task_uid)
        self.assertEqual("sample task 2", popped.task_instructions)
        self.assertEqual(1, popped.values)
        
        popped = self.queue.pop_task_input()
        self.assertEqual("b", popped.task_uid)
        self.assertEqual("sample task 2", popped.task_instructions)
        self.assertEqual(2, popped.values)

        # Test reading data source from another task
        self.queue = task_queue.TaskQueue()
        def completion_check(result):
            return result == 2
        first_task = Task("c", "first task", completion_check)
        first_task.add_data_source(
            DataSource.create_source_from_iterable([]))
        self.queue.push_task(first_task)
        self.queue.add_result("c", 1)
        self.queue.add_result("c", 2)

        second_task = Task("d", "second task")
        second_task.add_data_source(
            DataSource.create_source_from_task(first_task))
        self.queue.push_task(second_task)

        popped = self.queue.pop_task_input()
        self.assertEqual("d", popped.task_uid)
        self.assertEqual("second task", popped.task_instructions)
        self.assertEqual([1, 2], popped.values)

        # Test that popping data from empty task throws error
        self.queue = task_queue.TaskQueue()
        sample_task3 = Task("e", "sample task 3")
        sample_task3.add_data_source(
            DataSource.create_source_from_iterable([]))
        self.queue.push_task(sample_task3)

        with self.assertRaises(TaskQueueEmpty):
            self.queue.pop_task_input()

    def test_node_has_next_input(self):
        # Task with input returns true
        sample_task = Task("a", "sample task")
        sample_task.add_data_source(
            DataSource.create_source_from_iterable([1]))
        
        sample_node = TaskQueueNode(sample_task)
        self.assertTrue(sample_node.has_next_input())

        # Task without input returns false
        sample_task2 = Task("b", "sample task")
        sample_task2.add_data_source(
            DataSource.create_source_from_iterable([]))
        
        sample_node2 = TaskQueueNode(sample_task2)
        self.assertFalse(sample_node2.has_next_input())

        # Task with two inputs, but one is empty returns false
        sample_task3 = Task("c", "sample task")
        sample_task3.add_data_source(
            DataSource.create_source_from_iterable([1]))
        sample_task3.add_data_source(
            DataSource.create_source_from_iterable([]))

        sample_node3 = TaskQueueNode(sample_task3)
        self.assertFalse(sample_node3.has_next_input())

        # Task with one input value in a stream, but requires two
        # returns false
        sample_task4 = Task("d", "sample task")

        def require_2_values(stream):
            print(len(stream))
            return len(stream) >= 2
        sample_task4.add_data_source(DataSource.create_source_from_iterable(
            [1], availability_check=require_2_values))

        sample_node4 = TaskQueueNode(sample_task4)
        self.assertFalse(sample_node4.has_next_input())

    def test_node_next_input(self):
        # Task with input returns correct values
        sample_task = Task("a", "sample task")
        sample_task.add_data_source(
            DataSource.create_source_from_iterable([1]))
        
        sample_node = TaskQueueNode(sample_task)
        self.assertTrue([1], sample_node.next_input().values)

        # Task with no input raises error
        sample_task2 = Task("b", "sample task")
        sample_task2.add_data_source(
            DataSource.create_source_from_iterable([]))
        
        sample_node2 = TaskQueueNode(sample_task2)
        with self.assertRaises(StopIteration):
            sample_node2.next_input()

        # Task with custom reader returns correct value
        def read_individual_values(stream):
            return stream.pop(0)
        sample_task3 = Task("c", "sample task")
        sample_task3.add_data_source(DataSource.create_source_from_iterable(
            [1, 2], read_individual_values))

        sample_node3 = TaskQueueNode(sample_task3)
        self.assertEqual(1, sample_node3.next_input().values)
