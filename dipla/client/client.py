import time
import os
from dipla.shared.message_generator import generate_message


class Client(object):

    def __init__(self, event_listener, connection, quality_scorer, password):
        self.__event_listener = event_listener
        self.__connection = connection
        self.__quality_scorer = quality_scorer
        self.__password = password

    def start(self):
        self.__connection.start()
        self.__wait_until_connected(timeout_in_seconds=10)
        self.__send_binary_request()

    def __wait_until_connected(self, timeout_in_seconds):
        start_time = time.time()
        end_time = start_time + timeout_in_seconds
        while True:
            if time.time() < end_time:
                break
            if self.__event_listener.has_connected():
                return
            if self.__event_listener.has_errored():
                raise self.__event_listener.last_error()

    def __send_binary_request(self):
        data = {
            'platform': _get_platform(),
            'quality': self.__quality_scorer.get_quality(),
        }
        if self.__password != '':
            data['password'] = self.__password
        message_object = generate_message('get_binaries', data)
        self.__connection.send(message_object)


def _get_platform():
    """Get some information about the platform the client is running on."""
    if os.name == 'posix':
        return ''.join(os.uname())
    # TODO(ndonn): Add better info for Windows and Mac versions
    return os.name
