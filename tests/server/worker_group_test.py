import unittest
from dipla.server import worker_group
from dipla.server.worker_group import Worker


class WorkerGroupTest(unittest.TestCase):

    def setUp(self):
        self.group = worker_group.WorkerGroup()

    def test_add_worker(self):
        self.group.add_worker(Worker("A", None, 1))
        self.assertCountEqual(["A"], self.group.worker_uids())
        self.group.add_worker(Worker("B", None, 1))
        self.assertCountEqual(["A", "B"], self.group.worker_uids())

        with self.assertRaises(ValueError):
            self.group.add_worker(Worker("A", None, 1))

    def test_remove_worker(self):
        self.group.add_worker(Worker("A", None, 1))
        self.group.add_worker(Worker("B", None, 1))
        self.group.remove_worker("A")
        self.assertCountEqual(["B"], self.group.worker_uids())
        self.group.remove_worker("B")
        self.assertCountEqual([], self.group.worker_uids())

        with self.assertRaises(KeyError):
            self.group.remove_worker("A")

    def test_lease_worker(self):
        self.group.add_worker(Worker("A", None, quality=0.75))
        self.assertEqual(self.group.lease_worker().uid, "A")
        self.group.add_worker(Worker("B", None, quality=0.9))
        self.group.add_worker(Worker("C", None, quality=0.5))
        self.assertEqual("C", self.group.lease_worker().uid)
        self.assertEqual("B", self.group.lease_worker().uid)

        with self.assertRaises(IndexError):
            self.group.lease_worker()

    def test_return_worker(self):
        self.group.add_worker(Worker("A", None, quality=0.75))
        self.group.add_worker(Worker("B", None, quality=1))
        self.group.add_worker(Worker("C", None, quality=0.5))
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
