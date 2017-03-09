from unittest import TestCase
from unittest.mock import MagicMock
from dipla.server.server import ServerEventListener, Server
from dipla.shared.services import ServiceError
from dipla.server.worker_group import WorkerGroup, WorkerFactory
from dipla.shared.network.network_connection import ServerConnection
from pocketmock import create_mock_object
from dipla.server.task_queue import TaskQueue
from dipla.server.task_distribution import TaskInputDistributor
from dipla.shared.network.server_connection_provider import \
     ServerConnectionProvider


class ServerTest(TestCase):

    def setUp(self):
        self.__instantiate_mock_server_connection_provider()
        self.__instantiate_mock_task_queue()
        self.__instantiate_mock_task_input_distributor()

    def test_repeatedly_ticks_once_started(self):
        self.given_task_queue_is_active_for_three_ticks()
        self.given_a_server()
        self.given_the_tick_is_mocked()
        self.when_started()
        self.then_it_ticked_three_times()

    def test_task_input_is_distributed_each_tick(self):
        self.given_a_server()
        self.when_it_ticks()
        self.then_task_input_was_distributed()

    def test_everything_stops_when_task_queue_is_inactive(self):
        self.given_a_server()
        self.given_the_task_queue_is_inactive()
        self.when_started()
        self.then_everything_was_stopped()

    def test_server_connection_provider_starts_when_started(self):
        self.given_a_server()
        self.when_started()
        self.then_server_connection_provider_started()

    def given_a_server(self):
        self.server = Server(
            self.mock_server_connection_provider,
            self.mock_task_queue,
            self.mock_task_input_distributor
        )

    def given_the_tick_is_mocked(self):
        self.server.tick = MagicMock()

    def given_the_task_queue_is_inactive(self):
        self.mock_task_queue.is_inactive.return_value = True

    def given_task_queue_is_active_for_three_ticks(self):
        f = False
        self.mock_task_queue.is_inactive.side_effect = [f, f, f, True]

    def when_it_ticks(self):
        self.server.tick()

    def when_started(self):
        self.server.start()

    def then_task_input_was_distributed(self):
        method = self.mock_task_input_distributor.distribute_task_input
        self.assertEqual(1, method.call_count)

    def then_everything_was_stopped(self):
        method = self.mock_server_connection_provider.stop
        self.assertEqual(1, method.call_count)

    def then_it_ticked_three_times(self):
        # noinspection PyUnresolvedReferences
        self.assertEqual(3, self.server.tick.call_count)

    def then_server_connection_provider_started(self):
        method = self.mock_server_connection_provider.start
        self.assertEqual(1, method.call_count)

    def __instantiate_mock_task_input_distributor(self):
        self.mock_task_input_distributor = create_mock_object(
            TaskInputDistributor
        )

    def __instantiate_mock_server_connection_provider(self):
        self.mock_server_connection_provider = create_mock_object(
            ServerConnectionProvider
        )

    def __instantiate_mock_task_queue(self):
        self.mock_task_queue = create_mock_object(TaskQueue)


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
        self.given_the_worker_uids_are('xyz_uid')
        self.given_the_uid_generator_returns('xyz_uid')
        self.given_a_server_event_listener()
        self.when_the_connection_is_opened()
        self.when_the_connection_is_closed()
        self.then_the_worker_is_removed_from_worker_group('xyz_uid')

    def test_worker_is_removed_when_connection_error_occurs(self):
        self.given_the_worker_uids_are('123_uid')
        self.given_the_uid_generator_returns('123_uid')
        self.given_a_server_event_listener()
        self.when_the_connection_is_opened()
        self.when_a_connection_error_occurs()
        self.then_the_worker_is_removed_from_worker_group('123_uid')

    def test_worker_not_removed_if_does_not_exist(self):
        self.given_worker_group_has_no_workers()
        self.given_the_uid_generator_returns('abc_uid')
        self.given_a_server_event_listener()
        self.when_the_connection_is_opened()
        self.when_the_connection_is_closed()
        self.then_no_worker_was_removed()

    def given_the_worker_uids_are(self, uids):
        self.worker_group.worker_uids.return_value = uids

    def given_worker_group_has_no_workers(self):
        self.worker_group.worker_uids.return_value = []

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

    def then_no_worker_was_removed(self):
        method = self.worker_group.remove_worker
        self.assertEqual(0, method.call_count)

    def __instantiate_mock_connection(self):
        self.connection = create_mock_object(ServerConnection)

    def __instantiate_mock_worker_group(self):
        self.worker_group = create_mock_object(WorkerGroup)

    def __instantiate_empty_services(self):
        self.services = []

    def __instantiate_mock_worker_factory(self):
        self.worker_factory = create_mock_object(WorkerFactory)
