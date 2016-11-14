import unittest
from dipla.server import task_queue
from dipla.server.task_queue import Task
from dipla.server.task_queue import TaskQueueEmpty
from dipla.server.task_queue import DataInstruction


class TaskQueueTest(unittest.TestCase):

    def setUp(self):
        self.queue = task_queue.TaskQueue()

    def test_push_task(self):
        d1 = DataInstruction(name="datboi", value=0)
        self.queue.push_task(Task([d1], "task instructions"))
        popped = self.queue.pop_task()
        self.assertEqual(d1.name, popped.data_instructions[0].name)
        self.assertEqual("task instructions", popped.task_instructions)

    def test_pop_tasks(self):
        d1 = DataInstruction(name="lol", value=1)
        d2 = DataInstruction(name="lmao", value=2)
        self.queue.push_task(Task([d1], ""))
        self.queue.push_task(Task([d2], ""))
        self.assertEqual(d1.name, self.queue.pop_task().data_instructions[0].name)
        self.assertEqual(d2.name, self.queue.pop_task().data_instructions[0].name)
        d3 = DataInstruction(name="rofl", value=3)
        self.queue.push_task(Task([d3], ""))
        self.assertEqual(d3.name, self.queue.pop_task().data_instructions[0].name)

        # Test that the container_node attribute is removed
        d4 = DataInstruction(name="xD", value=4)
        self.queue.push_task(Task([d4], ""))
        self.assertFalse(hasattr(self.queue.pop_task(), "container_node"))

    def test_peek_tasks(self):
        d1 = DataInstruction(name="lol", value=1)
        d2 = DataInstruction(name="lmao", value=2)
        self.queue.push_task(Task([d1], ""))
        self.assertEqual(d1.name, self.queue.peek_task().data_instructions[0].name)
        self.queue.push_task(Task([d2], ""))
        self.assertEqual(d1.name, self.queue.peek_task().data_instructions[0].name)
        self.queue.pop_task()
        self.assertEqual(d2.name, self.queue.peek_task().data_instructions[0].name)

    def test_add_result(self):
        # Test task is marked as completed on any result if no check provided
        d1 = DataInstruction(name="john cena", value="do do do dooo")
        test_task = Task([d1], "")
        test_task.add_result("test result")
        self.assertTrue(test_task.completed)

        def check_result_says_done(result):
            return result == "done"

        d2 = DataInstruction(name="it's john cena again", value="haha")
        test_task = Task([d2], "", check_result_says_done)
        test_task.add_result("test result")
        self.assertFalse(test_task.completed)
        test_task.add_result("done")
        self.assertTrue(test_task.completed)

        # Test that task is removed from queue on completion
        d3 = DataInstruction(name="DO DO DO DOOO", value="do do do dooo")
        self.queue.push_task(Task([d3], ""))
        queue_task = self.queue.peek_task()
        queue_task.add_result("done")
        self.assertTrue(queue_task.completed)

        with self.assertRaises(TaskQueueEmpty):
            self.queue.peek_task()
