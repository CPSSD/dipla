import queue
import unittest
from dipla.shared.network.network_connection import ClientConnection
from dipla.shared.network.server_connection_provider import ServerConnectionProvider  # nopep8
from .network_connection_test import EventSavingEventListener, EchoEventListener  # nopep8
from .useful_assertions import *


ASSERTION_TIMEOUT = 5


PORT = 51515


class ServerConnectionProviderTest(unittest.TestCase):

    def setUp(self):
        self.server_connection_provider = None
        self.established_server_connections = queue.Queue()
        self.client_connections = []
        self.client_event_listeners = []

    def tearDown(self):
        self.close_all_connections()

    def test_that_there_are_no_established_connections_when_started(self):
        self.given_a_server_connection_provider()
        self.when_started()
        self.then_the_number_of_established_connections_is(0)

    def test_that_there_is_one_established_connection_when_client_connects(self):  # nopep8
        self.given_a_server_connection_provider()
        self.when_started()
        self.when_a_client_connects()
        self.then_the_client_is_connected()
        self.then_the_number_of_established_connections_is(1)

    def test_that_there_can_be_multiple_established_connections(self):
        self.given_a_server_connection_provider()
        self.when_started()
        self.when_a_client_connects()
        self.then_the_number_of_established_connections_is(1)
        self.when_a_client_connects()
        self.then_the_number_of_established_connections_is(2)
        self.when_a_client_connects()
        self.then_the_number_of_established_connections_is(3)

    def test_that_separate_communication_can_occur(self):
        self.given_a_server_connection_provider()
        self.when_started()
        self.when_a_client_connects()
        self.when_a_client_connects()
        self.when_a_client_connects()
        self.when_client_says(0, "Hello!")
        self.when_client_says(1, "There")
        self.when_client_says(2, "Friends")
        self.then_client_receives(0, "Echo: Hello!")
        self.then_client_receives(1, "Echo: There")
        self.then_client_receives(2, "Echo: Friends")

    def given_a_server_connection_provider(self):
        self.established_server_connections = queue.Queue()
        self.server_connection_provider = ServerConnectionProvider(
            self.established_server_connections,
            PORT,
            EchoEventListener
        )

    def when_started(self):
        self.server_connection_provider.start()

    def when_a_client_connects(self):
        event_listener = EventSavingEventListener()
        client_connection = ClientConnection(
            "localhost",
            PORT,
            event_listener
        )
        client_connection.start()
        self.client_event_listeners.append(event_listener)
        self.client_connections.append(client_connection)

    def when_client_says(self, index, message):
        self.client_connections[index].send(message)

    def then_client_receives(self, index, message):
        assert_event_listener_receives(
            self,
            self.client_event_listeners[index],
            message,
            ASSERTION_TIMEOUT
        )

    def when_the_first_client_disconnects(self):
        index = 0
        self.client_connections[index].stop()
        self.client_connections.pop(index)

    def then_the_number_of_established_connections_is(self, number):
        assert_number_of_connections(
            self,
            self.established_server_connections,
            number,
            ASSERTION_TIMEOUT
        )

    def then_the_client_is_connected(self):
        assert_is_connected(
            self,
            self.client_connections[0],
            ASSERTION_TIMEOUT
        )

    def close_all_connections(self):
        for client_connection in self.client_connections:
            try:
                client_connection.stop()
            except AttributeError:
                pass
            self.assertFalse(client_connection.isAlive())
        self.server_connection_provider.stop()
        self.assertFalse(self.server_connection_provider.isAlive())
