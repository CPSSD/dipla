from queue import Queue, Empty

DIGITS = ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9']


class MessageDefixer(object):
    """
    Allows the prefix of a message to be removed when fed a single character
    at a time.

    Stores each fully formed message within a queue that can be accessed later.

    Throws IllegalHeaderExceptions when malicious characters are fed into the
    message header, which can be used to disconnect potentially malicious
    users.
    """

    READ_HEADER_STATE = 0
    READ_BODY_STATE = 1

    def __init__(self):
        self._full_messages = Queue()
        self._state = 0
        self._feed_buffer = ""
        self._expected_message_length = 0

    def feed_character(self, character):
        if character != "":
            self._feed_buffer += character
            if self._state == MessageDefixer.READ_HEADER_STATE:
                if character in DIGITS:
                    pass
                elif character == ':':
                    self._expected_message_length = int(self._feed_buffer[:-1])
                    self._feed_buffer = ""
                    self._increment_state()
                else:
                    error = "Header must be numeric. Was fed: '{}'"
                    raise IllegalHeaderException(error.format(character))
            elif self._state == MessageDefixer.READ_BODY_STATE:
                if len(self._feed_buffer) == self._expected_message_length:
                    self._full_messages.put(self._feed_buffer)
                    self._feed_buffer = ""
                    self._increment_state()

    def get_defixed_message(self):
        try:
            return self._full_messages.get_nowait()
        except Empty:
            raise NoMessageException()

    def get_state(self):
        return self._state

    def _increment_state(self):
        self._state += 1
        if self._state == 2:
            self._state = 0


class NoMessageException(Exception):
    pass


class IllegalHeaderException(Exception):
    pass
