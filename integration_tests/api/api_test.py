from unittest import TestCase

from dipla.shared import uid_generator
from dipla.api import Dipla
from dipla.shared import uid_generator
from dipla.server.server import Server
from dipla.server.server import BinaryManager
from dipla.server.server_services import ServerServices, ServiceParams
from dipla.server.worker_group import WorkerGroup, Worker


class APIIntegrationTest(TestCase):

    def setUp(self):
        self.old_generate_uid = uid_generator.generate_uid

        next_id = [0]

        def determinable_uid_generator(length, existing_uids):
            next_id[0] = next_id[0] + 1
            return "foo_id " + str(next_id[0])
        uid_generator.generate_uid = determinable_uid_generator

    def test_scoped_task_inputs_contain_correct_arguments(self):
        @Dipla.scoped_distributable(count=3)  # n = 3
        def func(input_value, index, count):
            return None  # This function isn't used in this test

        Dipla.apply_distributable(func, [(1, 12)])
        inputs = []
        while Dipla.task_queue.has_next_input():

            inputs.append(Dipla.task_queue.pop_task_input().values)
        self.assertEquals(3, len(inputs))
        # Should contain 3 intervals, each with the same (1, 12) input
        self.assertEquals(
            [
                [[(1, 12)], [0], [3]],
                [[(1, 12)], [1], [3]],
                [[(1, 12)], [2], [3]]],
            inputs)

    def test_explorer_task_adds_discovered_signal_inputs_to_task_queue(self):
        # This integration test is only testing the integration between
        # the server service for receiving client results and the task
        # queue, this function never runs. It exists to create an
        # explorer task
        @Dipla.explorer()
        @Dipla.distributable()
        def func(inputsA, inputsB):
            return

        # Causes task to register in queue
        inputsA = []
        inputsB = []
        Dipla.apply_distributable(func, inputsA, inputsB)

        server_services = ServerServices(
            BinaryManager(), Dipla.stat_updater)
        service = server_services.get_service("client_result")

        worker_group = WorkerGroup(Dipla.stat_updater)

        server = Server(task_queue=Dipla.task_queue,
                        services=server_services,
                        stats=Dipla.stat_updater,
                        result_verifier=Dipla.result_verifier,
                        worker_group=worker_group)

        # Worker has not influence in test
        worker = Worker("foo", None)
        worker_group.add_worker(worker)
        worker_group.lease_worker()

        message = {
                "task_uid": "foo_id 1",
                "results": [1, 2, 3],
                "signals": {"DISCOVERED": [[[0, 0], [3, 3]]]}
        }

        service(message, ServiceParams(server, worker))
        self.assertEquals([0, 0], inputsA)
        self.assertEquals([3, 3], inputsB)

    def test_chasing_task_inputs_contain_correct_arguments(self):
        @Dipla.chasing_distributable(count=3, chasers=2)
        def func(input_value, previously_computed, index, count):
            return None  # This function isn't used in this test

        input_data = [
          [1, 2, 3],
          [4, 5, 6]
        ]

        Dipla.apply_distributable(func, input_data)
        inputs = []
        while Dipla.task_queue.has_next_input():
            inputs.append(Dipla.task_queue.pop_task_input().values)
        self.assertEquals(3, len(inputs))
        self.assertEquals(
            [
                [[[1, 2, 3]], [None], [0], [3]],
                [[[1, 2, 3]], [None], [1], [3]],
                [[[1, 2, 3]], [None], [2], [3]]],
            inputs)

    def test_second_chaser_in_chasing_task_inputs_contain_correct_arguments(self):  # nopep8

        @Dipla.chasing_distributable(count=3, chasers=2)
        def func(input_value, previously_computed, index, count):
            out = [0, 0, 0]
            out[2-index] = 1
            return out

        input_data = [
          [1, 2, 3],
          [4, 5, 6]
        ]

        Dipla.apply_distributable(func, input_data)
        inputs = []
        while Dipla.task_queue.has_next_input():
            popped_values = Dipla.task_queue.pop_task_input().values
            inputs.append(popped_values)
        Dipla.task_queue.add_result("foo_id 1", [0, 0, 1])
        Dipla.task_queue.add_result("foo_id 1", [0, 1, 0])
        Dipla.task_queue.add_result("foo_id 1", [1, 0, 0])
        while Dipla.task_queue.has_next_input():
            popped_values = Dipla.task_queue.pop_task_input().values
            inputs.append(popped_values)

        self.assertEquals(6, len(inputs))
        self.assertEquals(
            [
                [[[1, 2, 3]], [None], [0], [3]],
                [[[1, 2, 3]], [None], [1], [3]],
                [[[1, 2, 3]], [None], [2], [3]],
                [[[4, 5, 6]], [[0, 0, 1]], [0], [3]],
                [[[4, 5, 6]], [[0, 1, 0]], [1], [3]],
                [[[4, 5, 6]], [[1, 0, 0]], [2], [3]]],
            sorted(inputs))

    def tearDown(self):
        uid_generator.generate_uid = self.old_generate_uid
