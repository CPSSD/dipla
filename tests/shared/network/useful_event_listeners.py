from dipla.shared.network.network_connection import EventListener


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
