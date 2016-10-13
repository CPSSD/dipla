import logging
import threading


class LoggerInitialiser(object):

    INITIALISED = False

    def __init__(self, logger):
        self._logger = logger

    def initialise_if_necessary(self):
        if not LoggerInitialiser.INITIALISED:
            self._initialise_logger()

    def _initialise_logger(self):
        self._logger.setLevel(logging.DEBUG)
        file_handler = logging.FileHandler("DIPLA.LOG")
        file_handler.setLevel(logging.DEBUG)
        formatter = logging.Formatter(
            "%(asctime)s - %(levelname)s - %(name)s - %(message)s"
        )
        file_handler.setFormatter(formatter)
        self._logger.addHandler(file_handler)
        LoggerInitialiser.INITIALISED = True


def get_logger(logger_name):
    logger = logging.getLogger(logger_name)
    logger_initialiser = LoggerInitialiser(logger)
    logger_initialiser.initialise_if_necessary()
    return logger
