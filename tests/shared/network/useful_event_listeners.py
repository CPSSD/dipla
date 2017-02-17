from dipla.shared.network.network_connection import EventListener


class EventSavingEventListener(EventListener):

    def __init__(self):
        self.last_message_object = None
        self.last_error = None
        self.closed = False
        self.opened = False

    def on_open(self, connection, message_object):
        self.opened = True

    def on_message(self, connection, message_object):
        self.last_message_object = message_object

    def on_error(self, connection, error):
        self.last_error = error

    def on_close(self, connection, reason):
        self.closed = True


class EchoEventListener(EventListener):

    def __init__(self):
        self.last_message_object = None

    def on_open(self, connection, message_object):
        pass

    def on_error(self, connection, error):
        pass

    def on_close(self, connection, reason):
        pass

    def on_message(self, connection, message_object):
        self.last_message_object = message_object
        message_object['data'] = "Echo: " + message_object['data']
        connection.send(message_object)
