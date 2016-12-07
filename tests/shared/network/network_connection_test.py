import functools
import unittest
import time
from dipla.shared.network.network_connection import ClientConnection
from dipla.shared.network.network_connection import ServerConnection
from dipla.shared.network.network_connection import EventListener


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
        self.server_connection = ServerConnection(port,
                                                  event_listener)
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
        def does_not_receive_open():
            return not self.client_event_listener._opened
        assert_with_timeout(self, does_not_receive_open, ASSERTION_TIMEOUT)

    def then_client_receives_open_notification(self):
        def receives_open():
            return self.client_event_listener._opened
        assert_with_timeout(self, receives_open, ASSERTION_TIMEOUT)

    def then_client_is_connected(self):
        def connected():
            return self.client_connection.is_connected()
        assert_with_timeout(self, connected, ASSERTION_TIMEOUT)

    def then_client_not_connected(self):
        def not_connected():
            return not self.client_connection.is_connected()
        assert_with_timeout(self, not_connected, ASSERTION_TIMEOUT)

    def when_client_connection_sends(self, message):
        self.client_connection.send(message)

    def then_server_connection_receives_something(self):
        def received_something():
            return self.server_event_listener._last_message is not None
        assert_with_timeout(self, received_something, ASSERTION_TIMEOUT)

    def then_server_connection_receives_nothing(self):
        def received_nothing():
            return self.server_event_listener._last_message is None
        assert_with_timeout(self, received_nothing, ASSERTION_TIMEOUT)

    def then_server_connection_receives(self, message):
        def received_message(expected):
            return self.server_event_listener._last_message == expected
        received_expected = functools.partial(received_message, message)
        assert_with_timeout(self, received_expected, ASSERTION_TIMEOUT)

    def then_client_receives(self, message):
        def received_message(expected):
            return self.client_event_listener._last_message == expected
        received_expected = functools.partial(received_message, message)
        assert_with_timeout(self, received_expected, ASSERTION_TIMEOUT)

    def then_client_receives_no_errors(self):
        def received_no_errors():
            return self.client_event_listener._last_error is None
        assert_with_timeout(self, received_no_errors, ASSERTION_TIMEOUT)

    def then_client_receives_connection_refused_error(self):
        def received_error():
            return self.client_event_listener._last_error is not None
        assert_with_timeout(self, received_error, ASSERTION_TIMEOUT)

    def then_client_receives_close_notification(self):
        def received_close_notification():
            return self.client_event_listener._closed is True
        assert_with_timeout(self,
                            received_close_notification,
                            ASSERTION_TIMEOUT)

    def then_client_does_not_receive_close_notification(self):
        def not_received_close_notification():
            return self.client_event_listener._closed is False
        assert_with_timeout(self,
                            not_received_close_notification,
                            ASSERTION_TIMEOUT)

    def tearDown(self):
        try:
            self.client_connection.stop()
        except AttributeError:
            pass
        try:
            self.server_connection.stop()
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

    def test_that_server_event_listener_receives_error_when_binding_to_invalid_port(self):  # nopep8
        self.given_a_server_connection_on_port(-1)
        self.when_listening_for_client_connection()
        self.then_server_receives_error()

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

    def given_a_server_connection(self):
        self.given_a_server_connection_on_port(51111)

    def given_a_server_connection_on_port(self, port):
        event_listener = EventSavingEventListener()
        self.server_connection = ServerConnection(port, event_listener)
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
        def is_running():
            return self.server_connection.isAlive()
        assert_with_timeout(self, is_running, ASSERTION_TIMEOUT)

    def then_server_is_not_running(self):
        def is_not_running():
            return not self.server_connection.isAlive()
        assert_with_timeout(self, is_not_running, ASSERTION_TIMEOUT)

    def then_server_is_connected(self):
        def connected():
            return self.server_connection.is_connected()
        assert_with_timeout(self, connected, ASSERTION_TIMEOUT)

    def then_server_not_connected(self):
        def not_connected():
            return not self.server_connection.is_connected()
        assert_with_timeout(self, not_connected, ASSERTION_TIMEOUT)

    def then_client_receives_something(self):
        def received_something():
            return self.client_event_listener._last_message is not None
        assert_with_timeout(self, received_something, ASSERTION_TIMEOUT)

    def then_server_receives(self, message):
        def received_message(expected):
            return self.server_event_listener._last_message == expected
        received_expected = functools.partial(received_message, message)
        assert_with_timeout(self, received_expected, ASSERTION_TIMEOUT)

    def then_server_receives_number_of_bytes(self, num_of_bytes):
        def received_expected_bytes(expected):
            try:
                length = len(self.server_event_listener._last_message)
                return length == expected
            except TypeError:
                return False
        received_large_message = functools.partial(received_expected_bytes,
                                                   num_of_bytes)
        assert_with_timeout(self, received_large_message, ASSERTION_TIMEOUT)

    def then_client_connection_receives(self, message):
        def received_message(expected):
            return self.client_event_listener._last_message == expected

        received_expected = functools.partial(received_message, message)
        assert_with_timeout(self, received_expected, ASSERTION_TIMEOUT)

    def then_server_does_not_receive_open_notification(self):
        def not_received_open_notification():
            return not self.server_event_listener._opened
        assert_with_timeout(self,
                            not_received_open_notification,
                            ASSERTION_TIMEOUT)

    def then_server_receives_open_notification(self):
        def receives_open_notification():
            return self.server_event_listener._opened
        assert_with_timeout(self,
                            receives_open_notification,
                            ASSERTION_TIMEOUT)

    def then_server_does_not_receive_close_notification(self):
        def not_received_close_notification():
            return not self.server_event_listener._closed
        assert_with_timeout(self,
                            not_received_close_notification,
                            ASSERTION_TIMEOUT)

    def then_server_receives_close_notification(self):
        def received_close_notification():
            return self.server_event_listener._closed
        assert_with_timeout(self,
                            received_close_notification,
                            ASSERTION_TIMEOUT)

    def then_server_receives_no_errors(self):
        def received_no_errors():
            return self.server_event_listener._last_error is None
        assert_with_timeout(self, received_no_errors, ASSERTION_TIMEOUT)

    def then_server_receives_error(self):
        def received_error():
            return self.server_event_listener._last_error is not None
        assert_with_timeout(self, received_error, ASSERTION_TIMEOUT)

    def tearDown(self):
        try:
            self.client_connection.stop()
        except AttributeError:
            pass
        try:
            self.server_connection.stop()
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
        server_connection = ServerConnection(port, event_listener)
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
        def running(server_identifier):
            server_connection = self.server_connections[server_identifier]
            return server_connection.isAlive()
        is_running = functools.partial(running, identifier)
        assert_with_timeout(self, is_running, ASSERTION_TIMEOUT)

    def then_server_connection_is_not_running(self, identifier):
        def not_running(server_identifier):
            server_connection = self.server_connections[server_identifier]
            return not server_connection.isAlive()
        is_not_running = functools.partial(not_running, identifier)
        assert_with_timeout(self, is_not_running, ASSERTION_TIMEOUT)

    def then_client_connection_is_running(self, identifier):
        def running(client_identifier):
            client_connection = self.client_connections[client_identifier]
            return client_connection.isAlive()
        is_running = functools.partial(running, identifier)
        assert_with_timeout(self, is_running, ASSERTION_TIMEOUT)

    def then_client_connection_is_not_running(self, identifier):
        def not_running(client_identifier):
            client_connection = self.client_connections[client_identifier]
            return not client_connection.isAlive()
        is_not_running = functools.partial(not_running, identifier)
        assert_with_timeout(self, is_not_running, ASSERTION_TIMEOUT)

    def then_server_is_connected(self, identifier):
        def connected(server_identifier):
            server_connection = self.server_connections[server_identifier]
            return server_connection.is_connected()
        is_connected = functools.partial(connected, identifier)
        assert_with_timeout(self, is_connected, ASSERTION_TIMEOUT)

    def then_server_is_not_connected(self, identifier):
        def not_connected(server_identifier):
            server_connection = self.server_connections[server_identifier]
            return not server_connection.is_connected()
        server_not_connected = functools.partial(not_connected, identifier)
        assert_with_timeout(self, server_not_connected, ASSERTION_TIMEOUT)

    def then_client_is_connected(self, identifier):
        def connected(client_identifier):
            client_connection = self.client_connections[client_identifier]
            return client_connection.is_connected()
        is_connected = functools.partial(connected, identifier)
        assert_with_timeout(self, is_connected, ASSERTION_TIMEOUT)

    def then_client_is_not_connected(self, identifier):
        def not_connected(client_identifier):
            client_connection = self.client_connections[client_identifier]
            return not client_connection.is_connected()
        is_not_connected = functools.partial(not_connected, identifier)
        assert_with_timeout(self, is_not_connected, ASSERTION_TIMEOUT)

    def tearDown(self):
        for server_connection in self.server_connections.values():
            try:
                server_connection.stop()
            except:
                pass
        for client_connection in self.client_connections.values():
            try:
                client_connection.stop()
            except:
                pass


class EchoEventListener(EventListener):

    def __init__(self):
        self._last_message = None

    def on_open(self, connection, message):
        pass

    def on_error(self, connection, error):
        pass

    def on_close(self, connection, reason):
        pass

    def on_message(self, connection, message):
        self._last_message = message
        message = "Echo: " + message
        connection.send(message)


class EventSavingEventListener(EventListener):

    def __init__(self):
        self._last_message = None
        self._last_error = None
        self._closed = False
        self._opened = False

    def on_open(self, connection, message):
        self._opened = True

    def on_message(self, connection, message):
        self._last_message = message

    def on_error(self, connection, error):
        self._last_error = error

    def on_close(self, connection, reason):
        self._closed = True


def assert_with_timeout(test_case, condition_function, timeout):
    start_time = time.time()
    end_time = start_time + timeout
    condition_met = False
    while time.time() < end_time and not condition_met:
        condition_met = condition_function()
    test_case.assertTrue(condition_met)


def generate_bytes(num_of_bytes):
    return "x" * num_of_bytes


if __name__ == "__main__":
    unittest.main()
