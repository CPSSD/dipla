from unittest import TestCase
from unittest.mock import MagicMock
from dipla.server.server import ServerEventListener
from dipla.shared.services import ServiceError
from dipla.server.worker_group import WorkerGroup, WorkerFactory
from dipla.shared.network.network_connection import ServerConnection
from pocketmock import create_mock_object


# class ServerTest(TestCase):
#
#     def setUp(self):
#         self.task_queue = TaskQueue()
#         self.binary_manager = BinaryManager()
#         stats = {
#             'num_total_workers': 0,
#             'num_idle_workers': 0
#         }
#         stat_updater = statistics.StatisticsUpdater(stats)
#         self.worker_group = WorkerGroup(stat_updater)
#         self.server = Server(self.task_queue,
#                              self.binary_manager,
#                              self.worker_group,
#                              stat_updater)
#
#         self.sample_data_source = DataSource.create_source_from_iterable(
#           [1, 2, 3, 4], 'foosource')
#
#         self.server_task = Task('footask', 'bar', MachineType.server)
#         self.client_task = Task('footask', 'bar', MachineType.client)
#
#     def test_distribute_tasks_runs_server_task_without_connected_worker(self):
#         self.server_task.add_data_source(self.sample_data_source)
#
#         self.task_queue.push_task(self.server_task)
#         self.server.distribute_tasks()
#         self.assertEqual([1, 2, 3, 4], self.server_task.task_output)
#
#     def test_distribute_tasks_runs_server_task_with_connected_worker(self):
#         self.worker_group.add_worker(Worker('fooworker', None))
#         self.server_task.add_data_source(self.sample_data_source)
#
#         self.task_queue.push_task(self.server_task)
#         self.server.distribute_tasks()
#         self.assertEqual([1, 2, 3, 4], self.server_task.task_output)
#
#     def test_distribute_tasks_runs_client_task_on_connected_worker(self):
#         self.worker_group.add_worker(Worker('fooworker', None))
#         self.client_task.add_data_source(self.sample_data_source)
#
#         self.task_queue.push_task(self.client_task)
#
#         def mock_send(socket, label, data):
#             self.assertEquals([1, 2, 3, 4], data['arguments'][0])
#         self.server.send = mock_send
#
#         self.server.distribute_tasks()
#
#     def test_distribute_tasks_quits_when_no_connected_clients(self):
#         self.client_task.add_data_source(self.sample_data_source)
#         self.task_queue.push_task(self.client_task)
#
#         def mock_send(socket, label, data):
#             self.fail('Distribute Task attempted to send a message but' +
#                       ' should have quit')
#         self.server.send = mock_send
#
#         self.server.distribute_tasks()
#
#     def test_distribute_tasks_runs_client_and_server_tasks_together(self):
#         self.worker_group.add_worker(Worker('fooworker', None))
#         self.client_task.add_data_source(self.sample_data_source)
#         self.server_task.add_data_source(
#         DataSource.create_source_from_iterable([5, 4, 3, 2, 1], 'barsource'))
#
#         self.task_queue.push_task(self.client_task)
#         self.task_queue.push_task(self.server_task)
#
#         def mock_send(socket, label, data):
#             self.assertEquals([1, 2, 3, 4], data['arguments'][0])
#         self.server.send = mock_send
#
#         self.server.distribute_tasks()
#         self.assertEqual([5, 4, 3, 2, 1], self.server_task.task_output)

class ServerTickTest(TestCase):

    def setUp(self):
        self.__instantiate_mock_task_input_distributor()

    def test_task_input_is_distributed(self):
        self.given_a_server()
        self.when_it_ticks()
        self.then_task_input_was_distributed()

    def __instantiate_mock_task_input_distributor(self):
        self.mock_task_input_distributor = create_mock_object(
            TaskInputDistributor
        )


class ServerEventListenerTest(TestCase):

    def setUp(self):
        self.__instantiate_empty_services()
        self.__instantiate_mock_connection()
        self.__instantiate_mock_worker_group()
        self.__instantiate_mock_worker_factory()

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

    def test_worker_uid_generated_when_connection_opens(self):
        self.given_a_server_event_listener()
        self.when_the_connection_is_opened()
        self.then_a_uid_is_generated()

    def test_worker_is_created_when_connection_opens(self):
        self.given_the_uid_generator_returns('abcdef')
        self.given_a_server_event_listener()
        self.when_the_connection_is_opened()
        self.then_a_worker_is_created_with({
            'uid': 'abcdef',
            'connection': self.connection
        })

    def test_worker_is_added_to_worker_group_when_connection_opens(self):
        self.given_the_worker_factory_returns("Fake Worker")
        self.given_a_server_event_listener()
        self.when_the_connection_is_opened()
        self.then_the_worker_is_added_to_worker_group("Fake Worker")

    def test_worker_is_removed_when_connection_closes(self):
        self.given_the_uid_generator_returns('xyz_uid')
        self.given_a_server_event_listener()
        self.when_the_connection_is_opened()
        self.when_the_connection_is_closed()
        self.then_the_worker_is_removed_from_worker_group('xyz_uid')

    def test_worker_is_removed_when_connection_error_occurs(self):
        self.given_the_uid_generator_returns('123_uid')
        self.given_a_server_event_listener()
        self.when_the_connection_is_opened()
        self.when_a_connection_error_occurs()
        self.then_the_worker_is_removed_from_worker_group('123_uid')

    def given_the_services(self, service_names):
        self.services = {}
        for service_name in service_names:
            self.services[service_name] = MagicMock()

    def given_the_worker_factory_returns(self, return_value):
        self.worker_factory.create_from.return_value = return_value

    def given_the_service_will_raise_ServiceError(self, service_name):
        self.services[service_name].side_effect = ServiceError('foo', 0)

    def given_the_service_will_return(self, service_name, return_value):
        self.services[service_name] = MagicMock(return_value=return_value)

    def given_the_uid_generator_returns(self, uid):
        self.worker_group.generate_uid = MagicMock(return_value=uid)

    def given_a_server_event_listener(self):
        self.event_listener = ServerEventListener(
            self.worker_factory,
            self.worker_group,
            self.services
        )

    def when_it_receives(self, message_object):
        self.event_listener.on_message(self.connection, message_object)

    def when_the_connection_is_opened(self):
        message_object = {}
        self.event_listener.on_open(self.connection, message_object)

    def when_the_connection_is_closed(self):
        reason = "I want to close it"
        self.event_listener.on_close(self.connection, reason)

    def when_a_connection_error_occurs(self):
        reason = 'I want to force an error'
        self.event_listener.on_error(self.connection, reason)

    def then_a_uid_is_generated(self):
        self.worker_group.generate_uid.assert_called_with()

    def then_the_result_was_sent_back(self, message_object):
        self.connection.send.assert_called_with(message_object)

    def then_nothing_was_sent_back(self):
        self.assertEqual(0, self.connection.send.call_count)

    def then_the_service_ran(self, service_label, service_data):
        self.services[service_label].assert_called_with(service_data)

    def then_a_worker_is_created_with(self, properties):
        self.worker_factory.create_from.assert_called_with(
            properties['uid'], properties['connection']
        )

    def then_the_worker_is_added_to_worker_group(self, expected_arguments):
        self.worker_group.add_worker.assert_called_with(expected_arguments)

    def then_the_worker_is_removed_from_worker_group(self, expected_arguments):
        self.worker_group.remove_worker.assert_called_with(expected_arguments)

    def __instantiate_mock_connection(self):
        self.connection = create_mock_object(ServerConnection)

    def __instantiate_mock_worker_group(self):
        self.worker_group = create_mock_object(WorkerGroup)

    def __instantiate_empty_services(self):
        self.services = []

    def __instantiate_mock_worker_factory(self):
        self.worker_factory = create_mock_object(WorkerFactory)
