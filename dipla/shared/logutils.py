from logging import *
import threading


LOGGER_INITIALISED = False


def get_logger(module_name, level=DEBUG, handler=FileHandler("DIPLA.log"),
               format_="%(asctime)s - %(levelname)s - %(name)s - %(message)s"):

    logger = getLogger(module_name)

    global LOGGER_INITIALISED
    if LOGGER_INITIALISED:
        return logger

    logger.setLevel(level)

    formatter = Formatter(format_)
    handler.setFormatter(formatter)

    logger.addHandler(handler)

    LOGGER_INITIALISED = True
    return logger
