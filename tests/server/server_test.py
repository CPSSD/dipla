import unittest
from collections import namedtuple
from unittest.mock import MagicMock

from dipla.server.server import Server, BinaryManager, ServerEventListener
from dipla.server.task_queue import TaskQueue, Task, DataSource, MachineType
from dipla.server.worker_group import WorkerGroup, Worker
from dipla.shared import statistics
from dipla.shared.services import ServiceError


class ServerTest(unittest.TestCase):

    def setUp(self):
        self.task_queue = TaskQueue()
        self.binary_manager = BinaryManager()
        stats = {
            'num_total_workers': 0,
            'num_idle_workers': 0
        }
        stat_updater = statistics.StatisticsUpdater(stats)
        self.worker_group = WorkerGroup(stat_updater)
        self.server = Server(self.task_queue,
                             self.binary_manager,
                             self.worker_group,
                             stat_updater)

        self.sample_data_source = DataSource.create_source_from_iterable(
          [1, 2, 3, 4], 'foosource')

        self.server_task = Task('footask', 'bar', MachineType.server)
        self.client_task = Task('footask', 'bar', MachineType.client)

    def test_distribute_tasks_runs_server_task_without_connected_worker(self):
        self.server_task.add_data_source(self.sample_data_source)

        self.task_queue.push_task(self.server_task)
        self.server.distribute_tasks()
        self.assertEqual([1, 2, 3, 4], self.server_task.task_output)

    def test_distribute_tasks_runs_server_task_with_connected_worker(self):
        self.worker_group.add_worker(Worker('fooworker', None))
        self.server_task.add_data_source(self.sample_data_source)

        self.task_queue.push_task(self.server_task)
        self.server.distribute_tasks()
        self.assertEqual([1, 2, 3, 4], self.server_task.task_output)

    def test_distribute_tasks_runs_client_task_on_connected_worker(self):
        self.worker_group.add_worker(Worker('fooworker', None))
        self.client_task.add_data_source(self.sample_data_source)

        self.task_queue.push_task(self.client_task)

        def mock_send(socket, label, data):
            self.assertEquals([1, 2, 3, 4], data['arguments'][0])
        self.server.send = mock_send

        self.server.distribute_tasks()

    def test_distribute_tasks_quits_when_no_connected_clients(self):
        self.client_task.add_data_source(self.sample_data_source)
        self.task_queue.push_task(self.client_task)

        def mock_send(socket, label, data):
            self.fail('Distribute Task attempted to send a message but' +
                      ' should have quit')
        self.server.send = mock_send

        self.server.distribute_tasks()

    def test_distribute_tasks_runs_client_and_server_tasks_together(self):
        self.worker_group.add_worker(Worker('fooworker', None))
        self.client_task.add_data_source(self.sample_data_source)
        self.server_task.add_data_source(
         DataSource.create_source_from_iterable([5, 4, 3, 2, 1], 'barsource'))

        self.task_queue.push_task(self.client_task)
        self.task_queue.push_task(self.server_task)

        def mock_send(socket, label, data):
            self.assertEquals([1, 2, 3, 4], data['arguments'][0])
        self.server.send = mock_send

        self.server.distribute_tasks()
        self.assertEqual([5, 4, 3, 2, 1], self.server_task.task_output)


class ServerEventListenerTest(unittest.TestCase):

    def test_relevant_service_runs_when_message_received(self):
        self.given_the_services(['foo_service', 'bar_service'])
        self.given_a_server_event_listener()
        self.when_it_receives({'label': 'foo_service', 'data': 'xyz'})
        self.then_the_service_ran('foo_service', 'xyz')
    
    def test_service_result_is_sent_back(self):
        self.given_the_services(['foo_service'])
        self.given_the_service_will_return('foo_service', {'x': 'ARBITRARY'})
        self.given_a_server_event_listener()
        self.when_it_receives({'label': 'foo_service', 'data': 'xyz'})
        self.then_the_result_was_sent_back({'x': 'ARBITRARY'})

    def test_nothing_is_sent_back_if_service_returns_nothing(self):
        self.given_the_services(['cool_service'])
        self.given_the_service_will_return('cool_service', None)
        self.given_a_server_event_listener()
        self.when_it_receives({'label': 'cool_service', 'data': 'whatever'})
        self.then_nothing_was_sent_back()

    def test_runtime_error_is_sent_back_if_ServiceError_is_raised(self):
        self.given_the_services(['cool_service'])
        self.given_the_service_will_raise_ServiceError('cool_service')
        self.given_a_server_event_listener()
        self.when_it_receives({'label': 'cool_service', 'data': 'abc'})
        self.then_the_result_was_sent_back({
            'label': 'runtime_error',
            'data': {
                'details': 'foo',
                'code': 0
            }
        })

    def given_the_services(self, service_names):
        self.services = {}
        for service_name in service_names:
            self.services[service_name] = MagicMock()

    def given_the_service_will_raise_ServiceError(self, service_name):
        self.services[service_name].side_effect = ServiceError('foo', 0)

    def given_the_service_will_return(self, service_name, return_value):
        self.services[service_name] = MagicMock(return_value=return_value)

    def given_a_server_event_listener(self):
        self.connection = namedtuple('MockObject', 'send')
        self.connection.send = MagicMock()
        self.event_listener = ServerEventListener(self.services)

    def when_it_receives(self, message_object):
        self.event_listener.on_message(self.connection, message_object)

    def then_the_result_was_sent_back(self, message_object):
        self.connection.send.assert_called_with(message_object)

    def then_nothing_was_sent_back(self):
        self.assertEqual(0, self.connection.send.call_count)

    def then_the_service_ran(self, service_label, service_data):
        self.services[service_label].assert_called_with(service_data)
