import unittest
from dipla.server import task_queue
from dipla.server.task_queue import Task
from dipla.server.task_queue import TaskQueueEmpty


class TaskQueueTest(unittest.TestCase):

    def setUp(self):
        self.queue = task_queue.TaskQueue()

    def test_push_task(self):
        self.queue.push_task(Task("a", [1, 2, 3], "task instructions"))
        popped = self.queue.pop_task()
        self.assertEqual([1, 2, 3], popped.data_source)
        self.assertEqual("task instructions", popped.task_instructions)

    def test_pop_tasks(self):
        self.queue.push_task(Task("a", [1, 2, 3], ""))
        self.queue.push_task(Task("b", [3, 2, 1], ""))
        self.assertEqual([1, 2, 3], self.queue.pop_task().data_source)
        self.assertEqual([3, 2, 1], self.queue.pop_task().data_source)
        self.queue.push_task(Task("c", [5, 6, 7], ""))
        self.assertEqual([5, 6, 7], self.queue.pop_task().data_source)

    def test_peek_tasks(self):
        self.queue.push_task(Task("a", [1, 2, 3], ""))
        self.assertEqual([1, 2, 3], self.queue.peek_task().data_source)
        self.queue.push_task(Task("b", [3, 2, 1], ""))
        self.assertEqual([1, 2, 3], self.queue.peek_task().data_source)
        self.queue.pop_task()
        self.assertEqual([3, 2, 1], self.queue.peek_task().data_source)

    def test_add_result(self):
        # Test task is marked as completed on any result if no check provided
        test_task = Task("a", [], "")
        test_task.add_result("test result")
        self.assertTrue(test_task.completed)

        def check_result_says_done(result):
            return result == "done"

        test_task = Task("b", [], "", check_result_says_done)
        test_task.add_result("test result")
        self.assertFalse(test_task.completed)
        test_task.add_result("done")
        self.assertTrue(test_task.completed)

        # Test that task is removed from queue on completion
        self.queue.push_task(Task("c", [], ""))
        queue_task = self.queue.peek_task()
        queue_task.add_result("done")
        self.assertTrue(queue_task.completed)

        with self.assertRaises(TaskQueueEmpty):
            self.queue.peek_task()
