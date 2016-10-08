import unittest
from dipla.server import task_queue

class TaskQueueTest(unittest.TestCase):
    
    def test_add_task(self):
        queue = task_queue.TaskQueue()
        queue.add_task("data instructions", "task instructions")
        popped = queue.pop_task()
        self.assertEqual(popped.data_instructions, "data instructions")
        self.assertEqual(popped.task_instructions, "task instructions")

    def test_pop_tasks(self):
        queue = task_queue.TaskQueue()
        queue.add_task("1", "")
        queue.add_task("2", "")
        self.assertEqual(queue.pop_task().data_instructions, "1")
        self.assertEqual(queue.pop_task().data_instructions, "2")
        queue.add_task("3", "")
        self.assertEqual(queue.pop_task().data_instructions, "3")
