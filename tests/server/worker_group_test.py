import unittest
from dipla.server import worker_group
from dipla.server.worker_group import Worker, WorkerFactory
from dipla.shared import statistics
from tests.utils import create_mock_object


class WorkerGroupTest(unittest.TestCase):

    def setUp(self):
        stats = {
            "num_total_workers": 0,
            "num_idle_workers": 0,
        }
        stat_updater = statistics.StatisticsUpdater(stats)
        self.group = worker_group.WorkerGroup(stat_updater)

        self.stat_reader = statistics.StatisticsReader(stats)

    def test_add_worker(self):
        self.group.add_worker(Worker("A", None, 1))
        self.assertCountEqual(["A"], self.group.worker_uids())
        self.assertEqual(1, self.stat_reader.read("num_total_workers"))
        self.assertEqual(1, self.stat_reader.read("num_idle_workers"))
        self.group.add_worker(Worker("B", None, 1))
        self.assertCountEqual(["A", "B"], self.group.worker_uids())
        self.assertEqual(2, self.stat_reader.read("num_total_workers"))
        self.assertEqual(2, self.stat_reader.read("num_idle_workers"))

        with self.assertRaises(ValueError):
            self.group.add_worker(Worker("A", None, 1))

    def test_remove_worker(self):
        self.group.add_worker(Worker("A", None, 1))
        self.group.add_worker(Worker("B", None, 1))
        self.group.remove_worker("A")
        self.assertCountEqual(["B"], self.group.worker_uids())
        self.assertEqual(1, self.stat_reader.read("num_total_workers"))
        self.assertEqual(1, self.stat_reader.read("num_idle_workers"))
        self.group.remove_worker("B")
        self.assertCountEqual([], self.group.worker_uids())
        self.assertEqual(0, self.stat_reader.read("num_total_workers"))
        self.assertEqual(0, self.stat_reader.read("num_idle_workers"))

        with self.assertRaises(KeyError):
            self.group.remove_worker("A")

    def test_lease_worker(self):
        self.group.add_worker(Worker("A", None, quality=0.75))
        self.assertEqual(self.group.lease_worker().uid, "A")
        self.assertEqual(1, self.stat_reader.read("num_total_workers"))
        self.assertEqual(0, self.stat_reader.read("num_idle_workers"))
        self.group.add_worker(Worker("B", None, quality=0.9))
        self.group.add_worker(Worker("C", None, quality=0.5))
        self.assertEqual("C", self.group.lease_worker().uid)
        self.assertEqual("B", self.group.lease_worker().uid)
        self.assertEqual(3, self.stat_reader.read("num_total_workers"))
        self.assertEqual(0, self.stat_reader.read("num_idle_workers"))

        with self.assertRaises(IndexError):
            self.group.lease_worker()

    def test_return_worker(self):
        self.group.add_worker(Worker("A", None, quality=0.75))
        self.group.add_worker(Worker("B", None, quality=1))
        self.group.add_worker(Worker("C", None, quality=0.5))
        self.assertEqual(3, self.stat_reader.read("num_total_workers"))
        self.assertEqual(3, self.stat_reader.read("num_idle_workers"))
        first_uid = self.group.lease_worker().uid
        self.group.return_worker(first_uid)
        second_uid = self.group.lease_worker().uid
        self.assertEqual("C", second_uid)
        self.assertEqual(3, self.stat_reader.read("num_total_workers"))
        self.assertEqual(2, self.stat_reader.read("num_idle_workers"))

        test_uid = self.group.lease_worker().uid
        self.group.lease_worker()
        self.group.return_worker(test_uid)
        self.assertEqual("A", self.group.lease_worker().uid)

        with self.assertRaises(KeyError):
            self.group.return_worker("Z")


class WorkerFactoryTest(unittest.TestCase):

    def test_that_it_creates_a_worker(self):
        self.given_a_worker_factory()
        self.given_the_uid('abc_uid')
        self.given_a_mocked_connection()
        self.when_creating_worker()
        self.then_the_worker_has_the_uid('abc_uid')
        self.then_the_worker_has_the_mocked_connection()

    def given_a_worker_factory(self):
        self.factory = WorkerFactory()

    def given_the_uid(self, uid):
        self.uid = uid

    def given_a_mocked_connection(self):
        self.connection = create_mock_object([])

    def when_creating_worker(self):
        self.worker = self.factory.create_from(self.uid, self.connection)

    def then_the_worker_has_the_uid(self, expected):
        self.assertEqual(expected, self.worker.uid)

    def then_the_worker_has_the_mocked_connection(self):
        self.assertEqual(self.connection, self.worker.connection)
