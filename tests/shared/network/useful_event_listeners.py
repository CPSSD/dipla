from dipla.shared.network.network_connection import EventListener


class EventSavingEventListener(EventListener):

    def __init__(self):
        self.last_message = None
        self.last_error = None
        self.closed = False
        self.opened = False

    def on_open(self, connection, message):
        self.opened = True

    def on_message(self, connection, message):
        self.last_message = message

    def on_error(self, connection, error):
        self.last_error = error

    def on_close(self, connection, reason):
        self.closed = True


class EchoEventListener(EventListener):

    def __init__(self):
        self.last_message = None

    def on_open(self, connection, message):
        pass

    def on_error(self, connection, error):
        pass

    def on_close(self, connection, reason):
        pass

    def on_message(self, connection, message):
        self.last_message = message
        message = "Echo: " + message
        connection.send(message)
