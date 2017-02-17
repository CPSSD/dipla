import socket
import unittest
from dipla.shared.network.network_connection import ClientConnection
from dipla.shared.network.network_connection import ServerConnection
from .useful_assertions import *
from .useful_event_listeners import EchoEventListener
from .useful_event_listeners import EventSavingEventListener


ASSERTION_TIMEOUT = 10


class ClientConnectionTest(unittest.TestCase):

    def test_that_client_connection_can_be_established_and_stopped(self):
        self.given_running_server_connection()
        self.given_client_connection()
        self.when_client_connection_starts()
        self.then_client_is_connected()
        self.when_client_connection_stops()
        self.then_client_not_connected()

    def test_that_client_connection_can_stop_before_established(self):
        self.given_client_connection()
        self.when_client_connection_starts()
        self.then_client_not_connected()
        self.when_client_connection_stops()
        self.then_client_not_connected()

    def test_that_client_connection_can_stop_after_established(self):
        self.given_running_server_connection()
        self.given_client_connection()
        self.when_client_connection_starts()
        self.then_client_is_connected()
        self.when_client_connection_stops()
        self.then_client_not_connected()

    def test_that_client_connection_can_send_messages(self):
        self.given_running_server_connection()
        self.given_client_connection()
        self.then_server_connection_receives_nothing()
        self.when_client_connection_starts()
        self.when_client_connection_sends("Foo")
        self.then_server_connection_receives_something()

    def test_that_client_connection_can_send_legible_messages(self):
        self.given_running_server_connection()
        self.given_client_connection()
        self.then_server_connection_receives_nothing()
        self.when_client_connection_starts()
        self.when_client_connection_sends("Foo")
        self.then_server_connection_receives("Foo")

    def test_that_client_connection_can_receive_legible_message(self):
        self.given_running_server_connection()
        self.given_client_connection()
        self.then_server_connection_receives_nothing()
        self.when_client_connection_starts()
        self.when_client_connection_sends("Foo")
        self.then_client_receives("Echo: Foo")

    def test_that_client_event_listener_receives_no_errors_upon_normal_connection(self):  # nopep8
        self.given_running_server_connection()
        self.given_client_connection()
        self.when_client_connection_starts()
        self.then_client_receives_no_errors()

    def test_that_client_event_listener_receives_connection_refused_error_without_server(self):  # nopep8
        self.given_server_is_offline()
        self.given_client_connection()
        self.when_client_connection_starts()
        self.then_client_receives_connection_refused_error()

    def test_that_client_event_listener_receives_close_notification_when_client_stopped(self):  # nopep8
        self.given_running_server_connection()
        self.given_client_connection()
        self.when_client_connection_starts()
        self.when_client_connection_stops()
        self.then_client_receives_close_notification()

    def test_that_client_event_listener_receives_close_notification_when_server_stopped(self):  # nopep8
        self.given_running_server_connection()
        self.given_client_connection()
        self.when_client_connection_starts()
        self.when_server_connection_stops()
        self.then_client_receives_close_notification()

    def test_that_client_event_listener_receives_close_notification_after_prolonged_connection_stopped(self):  # nopep8
        self.given_running_server_connection()
        self.given_client_connection()
        self.when_client_connection_starts()
        self.then_client_does_not_receive_close_notification()
        self.when_client_connection_stops()
        self.then_client_receives_close_notification()

    def test_that_client_connection_with_wrong_port_number_cannot_connect_to_server(self):  # nopep8
        self.given_a_running_server_connection_on_port(13377)
        self.given_a_client_connecting_to_port(11011)
        self.when_client_connection_starts()
        self.then_client_receives_connection_refused_error()

    def test_that_client_connection_to_server_can_be_established_on_different_port(self):  # nopep8
        self.given_a_running_server_connection_on_port(13377)
        self.given_a_client_connecting_to_port(13377)
        self.when_client_connection_starts()
        self.then_client_is_connected()

    def test_that_client_connection_stops_after_client_sends_corrupted_header(self):  # nopep8
        self.given_running_server_connection()
        self.given_client_connection()
        self.when_client_connection_starts()
        self.then_client_is_connected()
        self.when_client_connection_directly_sends("f:foo")
        self.then_client_not_connected()

    def test_that_client_connection_stops_after_server_sends_corrupted_header(self):  # nopep8
        self.given_running_server_connection()
        self.given_client_connection()
        self.when_client_connection_starts()
        self.then_client_is_connected()
        self.when_server_connection_directly_sends("f:foo")
        self.then_client_not_connected()

    def test_that_client_connection_can_send_multiple_messages(self):
        self.given_running_server_connection()
        self.given_client_connection()
        self.when_client_connection_starts()
        self.when_client_connection_sends("Hello")
        self.then_server_connection_receives("Hello")
        self.when_client_connection_sends("World!")
        self.then_server_connection_receives("World!")

    def test_that_client_event_listener_receives_open_notification_upon_connecting(self):  # nopep8
        self.given_running_server_connection()
        self.given_client_connection()
        self.then_client_does_not_receive_open_notification()
        self.when_client_connection_starts()
        self.then_client_receives_open_notification()

    def given_server_is_offline(self):
        pass

    def given_running_server_connection(self):
        self.given_a_running_server_connection_on_port(51111)

    def given_client_connection(self):
        self.given_a_client_connecting_to_port(51111)

    def given_a_client_connecting_to_port(self, port):
        self.given_a_client_connecting_to('localhost', port)

    def given_a_client_connecting_to(self, address, port):
        event_listener = EventSavingEventListener()
        self.client_connection = ClientConnection(address,
                                                  port,
                                                  event_listener)
        self.client_event_listener = event_listener

    def given_a_running_server_connection_on_port(self, port):
        event_listener = EchoEventListener()

        socket_ = get_bound_socket(port)

        self.server_connection = ServerConnection(socket_, event_listener)
        self.server_connection.start()
        self.server_event_listener = event_listener

    def when_client_connection_starts(self):
        self.client_connection.start()

    def when_client_connection_stops(self):
        self.client_connection.stop()

    def when_server_connection_stops(self):
        self.server_connection.stop()

    def when_client_connection_directly_sends(self, message):
        self.client_connection._attempt_send_with_timeout(message)

    def when_server_connection_directly_sends(self, message):
        self.server_connection._attempt_send_with_timeout(message)

    def then_client_does_not_receive_open_notification(self):
        assert_event_listener_receives_no_open_notification(
            self,
            self.client_event_listener,
            ASSERTION_TIMEOUT
        )

    def then_client_receives_open_notification(self):
        assert_event_listener_receives_open_notification(
            self,
            self.client_event_listener,
            ASSERTION_TIMEOUT
        )

    def then_client_is_connected(self):
        assert_is_connected(
            self,
            self.client_connection,
            ASSERTION_TIMEOUT
        )

    def then_client_not_connected(self):
        assert_not_connected(
            self,
            self.client_connection,
            ASSERTION_TIMEOUT
        )

    def when_client_connection_sends(self, message):
        self.client_connection.send(message)

    def then_server_connection_receives_something(self):
        assert_event_listener_receives_something(
            self,
            self.server_event_listener,
            ASSERTION_TIMEOUT
        )

    def then_server_connection_receives_nothing(self):
        assert_event_listener_receives_nothing(
            self,
            self.server_event_listener,
            ASSERTION_TIMEOUT
        )

    def then_server_connection_receives(self, message):
        assert_event_listener_receives(
            self,
            self.server_event_listener,
            message,
            ASSERTION_TIMEOUT
        )

    def then_client_receives(self, message):
        assert_event_listener_receives(
            self,
            self.client_event_listener,
            message,
            ASSERTION_TIMEOUT
        )

    def then_client_receives_no_errors(self):
        assert_event_listener_receives_no_errors(
            self,
            self.client_event_listener,
            ASSERTION_TIMEOUT
        )

    def then_client_receives_connection_refused_error(self):
        assert_event_listener_receives_connection_refused(
            self,
            self.client_event_listener,
            ASSERTION_TIMEOUT
        )

    def then_client_receives_close_notification(self):
        assert_event_listener_receives_close_notification(
            self,
            self.client_event_listener,
            ASSERTION_TIMEOUT
        )

    def then_client_does_not_receive_close_notification(self):
        assert_event_listener_receives_no_close_notification(
            self,
            self.client_event_listener,
            ASSERTION_TIMEOUT
        )

    def tearDown(self):
        try:
            blindly_stop(self.server_connection)
        except AttributeError:
            pass
        try:
            blindly_stop(self.client_connection)
        except AttributeError:
            pass


class ServerConnectionTest(unittest.TestCase):

    def test_that_server_connection_can_start_and_stop(self):
        self.given_a_server_connection()
        self.when_listening_for_client_connection()
        self.then_server_connection_is_running()
        self.when_server_connection_stops()
        self.then_server_is_not_running()

    def test_that_server_connection_can_stop_after_established(self):
        self.given_a_server_connection()
        self.when_listening_for_client_connection()
        self.when_client_connects()
        self.when_server_connection_stops()
        self.then_server_is_not_running()

    def test_that_server_connection_can_send_messages(self):
        self.given_a_server_connection()
        self.when_listening_for_client_connection()
        self.when_client_connects()
        self.when_server_connection_sends("Hello")
        self.then_client_receives_something()

    def test_that_server_connection_can_send_legible_messages(self):
        self.given_a_server_connection()
        self.when_listening_for_client_connection()
        self.when_client_connects()
        self.when_server_connection_sends("Hello")
        self.then_client_connection_receives("Hello")

    def test_that_server_connection_can_receive_legible_messages(self):
        self.given_a_server_connection()
        self.when_listening_for_client_connection()
        self.when_client_connects()
        self.when_client_connection_sends("Hello")
        self.then_server_receives("Hello")

    def test_that_server_event_listener_receives_close_notification_when_server_stopped(self):  # nopep8
        self.given_a_server_connection()
        self.when_listening_for_client_connection()
        self.when_client_connects()
        self.when_server_connection_stops()
        self.then_server_receives_close_notification()

    def test_that_server_event_listener_receives_close_notification_when_client_stopped(self):  # nopep8
        self.given_a_server_connection()
        self.when_listening_for_client_connection()
        self.when_client_connects()
        self.then_server_does_not_receive_close_notification()
        self.when_client_connection_stops()
        self.then_server_receives_close_notification()

    def test_that_server_event_listener_receives_close_notification_after_prolonged_connection(self):  # nopep8
        self.given_a_server_connection()
        self.when_listening_for_client_connection()
        self.then_server_does_not_receive_close_notification()
        self.when_server_connection_stops()
        self.then_server_receives_close_notification()

    def test_that_server_event_listener_receives_no_errors_upon_normal_connection(self):  # nopep8
        self.given_a_server_connection()
        self.when_listening_for_client_connection()
        self.when_client_connects()
        self.then_server_receives_no_errors()

    def test_that_server_connection_to_client_can_be_established_on_different_port(self):  # nopep8
        self.given_a_server_connection_on_port(13377)
        self.when_listening_for_client_connection()
        self.when_client_connects_on_port(13377)

    def test_that_server_connection_can_receive_larger_messages_than_buffer_size(self):  # nopep8
        self.given_a_server_connection()
        self.when_listening_for_client_connection()
        self.when_client_connects()
        self.when_client_sends_number_of_bytes(250)
        self.then_server_receives_number_of_bytes(250)

    def test_that_server_connection_stops_after_client_sends_corrupted_header(self):  # nopep8
        self.given_a_server_connection()
        self.when_listening_for_client_connection()
        self.when_client_connects()
        self.then_server_is_connected()
        self.when_client_connection_directly_sends("f:foo")
        self.then_server_not_connected()

    def test_that_server_connection_stops_after_server_sends_corrupted_header(self):  # nopep8
        self.given_a_server_connection()
        self.when_listening_for_client_connection()
        self.when_client_connects()
        self.then_server_is_connected()
        self.when_server_connection_directly_sends("f:foo")
        self.then_server_not_connected()

    def test_that_server_connection_can_send_multiple_messages(self):
        self.given_a_server_connection()
        self.when_listening_for_client_connection()
        self.when_client_connects()
        self.when_server_connection_sends("Hello")
        self.then_client_connection_receives("Hello")
        self.when_server_connection_sends("World!")
        self.then_client_connection_receives("World!")

    def test_that_server_event_listener_receives_open_notification_when_connection_established(self):  # nopep8
        self.given_a_server_connection()
        self.when_listening_for_client_connection()
        self.then_server_does_not_receive_open_notification()
        self.when_client_connects()
        self.then_server_receives_open_notification()

    def test_that_server_event_listener_can_send_messages_while_receiving_large_amounts_of_data(self):  # nopep8
        self.given_a_server_connection()
        self.when_listening_for_client_connection()
        self.when_client_connects()
        self.then_server_receives_open_notification()
        self.when_client_sends_number_of_bytes(5000)
        self.when_server_connection_sends("Hello")
        self.then_client_connection_receives("Hello")
        self.when_server_connection_sends("World!")
        self.then_client_connection_receives("World!")
        self.then_server_receives_number_of_bytes(5000)

    def given_a_server_connection(self):
        self.given_a_server_connection_on_port(51111)

    def given_a_server_connection_on_port(self, port):
        event_listener = EventSavingEventListener()
        socket_ = get_bound_socket(port)
        self.server_connection = ServerConnection(socket_, event_listener)
        self.server_event_listener = event_listener

    def when_listening_for_client_connection(self):
        self.server_connection.start()

    def when_client_connects(self):
        self.when_client_connects_on_port(51111)

    def when_client_connects_on_port(self, port):
        event_listener = EventSavingEventListener()
        self.client_connection = ClientConnection('localhost',
                                                  port,
                                                  event_listener)
        self.client_connection.start()
        self.client_event_listener = event_listener

    def when_server_connection_stops(self):
        self.server_connection.stop()

    def when_server_connection_sends(self, message):
        self.server_connection.send(message)

    def when_client_connection_stops(self):
        self.client_connection.stop()

    def when_client_connection_sends(self, message):
        self.client_connection.send(message)

    def when_client_connection_directly_sends(self, message):
        self.client_connection._attempt_send_with_timeout(message)

    def when_server_connection_directly_sends(self, message):
        self.server_connection._attempt_send_with_timeout(message)

    def when_client_sends_number_of_bytes(self, num_of_bytes):
        bytes_to_send = generate_bytes(num_of_bytes)
        self.client_connection.send(bytes_to_send)

    def then_server_connection_is_running(self):
        assert_connection_is_running(
            self,
            self.server_connection,
            ASSERTION_TIMEOUT
        )

    def then_server_is_not_running(self):
        assert_connection_is_not_running(
            self,
            self.server_connection,
            ASSERTION_TIMEOUT
        )

    def then_server_is_connected(self):
        assert_is_connected(
            self,
            self.server_connection,
            ASSERTION_TIMEOUT
        )

    def then_server_not_connected(self):
        assert_not_connected(
            self,
            self.server_connection,
            ASSERTION_TIMEOUT
        )

    def then_client_receives_something(self):
        assert_event_listener_receives_something(
            self,
            self.client_event_listener,
            ASSERTION_TIMEOUT
        )

    def then_server_receives(self, message):
        assert_event_listener_receives(
            self,
            self.server_event_listener,
            message,
            ASSERTION_TIMEOUT
        )

    def then_server_receives_number_of_bytes(self, number_of_bytes):
        assert_event_listener_last_message_size(
            self,
            self.server_event_listener,
            number_of_bytes,
            ASSERTION_TIMEOUT
        )

    def then_client_connection_receives(self, message):
        assert_event_listener_receives(
            self,
            self.client_event_listener,
            message,
            ASSERTION_TIMEOUT
        )

    def then_server_does_not_receive_open_notification(self):
        assert_event_listener_receives_no_open_notification(
            self,
            self.server_event_listener,
            ASSERTION_TIMEOUT
        )

    def then_server_receives_open_notification(self):
        assert_event_listener_receives_open_notification(
            self,
            self.server_event_listener,
            ASSERTION_TIMEOUT
        )

    def then_server_does_not_receive_close_notification(self):
        assert_event_listener_receives_no_close_notification(
            self,
            self.server_event_listener,
            ASSERTION_TIMEOUT
        )

    def then_server_receives_close_notification(self):
        assert_event_listener_receives_close_notification(
            self,
            self.server_event_listener,
            ASSERTION_TIMEOUT
        )

    def then_server_receives_no_errors(self):
        assert_event_listener_receives_no_errors(
            self,
            self.server_event_listener,
            ASSERTION_TIMEOUT
        )

    def then_server_receives_error(self):
        assert_event_listener_receives_an_error(
            self,
            self.server_event_listener,
            ASSERTION_TIMEOUT
        )

    def tearDown(self):
        try:
            blindly_stop(self.server_connection)
        except AttributeError:
            pass
        try:
            blindly_stop(self.client_connection)
        except AttributeError:
            pass


class MultipleConnectionsTest(unittest.TestCase):

    def setUp(self):
        self.server_connections = {}
        self.client_connections = {}
        self.server_event_listeners = {}
        self.client_event_listeners = {}

    def test_that_multiple_servers_can_run_at_once(self):
        self.given_a_server_connection("ServerA", port=51111)
        self.given_a_server_connection("ServerB", port=51112)
        self.then_server_connection_is_not_running("ServerA")
        self.then_server_connection_is_not_running("ServerB")
        self.when_server_connection_starts("ServerA")
        self.when_server_connection_starts("ServerB")
        self.then_server_connection_is_running("ServerA")
        self.then_server_connection_is_running("ServerB")

    def test_that_multiple_clients_and_servers_can_be_connected_at_once(self):
        self.given_a_server_connection("ServerA", port=51111)
        self.given_a_server_connection("ServerB", port=51112)
        self.given_a_client_connection("ClientA", host_port=51111)
        self.given_a_client_connection("ClientB", host_port=51112)
        self.when_server_connection_starts("ServerA")
        self.when_server_connection_starts("ServerB")
        self.then_client_is_not_connected("ClientA")
        self.then_client_is_not_connected("ClientB")
        self.then_server_is_not_connected("ServerA")
        self.then_server_is_not_connected("ServerB")
        self.when_client_connection_starts("ClientA")
        self.then_server_is_connected("ServerA")
        self.then_client_is_connected("ClientA")
        self.then_server_is_not_connected("ServerB")
        self.when_client_connection_starts("ClientB")
        self.then_server_is_connected("ServerB")
        self.then_client_is_connected("ClientB")

    def given_a_server_connection(self, identifier, port):
        event_listener = EventSavingEventListener()
        socket_ = get_bound_socket(port)
        server_connection = ServerConnection(socket_, event_listener)
        self.server_event_listeners[identifier] = event_listener
        self.server_connections[identifier] = server_connection

    def given_a_client_connection(self, identifier, host_port):
        event_listener = EventSavingEventListener()
        client_connection = ClientConnection('localhost',
                                             host_port,
                                             event_listener)
        self.client_event_listeners[identifier] = event_listener
        self.client_connections[identifier] = client_connection

    def when_server_connection_starts(self, identifier):
        self.server_connections[identifier].start()

    def when_client_connection_starts(self, identifier):
        self.client_connections[identifier].start()

    def then_server_connection_is_running(self, identifier):
        assert_connection_is_running(
            self,
            self.server_connections[identifier],
            ASSERTION_TIMEOUT
        )

    def then_server_connection_is_not_running(self, identifier):
        assert_connection_is_not_running(
            self,
            self.server_connections[identifier],
            ASSERTION_TIMEOUT
        )

    def then_client_connection_is_running(self, identifier):
        assert_connection_is_running(
            self,
            self.client_connections[identifier],
            ASSERTION_TIMEOUT
        )

    def then_client_connection_is_not_running(self, identifier):
        assert_connection_is_not_running(
            self,
            self.client_connections[identifier],
            ASSERTION_TIMEOUT
        )

    def then_server_is_connected(self, identifier):
        assert_is_connected(
            self,
            self.server_connections[identifier],
            ASSERTION_TIMEOUT
        )

    def then_server_is_not_connected(self, identifier):
        assert_not_connected(
            self,
            self.server_connections[identifier],
            ASSERTION_TIMEOUT
        )

    def then_client_is_connected(self, identifier):
        assert_is_connected(
            self,
            self.client_connections[identifier],
            ASSERTION_TIMEOUT
        )

    def then_client_is_not_connected(self, identifier):
        assert_not_connected(
            self,
            self.client_connections[identifier],
            ASSERTION_TIMEOUT
        )

    def tearDown(self):
        blindly_stop_all(self.server_connections)
        blindly_stop_all(self.client_connections)


def generate_bytes(num_of_bytes):
    return "x" * num_of_bytes


def get_bound_socket(port):
    socket_ = socket.socket()
    socket_.setblocking(True)
    socket_.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    socket_.bind(('localhost', port))
    return socket_


def blindly_stop(client_connection):
    try:
        client_connection.stop()
    except:
        pass


def blindly_stop_all(connections):
    for connection in connections.values():
        blindly_stop(connection)


if __name__ == "__main__":
    unittest.main()
