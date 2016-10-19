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

    def test_lease_worker(self):
        self.group.add_worker(Worker("A", 0.75, None))
        self.assertEqual(self.group.lease_worker().uid, "A")
        self.group.add_worker(Worker("B", 0.9, None))
        self.group.add_worker(Worker("C", 0.5, None))
        self.assertEqual(self.group.lease_worker().uid, "C")
        self.assertEqual(self.group.lease_worker().uid, "B")

    def test_return_worker(self):
        self.group.add_worker(Worker("A", 0.75, None))
        self.group.add_worker(Worker("B", 1, None))
        self.group.add_worker(Worker("C", 0.5, None))
        first_uid = self.group.lease_worker().uid
        self.group.return_worker(first_uid)
        second_uid = self.group.lease_worker().uid
        self.assertEqual("C", second_uid)
        
        test_uid = self.group.lease_worker().uid
        self.group.lease_worker()
        self.group.return_worker(test_uid)
        self.assertEqual("A", self.group.lease_worker().uid)

        with self.assertRaises(KeyError):
            self.group.return_worker("Z")
