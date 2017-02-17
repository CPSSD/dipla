from tests.utils import assert_with_timeout


def assert_event_listener_receives_nothing(test_case,
                                           event_listener,
                                           assertion_timeout):
    def receives_nothing():
        return event_listener.last_message_object is None

    assert_with_timeout(test_case, receives_nothing, assertion_timeout)


def assert_event_listener_receives_something(test_case,
                                             event_listener,
                                             assertion_timeout):
    def receives_something():
        return event_listener.last_message_object is not None

    assert_with_timeout(test_case, receives_something, assertion_timeout)


def assert_event_listener_receives(test_case,
                                   event_listener,
                                   message_object,
                                   assertion_timeout):
    def receives_message():
        return event_listener.last_message_object == message_object
    assert_with_timeout(test_case, receives_message, assertion_timeout)


def assert_is_connected(test_case, connection, assertion_timeout):
    def is_connected():
        return connection.is_connected()

    assert_with_timeout(test_case, is_connected, assertion_timeout)


def assert_not_connected(test_case, connection, assertion_timeout):
    def not_connected():
        return not connection.is_connected()

    assert_with_timeout(test_case, not_connected, assertion_timeout)


def assert_event_listener_receives_no_errors(test_case,
                                             event_listener,
                                             assertion_timeout):
    def receives_no_errors():
        return event_listener.last_error is None

    assert_with_timeout(test_case, receives_no_errors, assertion_timeout)


def assert_event_listener_receives_no_close_notification(test_case,
                                                         event_listener,
                                                         assertion_timeout):
    def does_not_receive_close_notification():
        return event_listener.closed is False

    assert_with_timeout(test_case,
                        does_not_receive_close_notification,
                        assertion_timeout)


def assert_event_listener_receives_close_notification(test_case,
                                                      event_listener,
                                                      assertion_timeout):
    def receives_close_notification():
        return event_listener.closed

    assert_with_timeout(test_case,
                        receives_close_notification,
                        assertion_timeout)


def assert_event_listener_receives_an_error(test_case,
                                            event_listener,
                                            assertion_timeout):
    def receives_error():
        return event_listener.last_error is not None

    assert_with_timeout(test_case, receives_error, assertion_timeout)


def assert_connection_is_running(test_case,
                                 connection,
                                 assertion_timeout):
    def is_running():
        return connection.isAlive()

    assert_with_timeout(test_case, is_running, assertion_timeout)


def assert_connection_is_not_running(test_case,
                                     connection,
                                     assertion_timeout):
    def is_not_running():
        return not connection.isAlive()

    assert_with_timeout(test_case, is_not_running, assertion_timeout)


def assert_event_listener_receives_no_open_notification(test_case,
                                                        event_listener,
                                                        assertion_timeout):
    def receives_no_open_notification():
        return not event_listener.opened

    assert_with_timeout(test_case, receives_no_open_notification,
                        assertion_timeout)


def assert_event_listener_receives_open_notification(test_case,
                                                     event_listener,
                                                     assertion_timeout):
    def receives_open_notification():
        return event_listener.opened

    assert_with_timeout(test_case, receives_open_notification,
                        assertion_timeout)


def assert_event_listener_receives_connection_refused(test_case,
                                                      event_listener,
                                                      assertion_timeout):
    def receives_connection_refused():
        return event_listener.last_error is not None

    assert_with_timeout(test_case, receives_connection_refused,
                        assertion_timeout)


def assert_event_listener_last_message_size(test_case,
                                            event_listener,
                                            expected_size,
                                            assertion_timeout):
    def receives_expected_number_of_bytes():
        try:
            length = len(event_listener.last_message_object['data'])
            return length == expected_size
        except TypeError:
            return False

    assert_with_timeout(test_case, receives_expected_number_of_bytes,
                        assertion_timeout)


def assert_number_of_connections(test_case,
                                 established_connections,
                                 expected_number,
                                 assertion_timeout):
    def has_correct_number():
        number_of_connections = established_connections.qsize()
        return number_of_connections == expected_number

    assert_with_timeout(test_case, has_correct_number, assertion_timeout)
