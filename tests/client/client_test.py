import unittest
from unittest.mock import MagicMock
from collections import namedtuple
from dipla.client.client import ClientEventListener


class ClientEventListenerTest(unittest.TestCase):

    def setUp(self):
        self.services = None
        self.connection = None
        self.event_listener = None

    def test_connection_recorded_when_established(self):
        self.given_a_client_event_listener()
        self.then_connection_not_recorded()
        self.when_connection_is_established()
        self.then_connection_was_recorded()

    def test_failure_recorded_when_connection_refused(self):
        self.given_a_client_event_listener()
        self.then_has_not_errored()
        self.then_did_not_refuse_to_connect()
        self.when_connection_is_refused()
        self.then_has_errored()
        self.then_refused_to_connect()

    def test_relevant_service_runs_when_message_received(self):
        self.given_the_services(["foo_service", "bar_service"])
        self.given_a_client_event_listener()
        self.when_it_receives({'label': 'foo_service', 'data': 'xyz'})
        self.then_the_service_ran('foo_service', 'xyz')
        self.when_it_receives({'label': 'bar_service', 'data': 'abcdefg'})
        self.then_the_service_ran('bar_service', 'abcdefg')

    def test_service_result_is_sent_back(self):
        self.given_the_services(["cool_service"])
        self.given_the_service_will_return("cool_service", {'x': "ARBITRARY"})
        self.given_a_client_event_listener()
        self.when_it_receives({'label': 'cool_service', 'data': 'xyz'})
        self.then_the_result_was_sent_back({'x': "ARBITRARY"})

        self.given_the_services(["cooler_service"])
        self.given_the_service_will_return("cooler_service", {'FOO': "BAR"})
        self.given_a_client_event_listener()
        self.when_it_receives({'label': 'cooler_service', 'data': ''})
        self.then_the_result_was_sent_back({'FOO': "BAR"})

    def given_the_services(self, service_names):
        self.services = {}
        for service_name in service_names:
            service = namedtuple('MockObject', 'execute')
            service.execute = MagicMock()
            self.services[service_name] = service

    def given_the_service_will_return(self, service_name, return_value):
        service = self.services[service_name]
        service.execute = MagicMock(return_value=return_value)

    def given_a_client_event_listener(self):
        self.connection = namedtuple('MockObject', 'send')
        self.connection.send = MagicMock()
        self.event_listener = ClientEventListener(self.services)

    def when_it_receives(self, message_object):
        self.event_listener.on_message(self.connection, message_object)

    def when_connection_is_established(self):
        self.event_listener.on_open(self.connection, "")

    def when_connection_is_refused(self):
        self.event_listener.on_error(self.connection, ConnectionRefusedError())

    def then_connection_not_recorded(self):
        self.assertFalse(self.event_listener.has_connected())

    def then_connection_was_recorded(self):
        self.assertTrue(self.event_listener.has_connected())

    def then_did_not_refuse_to_connect(self):
        self.assertFalse(self.event_listener.refused_to_connect())

    def then_refused_to_connect(self):
        self.assertTrue(self.event_listener.refused_to_connect())

    def then_has_errored(self):
        self.assertTrue(self.event_listener.has_errored())

    def then_has_not_errored(self):
        self.assertFalse(self.event_listener.has_errored())

    def then_the_service_ran(self, service_label, service_data):
        self.services[service_label].execute.assert_called_with(service_data)

    def then_the_result_was_sent_back(self, message_object):
        self.connection.send.assert_called_with(message_object)
