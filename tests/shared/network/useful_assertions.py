import functools
import time

from tests.utils import assert_with_timeout


def assert_event_listener_receives_nothing(test_object,
                                           event_listener,
                                           assertion_timeout):
    def receives_nothing():
        return event_listener.last_message_object is None

    assert_with_timeout(test_object, receives_nothing, assertion_timeout)


def assert_event_listener_receives_something(test_object,
                                             event_listener,
                                             assertion_timeout):
    def receives_something():
        return event_listener.last_message_object is not None

    assert_with_timeout(test_object, receives_something, assertion_timeout)


def assert_event_listener_receives(test_object,
                                   event_listener,
                                   message,
                                   assertion_timeout):
    def receives_message():
        print("CHECKING SHIT - actual:{} expected:{}".format(event_listener.last_message_object, message))
        time.sleep(0.2)
        return event_listener.last_message_object == message
    assert_with_timeout(test_object, receives_message, assertion_timeout)


def assert_is_connected(test_object, connection, assertion_timeout):
    def is_connected():
        return connection.is_connected()

    assert_with_timeout(test_object, is_connected, assertion_timeout)


def assert_not_connected(test_object, connection, assertion_timeout):
    def not_connected():
        return not connection.is_connected()

    assert_with_timeout(test_object, not_connected, assertion_timeout)


def assert_event_listener_receives_no_errors(test_object,
                                             event_listener,
                                             assertion_timeout):
    def receives_no_errors():
        return event_listener.last_error is None

    assert_with_timeout(test_object, receives_no_errors, assertion_timeout)


def assert_event_listener_receives_no_close_notification(test_object,
                                                         event_listener,
                                                         assertion_timeout):
    def does_not_receive_close_notification():
        return event_listener.closed is False

    assert_with_timeout(test_object,
                        does_not_receive_close_notification,
                        assertion_timeout)


def assert_event_listener_receives_close_notification(test_object,
                                                      event_listener,
                                                      assertion_timeout):
    def receives_close_notification():
        return event_listener.closed

    assert_with_timeout(test_object,
                        receives_close_notification,
                        assertion_timeout)


def assert_event_listener_receives_an_error(test_object,
                                            event_listener,
                                            assertion_timeout):
    def receives_error():
        return event_listener.last_error is not None

    assert_with_timeout(test_object, receives_error, assertion_timeout)


def assert_connection_is_running(test_object,
                                 connection,
                                 assertion_timeout):
    def is_running():
        return connection.isAlive()

    assert_with_timeout(test_object, is_running, assertion_timeout)


def assert_connection_is_not_running(test_object,
                                     connection,
                                     assertion_timeout):
    def is_not_running():
        return not connection.isAlive()

    assert_with_timeout(test_object, is_not_running, assertion_timeout)


def assert_event_listener_receives_no_open_notification(test_object,
                                                        event_listener,
                                                        assertion_timeout):
    def receives_no_open_notification():
        return not event_listener.opened

    assert_with_timeout(test_object, receives_no_open_notification,
                        assertion_timeout)


def assert_event_listener_receives_open_notification(test_object,
                                                     event_listener,
                                                     assertion_timeout):
    def receives_open_notification():
        return event_listener.opened

    assert_with_timeout(test_object, receives_open_notification,
                        assertion_timeout)


def assert_event_listener_receives_connection_refused(test_object,
                                                      event_listener,
                                                      assertion_timeout):
    def receives_connection_refused():
        return event_listener.last_error is not None

    assert_with_timeout(test_object, receives_connection_refused,
                        assertion_timeout)


def assert_event_listener_last_message_size(test_object,
                                            event_listener,
                                            expected_size,
                                            assertion_timeout):
    def receives_expected_number_of_bytes():
        try:
            length = len(event_listener.last_message_object['data'])
            return length == expected_size
        except TypeError:
            return False

    assert_with_timeout(test_object, receives_expected_number_of_bytes,
                        assertion_timeout)


def assert_number_of_connections(test_object,
                                 established_connections,
                                 expected_number,
                                 assertion_timeout):
    def has_correct_number():
        number_of_connections = established_connections.qsize()
        return number_of_connections == expected_number

    assert_with_timeout(test_object, has_correct_number, assertion_timeout)
