import unittest
from dipla.server.server import Server, BinaryManager, ServerServices
from dipla.server.result_verifier import ResultVerifier
from dipla.server.task_queue import TaskQueue, Task, DataSource, MachineType
from dipla.server.worker_group import WorkerGroup, Worker
from dipla.shared import statistics


class ServerTest(unittest.TestCase):

    def setUp(self):
        self.task_queue = TaskQueue()
        self.binary_manager = BinaryManager()
        self.result_verifier = ResultVerifier()
        stats = {
            "num_total_workers": 0,
            "num_idle_workers": 0
        }
        stat_updater = statistics.StatisticsUpdater(stats)
        self.worker_group = WorkerGroup(stat_updater)
        self.server = Server(self.task_queue,
                             ServerServices(
                                self.binary_manager,
                                stat_updater),
                             self.result_verifier,
                             self.worker_group,
                             stat_updater)

        self.server.should_distribute_tasks = True

        self.sample_data_source = DataSource.create_source_from_iterable(
          [1, 2, 3, 4], "foosource")

        self.server_task = Task("footask", "bar", MachineType.server)
        self.client_task = Task("footask", "bar", MachineType.client)

    def test_distribute_tasks_runs_server_task_without_connected_worker(self):
        self.server_task.add_data_source(self.sample_data_source)

        self.task_queue.push_task(self.server_task)
        self.server.distribute_tasks()
        self.assertEqual([1, 2, 3, 4], self.server_task.task_output)

    def test_distribute_tasks_runs_server_task_with_connected_worker(self):
        self.worker_group.add_worker(Worker("fooworker", None))
        self.server_task.add_data_source(self.sample_data_source)

        self.task_queue.push_task(self.server_task)
        self.server.distribute_tasks()
        self.assertEqual([1, 2, 3, 4], self.server_task.task_output)

    def test_distribute_tasks_runs_client_task_on_connected_worker(self):
        self.worker_group.add_worker(Worker("fooworker", None))
        self.client_task.add_data_source(self.sample_data_source)

        self.task_queue.push_task(self.client_task)

        def mock_send(socket, label, data):
            self.assertEquals([1], data['arguments'][0])
        self.server.send = mock_send

        self.server.distribute_tasks()

    def test_distribute_tasks_quits_when_no_connected_clients(self):
        self.client_task.add_data_source(self.sample_data_source)
        self.task_queue.push_task(self.client_task)

        def mock_send(socket, label, data):
            self.fail("Distribute Task attempted to send a message but" +
                      " should have quit")
        self.server.send = mock_send

        self.server.distribute_tasks()

    def test_distribute_tasks_runs_client_and_server_tasks_together(self):
        self.worker_group.add_worker(Worker("fooworker", None))
        self.client_task.add_data_source(self.sample_data_source)
        self.server_task.add_data_source(
         DataSource.create_source_from_iterable([5, 4, 3, 2, 1], "barsource"))

        self.task_queue.push_task(self.client_task)
        self.task_queue.push_task(self.server_task)

        def mock_send(socket, label, data):
            self.assertEquals([1, 2, 3, 4], data['arguments'][0])
        self.server.send = mock_send

        self.server.distribute_tasks()
        self.assertEqual([5, 4, 3, 2, 1], self.server_task.task_output)
