import unittest
from dipla.server import task_queue
from dipla.server.task_queue import Task, DataSource
from dipla.server.task_queue import TaskQueueEmpty


class TaskQueueTest(unittest.TestCase):

    def setUp(self):
        self.queue = task_queue.TaskQueue()

    # TODO(StefanKennedy) Test push task
    def test_push_task(self):
        sample_task = Task("a", "sample task")
        sample_task.add_data_source(
            DataSource.create_source_from_iterable([1, 2, 3]))
        self.queue.push_task(sample_task)
        self.assertEqual({"a"}, self.queue.active_tasks)
        self.assertEqual({"a"}, self.queue.nodes.keys())

        sample_task2 = Task("b", "sample task 2")
        sample_task2.add_data_source(
            DataSource.create_source_from_task(sample_task))
        self.queue.push_task(sample_task2)
        self.assertEqual({"a"}, self.queue.active_tasks)
        self.assertEqual({"a", "b"}, self.queue.nodes.keys())

        sample_task3 = Task("c", "sample task 3")
        self.queue.push_task(sample_task3)
        self.assertEqual({"a"}, self.queue.active_tasks)
        self.assertEqual({"a", "b", "c"}, self.queue.nodes.keys())
    
    def test_add_result(self):
        # Test task is marked as open on any result if no check provided
        self.queue.push_task(Task("a", ""))
        self.queue.add_result("a", "test result")
        self.assertTrue(self.queue.get_task_open("a"))

        def check_result_says_done(result):
            return result == "done"

        self.queue.push_task(Task("b", "", check_result_says_done))
        self.queue.add_result("b", "test result")
        self.assertFalse(self.queue.get_task_open("b"))
        self.queue.add_result("b", "done")
        self.assertTrue(self.queue.get_task_open("b"))

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
        print(popped.values)
        self.assertEqual([1, 2], popped.values)
        #TODO(StefanKennedy) Test that correct exceptions are raised

