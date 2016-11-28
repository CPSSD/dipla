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
        self.queue.push_task(Task("a", [], ""))
        self.queue.add_result("a", "test result")
        self.assertIsNone(self.queue.queue_head)

        def check_result_says_done(result):
            return result == "done"

        self.queue.push_task(Task("b", [], "", check_result_says_done))
        self.queue.add_result("b", "test result")
        self.assertIsNotNone(self.queue.queue_head)
        self.queue.add_result("b", "done")
        self.assertIsNone(self.queue.queue_head)
