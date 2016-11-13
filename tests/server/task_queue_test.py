import unittest
from dipla.server import task_queue
from dipla.server.task_queue import Task
from dipla.server.task_queue import TaskQueueEmpty 


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
        
        # Test that the container_node attribute is removed
        self.queue.push_task(Task("4", ""))
        self.assertFalse(hasattr(self.queue.pop_task(), "container_node"))

    def test_peek_tasks(self):
        self.queue.push_task(Task("1", ""))
        self.assertEqual("1", self.queue.peek_task().data_instructions)
        self.queue.push_task(Task("2", ""))
        self.assertEqual("1", self.queue.peek_task().data_instructions)
        self.queue.pop_task()
        self.assertEqual("2", self.queue.peek_task().data_instructions)

    def test_add_result(self):
       	# Test task is marked as completed on any result if no check provided
        test_task = Task("1", "")
        test_task.add_result("test result")
        self.assertTrue(test_task.completed)

        def check_result_says_done(result):
            return result == "done"

        test_task = Task("2", "", check_result_says_done)
        test_task.add_result("test result")
        self.assertFalse(test_task.completed)
        test_task.add_result("done")
        self.assertTrue(test_task.completed)        

        # Test that task is removed from queue on completion
        self.queue.push_task(Task("3", ""))
        queue_task = self.queue.peek_task()
        queue_task.add_result("done")
        self.assertTrue(queue_task.completed)
        
        with self.assertRaises(TaskQueueEmpty):
            self.queue.peek_task()
