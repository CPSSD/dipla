import logging
import socket
from threading import Thread, Event

import time

from dipla.shared.network.network_connection import ServerConnection


class ServerConnectionProvider(Thread):
    """
    A class to instantiate new ServerConnection instances when necessary.
    Enables multiple clients to connect to the same port.
    """

    def __init__(self, established_connections, port, event_listener_class):
        self.__established_connections = established_connections
        self.__event_listener_class = event_listener_class
        self.__logger = logging.getLogger(__name__)
        self.__stop_event = Event()
        self.__current_server_connection = None
        self.__bind_master_socket_to(port)
        super().__init__()
        self.__logger.debug(CONSTRUCTOR_MESSAGE)

    def run(self):
        while not self.__stop_event.is_set():
            self.__create_new_server_connection()
            self.__start_new_server_connection()
            self.__add_to_established_connections_when_ready()

    def stop(self):
        self.__logger.debug(STOPPING_MESSAGE)
        self.__stop_event.set()
        self.__stop_current_server_connection()
        self.__stop_all_established_connections()
        self.__close_bound_socket()
        self.join()
        self.__logger.debug(STOPPED_MESSAGE)

    def __bind_master_socket_to(self, port):
        self.__master_socket = socket.socket()
        self.__master_socket.setblocking(True)
        self.__master_socket.setsockopt(socket.SOL_SOCKET,
                                        socket.SO_REUSEADDR,
                                        1)
        self.__master_socket.bind(('', port))

    def __create_new_server_connection(self):
        self.__logger.debug(CREATING_SERVER_CONNECTION_MESSAGE)
        self.__current_server_connection = ServerConnection(
            self.__master_socket,
            self.__event_listener_class()
        )
        self.__logger.debug(CREATED_SERVER_CONNECTION_MESSAGE)

    def __start_new_server_connection(self):
        if not self.__stop_event.is_set():
            self.__logger.debug(STARTING_SERVER_CONNECTION_MESSAGE)
            self.__current_server_connection.start()
            self.__logger.debug(STARTED_SERVER_CONNECTION_MESSAGE)

    def __add_to_established_connections_when_ready(self):
        while not self.__stop_event.is_set():
            if self.__current_server_connection.is_connected():
                self.__store_current_connection()
                break
            time.sleep(0.1)

    def __store_current_connection(self):
        self.__established_connections.put(
            self.__current_server_connection
        )

    def __stop_all_established_connections(self):
        self.__logger.debug(STOPPING_ESTABLISHED_MESSAGE)
        established_connections = self.__established_connections
        while not established_connections.empty():
            established_connection = established_connections.get_nowait()
            established_connection.stop()
        self.__logger.debug(STOPPED_ESTABLISHED_MESSAGE.format(
            established_connections.qsize()
        ))

    def __stop_current_server_connection(self):
        try:
            self.__current_server_connection.stop()
        except AttributeError:
            self.__logger.debug(SERVER_CONNECTION_NOT_CREATED)
        except RuntimeError:
            self.__logger.debug(SERVER_CONNECTION_NOT_STARTED)

    def __close_bound_socket(self):
        try:
            self.__logger.debug(SHUTTING_DOWN_MASTER_SOCKET_MESSAGE)
            self.__master_socket.shutdown(socket.SHUT_RDWR)
            self.__logger.debug(SHUT_DOWN_MASTER_SOCKET_MESSAGE)
        except Exception as e:
            self.__logger.critical(MASTER_SOCKET_FAILURE_MESSAGE.format(e))

        try:
            self.__logger.debug(CLOSING_MASTER_SOCKET_MESSAGE)
            self.__master_socket.close()
            self.__logger.debug(CLOSED_MASTER_SOCKET_MESSAGE)
        except Exception as e:
            self.__logger.critical(MASTER_SOCKET_FAILURE_MESSAGE.format(e))


CONSTRUCTOR_MESSAGE = "Created a new ServerConnectionProvider"

CREATING_SERVER_CONNECTION_MESSAGE = "Creating a new ServerConnection..."

CREATED_SERVER_CONNECTION_MESSAGE = "ServerConnection creation succeeded."

STARTING_SERVER_CONNECTION_MESSAGE = "Starting current ServerConnection..."

STARTED_SERVER_CONNECTION_MESSAGE = "Started ServerConnection successfully."

SERVER_CONNECTION_NOT_CREATED = "Can't stop ServerConnection; it hasn't been "\
                                "created."

SERVER_CONNECTION_NOT_STARTED = "Can't stop ServerConnection; it hasn't "\
                                "started."

STOPPING_ESTABLISHED_MESSAGE = "Stopping all established connections..."

STOPPED_ESTABLISHED_MESSAGE = "Successfully stopped {} established "\
                              "connections."

CLOSING_MASTER_SOCKET_MESSAGE = "Closing master socket..."

CLOSED_MASTER_SOCKET_MESSAGE = "Successfully closed master socket."

SHUTTING_DOWN_MASTER_SOCKET_MESSAGE = "Shutting down master socket..."

SHUT_DOWN_MASTER_SOCKET_MESSAGE = "Successfully shut down master socket."

MASTER_SOCKET_FAILURE_MESSAGE = "Something happened when shutting_down/"\
                                "closing master socket: {}"

STOPPING_MESSAGE = "Stopping ServerConnectionProvider..."

STOPPED_MESSAGE = "ServerConnectionProvider stopped successfully."
