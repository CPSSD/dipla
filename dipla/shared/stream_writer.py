from threading import Thread
from .logutils import get_logger


# This class writes a message to a stream in a separate thread.
#
# To use it:
# 1. Instantiate a StreamWriter with a stream and a message.
# 2. Call the `start` method.
#
# To write another message, you will need a new StreamWriter instance.
class StreamWriter(Thread):

    def __init__(self, stream, message):
        super().__init__()
        self._logger = get_logger(__name__)
        self._stream = stream
        self._message = message

    # Override
    def run(self):
        log_message = "StreamWriter: about to write {} to {}."
        self._logger.debug(log_message.format(self._message, self._stream))
        self._stream.write(self._message)
