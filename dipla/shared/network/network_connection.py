import errno
import socket
import threading
import time
from dipla.shared.network.message_defixer import MessageDefixer
from dipla.shared.network.message_defixer import NoMessageException
from dipla.shared.network.message_defixer import IllegalHeaderException
from dipla.shared.network.message_prefixer import prefix_message


EMPTY = ""


class SocketConnection(threading.Thread):
    """
    This class represents a network connection that uses sockets. It contains
    the more general code related to bi-directional network communication,
    such as "sending" and "receiving" functionality.

    THIS CLASS SHOULD NOT BE INSTANTIATED; IT IS TO BE INHERITED ONLY.

    It provides templates for methods such as _prepare_socket,
    _perform_connection_step, and _cleanup, that MUST be implemented
    by the subclasses/inheritors of this class.

    It also provides a standard way of "catching" certain events, and emitting
    them to a NetworkEventListener object. This NetworkEventListener object
    will have methods triggered by these events, such as:
    on_message, on_open, on_close, and on_error.
    """

    DATA_ENCODING = "UTF-8"

    def __init__(self, host_address, host_port, event_listener, label):
        super(SocketConnection, self).__init__()
        self._message_defixer = MessageDefixer()
        self._event_listener = event_listener
        self._stop_event = threading.Event()
        self._host_address = host_address
        self._host_port = host_port
        self._connection = None
        self._connected = False
        self._label = label
        self._init_socket()

    def run(self):
        try:
            self._perform_connection_step()
            self._receive_messages()
        except ConnectionShouldStopError as reason:
            self._emit_expected_close(reason)
        except ConnectionFailedError as reason:
            self._emit_expected_error(reason)
        except socket.error as socket_error:
            self._emit_unexpected_error("socket error", socket_error)
        except Exception as error:
            self._emit_unexpected_error("non-socket error", error)
        finally:
            self._cleanup()
            self._emit_final_close()

    def send(self, message):
        print(SEND_MESSAGE_MESSAGE.format(self._label), message)
        message = prefix_message(message)
        self._attempt_send_with_timeout(message)
        print(SENT_MESSAGE_MESSAGE.format(self._label))

    def stop(self):
        print(STOP_MESSAGE.format(self._label))
        self._cleanup()
        self.join()
        print(STOP_SUCCESS_MESSAGE.format(self._label))

    def is_connected(self):
        print(CHECK_CONNECTED_MESSAGE.format(self._label))
        return self._connected

    def _init_socket(self):
        try:
            self._prepare_socket()
        except ConnectionPreparationFailedError as reason:
            self._event_listener.on_error(self, reason)

    def _receive_messages(self):
        while self._should_still_run():
            try:
                self._read_byte_from_socket()
                self._handle_received_byte()
            except socket.error as socket_error:
                self._recover_from_receival_error(socket_error)

    def _read_byte_from_socket(self):
        byte_of_data = self._connection.recv(1)
        decoded_byte = byte_of_data.decode(SocketConnection.DATA_ENCODING)
        self._decoded_byte = decoded_byte

    def _handle_received_byte(self):
        if self._decoded_byte is not EMPTY:
            self._feed_byte_to_defixer(self._decoded_byte)
            self._check_defixer_for_full_message()
        else:
            stop_reason = EMPTY_MESSAGE_MESSAGE.format(self._label)
            raise ConnectionShouldStopError(stop_reason)

    def _feed_byte_to_defixer(self, message):
        print(RECEIVED_MESSAGE_MESSAGE.format(self._label, message))
        try:
            self._message_defixer.feed_character(message)
        except IllegalHeaderException:
            raise ConnectionShouldStopError(CORRUPT_HEADER_MESSAGE)

    def _check_defixer_for_full_message(self):
        try:
            full_message = self._message_defixer.get_defixed_message()
            self._event_listener.on_message(self, full_message)
        except NoMessageException:
            pass

    def _emit_unexpected_error(self, error_type, error):
        print(UNEXPECTED_ERROR_MESSAGE.format(error_type, self._label, error))
        self._event_listener.on_error(self, error)

    def _emit_expected_close(self, reason):
        print(EXPECTED_ERROR_MESSAGE.format(self._label, reason))
        self._event_listener.on_close(self, reason)

    def _emit_final_close(self):
        self._event_listener.on_close(self, CLEANUP_MESSAGE)

    def _emit_expected_error(self, reason):
        print(EXPECTED_ERROR_MESSAGE.format(self._label, reason))
        self._event_listener.on_error(self, reason)

    def _emit_open_event(self):
        print(CONNECTION_ESTABLISHED_MESSAGE.format(
            self._label, self._host_address))
        self._event_listener.on_open(self, "Connection established.")

    def _should_still_run(self):
        return not self._stop_event.is_set()

    def _attempt_send_with_timeout(self, message):
        timeout = 4
        start_time = time.time()
        end_time = start_time + timeout
        encoded = message.encode(SocketConnection.DATA_ENCODING)
        sent_successfully = False
        while time.time() < end_time and sent_successfully is False:
            sent_successfully = self._attempt_send(encoded)

    def _attempt_send(self, encoded_message):
        success = False
        try:
            self._connection.send(encoded_message)
            success = True
        except AttributeError:
            print(ATTRIBUTE_ERROR_SEND_MESSAGE.format(self._label))
        except socket.error as e:
            self._recover_from_sending_error(e)
        return success

    def _stop_connection_element(self, connection_element):
        try:
            connection_element.shutdown(socket.SHUT_RDWR)
            connection_element.close()
            print(CONNECTION_ELEMENT_CLOSED_MESSAGE.format(self._label))
        except AttributeError:
            print(ATTRIBUTE_ERROR_CLOSE_MESSAGE.format(self._label))
        except socket.error as socket_error:
            self._recover_from_disconnect_error(socket_error)

    def _recover_from_receival_error(self, socket_error):
        if socket_error.errno == errno.ENOTCONN:
            print(RECEIVE_NOT_CONNECTED_MESSAGE.format(self._label))
        else:
            raise socket_error

    def _recover_from_sending_error(self, socket_error):
        if socket_error.errno == errno.EPIPE:
            print(BROKEN_PIPE_SEND_MESSAGE.format(self._label))
        else:
            raise socket_error

    def _recover_from_disconnect_error(self, socket_error):
        if socket_error.errno == errno.ENOTCONN:
            print(CONNECTION_NOT_OPEN_STOP_MESSAGE.format(self._label))
        elif socket_error.errno == errno.EBADF:
            print(STOP_CONNECTION_ELEMENT_TWICE_MESSAGE.format(self._label))
        else:
            raise socket_error

    def _prepare_socket(self):
        pass  # ABSTRACT: To be implemented by inheritors.

    def _perform_connection_step(self):
        pass  # ABSTRACT: To be implemented by inheritors.

    def _cleanup(self):
        pass  # ABSTRACT: To be implemented by inheritors.


class ClientConnection(SocketConnection):
    """
    The ClientConnection is a subclass of a SocketConnection. It is used to
    establish a connection with an already-listening ServerConnection.
    """

    def __init__(self, host_address, host_port, event_listener):
        super(ClientConnection, self).__init__(host_address,
                                               host_port,
                                               event_listener,
                                               "ClientConnection")

    def _prepare_socket(self):
        self._connection = socket.socket()
        self._connection.setblocking(True)
        self._connection.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    def _perform_connection_step(self):
        print(START_CONNECTING_MESSAGE.format(self._label))
        try:
            self._connect_to_endpoint()
            self._emit_open_event()
        except socket.error as socket_error:
            self._recover_from_connection_error(socket_error)

    def _connect_to_endpoint(self):
        print(ATTEMPTING_CONNECT_MESSAGE.format(
            self._label, self._host_address, self._host_port))
        self._connection.connect((self._host_address, self._host_port))
        self._connected = True

    def _recover_from_connection_error(self, socket_error):
        if socket_error.errno == errno.ECONNREFUSED:
            raise ConnectionFailedError("Connection Refused.")
        elif socket_error.errno == errno.ECONNRESET:
            raise ConnectionFailedError("Connection Reset.")
        elif socket_error.errno == errno.EINPROGRESS:
            raise ConnectionShouldStopError("Operation now in progress.")
        else:
            raise socket_error

    def _cleanup(self):
        self._stop_event.set()
        self._stop_connection_element(self._connection)
        self._connected = False


class ServerConnection(SocketConnection):
    """
    The ServerConnection is a subclass of a SocketConnection. It is used to
    bind a socket to a port during the connection process and accept an
    incoming ClientConnection.
    """

    def __init__(self, host_port, event_listener):
        super(ServerConnection, self).__init__("localhost",
                                               host_port,
                                               event_listener,
                                               "ServerConnection")

    def _prepare_socket(self):
        self._socket = socket.socket()
        self._socket.setblocking(True)
        self._socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._bind_socket()
        self._socket.listen(5)

    def _bind_socket(self):
        try:
            self._socket.bind(('localhost', self._host_port))
        except OverflowError:
            raise ConnectionPreparationFailedError(ILLEGAL_PORT_BIND_MESSAGE)

    def _perform_connection_step(self):
        print(START_CONNECTING_MESSAGE.format(self._label))
        try:
            self._accept_incoming_connection()
            self._emit_open_event()
        except OSError as os_error:
            self._recover_from_connection_error(os_error)

    def _accept_incoming_connection(self):
        self._connection, self._connection_address = self._socket.accept()
        self._connected = True
        print(CONNECTION_ESTABLISHED_MESSAGE.format(
            self._label,
            self._connection_address
        ))

    def _recover_from_connection_error(self, os_error):
        if os_error.errno == errno.EINVAL:
            print(CLOSED_WHILE_ACCEPTING_MESSAGE.format(self._label))
        else:
            raise os_error

    def _cleanup(self):
        self._stop_event.set()
        self._stop_connection_element(self._connection)
        self._stop_connection_element(self._socket)
        self._connected = False


class EventListener(object):

    def on_open(self, connection, message):
        pass  # ABSTRACT

    def on_message(self, connection, message):
        pass  # ABSTRACT

    def on_error(self, connection, error):
        pass  # ABSTRACT

    def on_close(self, connection, reason):
        pass  # ABSTRACT


class ConnectionShouldStopError(Exception):
    pass


class ConnectionFailedError(Exception):
    pass


class ConnectionPreparationFailedError(Exception):
    pass


"""
The following constants are strings which are used heavily when:
* Generating error messages.
* Generating logger statements.

I have extracted them because it greatly improves the readability of the
classes above, and makes it easier to stay within PEP8's character limit.
"""

UNEXPECTED_ERROR_MESSAGE = "CRITICAL: Unexpected {} occurred in {}... {}"

EXPECTED_ERROR_MESSAGE = "{} caught an expected error: {}"

STOP_MESSAGE = "{} has been requested to shut down."

STOP_SUCCESS_MESSAGE = "{} has been shut down and joined with calling thread."

RECEIVED_MESSAGE_MESSAGE = "{} received message: {}"

EMPTY_MESSAGE_MESSAGE = "{}'s received message was empty, indicating a " \
                        "closed connection. "

RECEIVE_NOT_CONNECTED_MESSAGE = "{} e: Tried to receive when not connected."

CLEANUP_MESSAGE = "Connection has been closed in cleanup function"

CHECK_CONNECTED_MESSAGE = "{} has been requested to check if it is connected"

SEND_MESSAGE_MESSAGE = "{} has been requested to send:"

ATTRIBUTE_ERROR_SEND_MESSAGE = "{} e: Can't send message yet. No connection."

BROKEN_PIPE_SEND_MESSAGE = "{} e: Broken pipe error when sending because " \
                           "connection not open. "

SENT_MESSAGE_MESSAGE = "{} sent message successfully."

CONNECTION_ELEMENT_CLOSED_MESSAGE = "A {} connection element has been shut " \
                                    "down & closed. "

ATTRIBUTE_ERROR_CLOSE_MESSAGE = "{}: There is no connected attribute to close."

CONNECTION_NOT_OPEN_STOP_MESSAGE = "{} e: Shutting down a connection " \
                                   "element before it was established."

STOP_CONNECTION_ELEMENT_TWICE_MESSAGE = "{} e: Tried to clean up a " \
                                        "connection element for second time."

START_CONNECTING_MESSAGE = "{} has begun the connection process."

ILLEGAL_PORT_BIND_MESSAGE = "Attempted to bind to invalid port number."

ATTEMPTING_CONNECT_MESSAGE = "{} attempting to establish connection to ({}:{})"

CONNECTION_ESTABLISHED_MESSAGE = "{} established connection with {}."

CLOSED_WHILE_ACCEPTING_MESSAGE = "{} shut down while accepting connection."

CORRUPT_HEADER_MESSAGE = "Received corrupted header, indicating malicious " \
                         "behaviour from sender. "