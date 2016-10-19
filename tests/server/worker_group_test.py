import unittest
from dipla.server import worker_group
from dipla.server.worker_group import Worker


class WorkerGroupTest(unittest.TestCase):

    def setUp(self):
        self.group = worker_group.WorkerGroup() 

    def test_add_worker(self):
        self.group.add_worker(Worker("A", 1, None))
        self.assertCountEqual(self.group.worker_uids(), ["A"])
        self.group.add_worker(Worker("B", 1, None))
        self.assertCountEqual(self.group.worker_uids(), ["A", "B"])

    def test_remove_worker(self):
        self.group.add_worker(Worker("A", 1, None))
        self.group.add_worker(Worker("B", 1, None))
        self.group.remove_worker("A")
        self.assertCountEqual(self.group.worker_uids(), ["B"])
        self.group.remove_worker("B")
        self.assertCountEqual(self.group.worker_uids(), [])
