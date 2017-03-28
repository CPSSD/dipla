import logging
from logging import DEBUG
from logging import FileHandler
from logging import Formatter
import threading


class LogUtils:

    logger = logging.getLogger(__name__)

    # Initialises the logger.
    #
    # Allows custom logging configuration to be set.
    #
    # WARNING:
    # Calling this multiple times will result in undesired behaviour
    # such as duplicated log output.
    @staticmethod
    def init(level=DEBUG,
             handler=FileHandler("DIPLA.log"),
             format_="%(asctime)s - %(levelname)s - %(name)s - %(message)s"):
        handler.setFormatter(Formatter(format_))
        LogUtils.logger = logging.getLogger()
        LogUtils.logger.setLevel(level)
        LogUtils.logger.addHandler(handler)

    @staticmethod
    def debug(message):
        """
        Params:
         - message is a string containing the debug message to be logged
        """
        LogUtils.logger.debug(message)

    @staticmethod
    def warning(message):
        """
        Params:
         - message is a string containing the warning to be logged
        """
        LogUtils.logger.warning(message)

    @staticmethod
    def error(message, error):
        """
        Params:
         - message is a string containing the error to be logged
         - error is the error object to be logged
        """
        LogUtils.logger.error("%s: %s" % (message, error))
