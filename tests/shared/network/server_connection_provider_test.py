import unittest
import time
from dipla.shared.network.network_connection import ClientConnection
from .network_connection_test import EventSavingEventListener
from tests.utils import assert_with_timeout
from dipla.shared.network.server_connection_provider import ServerConnectionProvider  # nopep8


ASSERTION_TIMEOUT = 5


PORT = 51515


class ServerConnectionProviderTest(unittest.TestCase):

    def setUp(self):
        self.server_connection_provider = None
        self.established_server_connections = set()
        self.client_connections = []

    def tearDown(self):
        self.shut_shit_down()

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

    def test_that_there_are_two_established_connections(self):
        self.given_a_server_connection_provider()
        self.when_started()
        self.when_a_client_connects()
        self.then_the_number_of_established_connections_is(1)
        self.when_a_client_connects()
        self.then_the_number_of_established_connections_is(2)

    def given_a_server_connection_provider(self):
        self.established_server_connections = set()
        self.server_connection_provider = ServerConnectionProvider(
            self.established_server_connections,
            PORT,
            EventSavingEventListener
        )

    def when_started(self):
        self.server_connection_provider.start()

    def when_a_client_connects(self):
        client_connection = ClientConnection(
            "localhost",
            PORT,
            EventSavingEventListener()
        )
        client_connection.start()
        self.client_connections.append(client_connection)

    def then_the_number_of_established_connections_is(self, expected):
        def has_correct_number():
            number_of_connections = len(self.established_server_connections)
            return expected == number_of_connections
        assert_with_timeout(self, has_correct_number, ASSERTION_TIMEOUT)

    def then_the_client_is_connected(self):
        def is_connected():
            time.sleep(0.5)
            return self.client_connections[0].is_connected()
        assert_with_timeout(self, is_connected, ASSERTION_TIMEOUT)

    def shut_shit_down(self):
        for client_connection in self.client_connections:
            try:
                client_connection.stop()
            except AttributeError:
                pass
            self.assertFalse(client_connection.isAlive())
        self.server_connection_provider.stop()
        self.assertFalse(self.server_connection_provider.isAlive())
