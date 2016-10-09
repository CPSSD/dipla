import unittest
from dipla.server import task_queue
from dipla.server.task_queue import QueueItem

class TaskQueueTest(unittest.TestCase):

    def setUp(self):
        self.queue = task_queue.TaskQueue()

    def test_push_task(self):
        self.queue.push_task(QueueItem(
            "data instructions",
            "task instructions"))
        popped = self.queue.pop_task()
        self.assertEqual(popped.data_instructions, "data instructions")
        self.assertEqual(popped.task_instructions, "task instructions")

    def test_pop_tasks(self):
        self.queue.push_task(QueueItem("1", ""))
        self.queue.push_task(QueueItem("2", ""))
        self.assertEqual(self.queue.pop_task().data_instructions, "1")
        self.assertEqual(self.queue.pop_task().data_instructions, "2")
        self.queue.push_task(QueueItem("3", ""))
        self.assertEqual(self.queue.pop_task().data_instructions, "3")

    def test_peek_tasks(self):
        self.queue.push_task(QueueItem("1", ""))
        self.assertEqual(self.queue.peek_task().data_instructions, "1")
        self.queue.push_task(QueueItem("2", ""))
        self.assertEqual(self.queue.peek_task().data_instructions, "1")
        self.queue.pop_task()
        self.assertEqual(self.queue.peek_task().data_instructions, "2")
        
