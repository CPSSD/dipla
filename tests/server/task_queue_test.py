import unittest
from dipla.server import task_queue
from dipla.server.task_queue import Task


class TaskQueueTest(unittest.TestCase):

    def setUp(self):
        self.queue = task_queue.TaskQueue()

    def test_push_task(self):
        self.queue.push_task(Task("data instructions", "task instructions"))
        popped = self.queue.pop_task()
        self.assertEqual("data instructions", popped.data_instructions)
        self.assertEqual("task instructions", popped.task_instructions)

    def test_pop_tasks(self):
        self.queue.push_task(Task("1", ""))
        self.queue.push_task(Task("2", ""))
        self.assertEqual("1", self.queue.pop_task().data_instructions)
        self.assertEqual("2", self.queue.pop_task().data_instructions)
        self.queue.push_task(Task("3", ""))
        self.assertEqual("3", self.queue.pop_task().data_instructions)

    def test_peek_tasks(self):
        self.queue.push_task(Task("1", ""))
        self.assertEqual("1", self.queue.peek_task().data_instructions)
        self.queue.push_task(Task("2", ""))
        self.assertEqual("1", self.queue.peek_task().data_instructions)
        self.queue.pop_task()
        self.assertEqual("2", self.queue.peek_task().data_instructions)
