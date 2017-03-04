from unittest import TestCase
from unittest.mock import call
from pocketmock import create_mock_object
from dipla.server.task_queue import TaskQueue, TaskInput, MachineType
from dipla.server.task_distributor import TaskInputDistributor
from dipla.server.task_distributor import VerificationInputStorer
from dipla.server.worker_group import Worker, WorkerGroup
from dipla.shared.network.network_connection import ServerConnection


class TaskInputDistributorTest(TestCase):

    def setUp(self):
        self.__instantiate_mock_worker_group()
        self.__instantiate_mock_task_queue()
        self.__instantiate_mock_verification_input_storer()

    def test_nothing_is_sent_to_worker_when_no_input_is_fetched(self):
        self.given_the_next_task_input_is(None)
        self.given_a_task_input_distributor()
        self.when_distributing()
        self.then_nothing_is_sent_to_worker()

    def test_nothing_is_sent_to_worker_if_task_is_for_server(self):
        self.given_the_next_task_input_is_for_server()
        self.given_a_task_input_distributor()
        self.when_distributing()
        self.then_nothing_is_sent_to_worker()

    def test_task_input_sent_to_worker_if_task_for_client(self):

        mock_task_input = create_mock_object(TaskInput)
        mock_task_input.task_uid = '123_uid'
        mock_task_input.task_instructions = 'do_this_task'
        mock_task_input.machine_type = MachineType.client
        mock_task_input.values = 'cool_values'

        self.given_a_worker_is_available()
        self.given_the_next_task_input_is(mock_task_input)
        self.given_a_task_input_distributor()
        self.when_distributing()
        self.then_the_worker_is_sent({
            'label': 'run_instructions',
            'data': {
                'task_uid': '123_uid',
                'task_instructions': 'do_this_task',
                'arguments': 'cool_values'
            }
        })

    def test_server_task_input_requested_when_no_workers_available(self):
        self.given_no_workers_are_available()
        self.given_server_input_is_available()
        self.given_a_task_input_distributor()
        self.when_distributing()
        self.then_server_task_input_was_taken()

    def test_no_task_input_requested_when_no_workers_or_server_input_available(self):  # nopep8
        self.given_no_workers_are_available()
        self.given_no_server_input_is_available()
        self.given_a_task_input_distributor()
        self.when_distributing()
        self.then_no_task_input_was_taken()

    def test_verification_input_is_not_potentially_stored_for_server_tasks(self):  # nopep8
        self.given_no_workers_are_available()
        self.given_server_input_is_available()
        self.given_a_task_input_distributor()
        self.when_distributing()
        self.then_no_verification_input_was_potentially_stored()

    def test_verification_input_is_potentially_stored_for_client_tasks(self):  # nopep8
        self.given_next_task_input_is_for_client()
        self.given_a_worker_is_available()
        self.given_a_task_input_distributor()
        self.when_distributing()
        self.then_verification_input_was_potentially_stored()

    def test_server_task_input_is_added_to_task_queue_as_results(self):

        def test_1():
            mock_task_input = create_mock_object(TaskInput)
            mock_task_input.task_uid = 'cool_uid'
            mock_task_input.machine_type = MachineType.server
            mock_task_input.values = [[10, 20, 500], 'ignored']

            self.given_no_workers_are_available()
            self.given_the_next_task_input_is(mock_task_input)
            self.given_a_task_input_distributor()
            self.when_distributing()
            self.then_the_result_was_added_to_task_queue(0, 'cool_uid', 10)
            self.then_the_result_was_added_to_task_queue(1, 'cool_uid', 20)
            self.then_the_result_was_added_to_task_queue(2, 'cool_uid', 500)

        def test_2():
            mock_task_input = create_mock_object(TaskInput)
            mock_task_input.task_uid = 'cooler_uid'
            mock_task_input.machine_type = MachineType.server
            mock_task_input.values = [[50, 2, 139, 599], 'ignored']

            self.given_no_workers_are_available()
            self.given_the_next_task_input_is(mock_task_input)
            self.given_a_task_input_distributor()
            self.when_distributing()
            self.then_the_result_was_added_to_task_queue(0, 'cooler_uid', 50)
            self.then_the_result_was_added_to_task_queue(1, 'cooler_uid', 2)
            self.then_the_result_was_added_to_task_queue(2, 'cooler_uid', 139)
            self.then_the_result_was_added_to_task_queue(3, 'cooler_uid', 599)

        for test_method in [test_1, test_2]:
            self.setUp()
            test_method()

    def given_next_task_input_is_for_client(self):
        mock_task_input = create_mock_object(TaskInput)
        mock_task_input.task_uid = '123_uid'
        mock_task_input.task_instructions = 'do_this_task'
        mock_task_input.machine_type = MachineType.client
        mock_task_input.values = 'cool_values'
        self.given_the_next_task_input_is(mock_task_input)

    def given_a_worker_is_available(self): pass

    def given_no_workers_are_available(self):
        self.mock_worker_group.has_available_worker.return_value = False

    def given_server_input_is_available(self):
        def has_next_input(machine_type):
            if machine_type == MachineType.server:
                return True
            else:
                return False
        self.mock_task_queue.has_next_input.side_effect = has_next_input

    def given_no_server_input_is_available(self):
        self.mock_task_queue.has_next_input.return_value = False

    def given_the_next_task_input_is_for_server(self):
        mock_task_input = create_mock_object(TaskInput)
        mock_task_input.task_uid = 'boi_uid'
        mock_task_input.machine_type = MachineType.server
        mock_task_input.values = [[]]
        self.mock_task_queue.pop_task_input.return_value = mock_task_input

    def given_the_next_task_input_is(self, return_value):
        self.mock_task_input = return_value
        self.mock_task_queue.pop_task_input.return_value = return_value

    def given_a_task_input_distributor(self):
        self.task_distributor = TaskInputDistributor(
            self.mock_worker_group,
            self.mock_task_queue,
            self.mock_verification_input_storer
        )

    def when_distributing(self):
        self.task_distributor.distribute_task()

    def then_nothing_is_sent_to_worker(self):
        self.assertEqual(0, self.mock_worker_connection.send.call_count)

    def then_the_worker_is_sent(self, message_object):
        self.mock_worker_connection.send.assert_called_with(message_object)

    def then_server_task_input_was_taken(self):
        pop_method = self.mock_task_queue.pop_task_input
        pop_method.assert_called_with(MachineType.server)

    def then_no_task_input_was_taken(self):
        pop_method = self.mock_task_queue.pop_task_input
        self.assertEqual(0, pop_method.call_count)

    def then_no_verification_input_was_potentially_stored(self):
        method = self.mock_verification_input_storer.potentially_store
        self.assertEqual(0, method.call_count)

    def then_verification_input_was_potentially_stored(self):
        method = self.mock_verification_input_storer.potentially_store
        method.assert_called_with(self.mock_worker, self.mock_task_input)

    def then_the_result_was_added_to_task_queue(self, index, task_uid, result):
        calls = self.mock_task_queue.add_result.mock_calls
        self.assertEqual(call(task_uid, result), calls[index])

    def __instantiate_mock_worker_group(self):
        self.mock_worker_connection = create_mock_object(ServerConnection)

        self.mock_worker = create_mock_object(Worker)
        self.mock_worker.connection = self.mock_worker_connection

        self.mock_worker_group = create_mock_object(WorkerGroup)
        self.mock_worker_group.lease_worker.return_value = self.mock_worker

    def __instantiate_mock_task_queue(self):
        self.mock_task_queue = create_mock_object(TaskQueue)

    def __instantiate_mock_verification_input_storer(self):
        self.mock_verification_input_storer = create_mock_object(
            VerificationInputStorer
        )


class VerificationInputStorerTest(TestCase):

    def setUp(self):
        self.__instantiate_empty_verification_inputs()
        self.__instantiate_mock_task_input()
        self.__instantiate_mock_worker()

    def test_verification_inputs_size_remains_unchanged_when_probability_not_met(self):  # nopep8
        self.given_the_random_number_is(0.8)
        self.given_the_verification_probability_is(0.4)
        self.given_a_verification_input_storer()
        self.when_potentially_storing_task_input()
        self.then_no_input_was_stored()

    def test_verification_inputs_size_remains_unchanged_when_probability_matched_exactly(self):  # nopep8
        self.given_the_random_number_is(0.6)
        self.given_the_verification_probability_is(0.6)
        self.given_a_verification_input_storer()
        self.when_potentially_storing_task_input()
        self.then_no_input_was_stored()

    def test_verification_inputs_size_increases_when_probability_met(self):
        self.given_the_random_number_is(0.49)
        self.given_the_verification_probability_is(0.5)
        self.given_a_verification_input_storer()
        self.when_potentially_storing_task_input()
        self.then_input_was_stored()

    def test_correct_key_is_stored_in_verification_inputs(self):
        self.given_the_probability_will_be_met()
        self.given_the_worker_uid_is('worker_uid')
        self.given_the_task_uid_is('task_uid')
        self.given_a_verification_input_storer()
        self.when_potentially_storing_task_input()
        self.then_the_key_was_stored('worker_uid-task_uid')

    def test_correct_value_is_stored_in_verification_inputs(self):
        self.given_the_probability_will_be_met()
        self.given_the_task_uid_is('this_task_uid')
        self.given_the_task_instructions_are('these_task_instructions_yo')
        self.given_the_task_input_values_are('these_input_values_yo')
        self.given_the_worker_uid_is('bob_the_builder_yo')
        self.given_a_verification_input_storer()
        self.when_potentially_storing_task_input()
        self.then_the_verification_input_exists(
            'bob_the_builder_yo-this_task_uid',
            {
                'task_instructions': 'these_task_instructions_yo',
                'inputs': 'these_input_values_yo',
                'original_worker_uid': 'bob_the_builder_yo'
            }
        )

    def test_multiple_verification_inputs_can_be_stored(self):
        self.given_the_probability_will_be_met()
        self.given_a_verification_input_storer()

        self.given_the_task_uid_is('task_1')
        self.given_the_task_instructions_are('instructions_1')
        self.given_the_task_input_values_are('values_1')
        self.given_the_worker_uid_is('worker_1')
        self.when_potentially_storing_task_input()

        self.given_the_task_uid_is('task_2')
        self.given_the_task_instructions_are('instructions_2')
        self.given_the_task_input_values_are('values_2')
        self.given_the_worker_uid_is('worker_2')
        self.when_potentially_storing_task_input()

        self.then_the_verification_input_exists(
            'worker_1-task_1',
            {
                'task_instructions': 'instructions_1',
                'inputs': 'values_1',
                'original_worker_uid': 'worker_1'
            }
        )
        self.then_the_verification_input_exists(
            'worker_2-task_2',
            {
                'task_instructions': 'instructions_2',
                'inputs': 'values_2',
                'original_worker_uid': 'worker_2'
            }
        )

    def given_the_random_number_is(self, random_number):
        def random_number_function():
            return random_number
        self.random_number_function = random_number_function

    def given_the_verification_probability_is(self, verification_probability):
        self.verification_probability = verification_probability

    def given_the_task_instructions_are(self, task_instructions):
        self.mock_task_input.task_instructions = task_instructions

    def given_the_task_input_values_are(self, task_input_values):
        self.mock_task_input.values = task_input_values

    def given_the_worker_uid_is(self, uid):
        self.mock_worker.uid = uid

    def given_the_task_uid_is(self, uid):
        self.mock_task_input.task_uid = uid

    def given_the_probability_will_be_met(self):
        self.given_the_random_number_is(0)
        self.given_the_verification_probability_is(1)

    def given_a_verification_input_storer(self):
        self.verification_input_storer = VerificationInputStorer(
            self.verification_inputs,
            self.verification_probability,
            self.random_number_function
        )

    def when_potentially_storing_task_input(self):
        self.verification_input_storer.potentially_store(
            self.mock_worker,
            self.mock_task_input
        )

    def then_no_input_was_stored(self):
        self.assertEqual(0, len(self.verification_inputs))

    def then_input_was_stored(self):
        self.assertEqual(1, len(self.verification_inputs))

    def then_the_key_was_stored(self, key):
        self.assertIn(key, self.verification_inputs)

    def then_the_verification_input_exists(self, key, value):
        verification_input = self.verification_inputs[key]
        self.assertEqual(value, verification_input)

    def __instantiate_empty_verification_inputs(self):
        self.verification_inputs = {}

    def __instantiate_mock_task_input(self):
        self.mock_task_input = create_mock_object(TaskInput)

    def __instantiate_mock_worker(self):
        self.mock_worker = create_mock_object(Worker)
