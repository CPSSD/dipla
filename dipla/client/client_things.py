from dipla.shared.network.network_connection import EventListener


class ClientEventListener(EventListener):

    def __init__(self, services):
        self.__services = services
        self.__has_connected = False
        self.__last_error = None

    def on_error(self, connection, error):
        self.__last_error = error

    def on_message(self, connection, message_object):
        service_name = message_object['label']
        service_arguments = message_object['data']
        service = self.__services[service_name]
        service_result = service.execute(service_arguments)
        connection.send(service_result)

    def on_close(self, connection, reason):
        pass

    def on_open(self, connection, message):
        self.__has_connected = True

    # Useful methods

    def has_connected(self):
        return self.__has_connected

    def has_errored(self):
        return self.__last_error is not None

    def last_error(self):
        return self.__last_error

    def refused_to_connect(self):
        return isinstance(self.__last_error, ConnectionRefusedError)
