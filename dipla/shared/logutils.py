from logging import getLogger
from logging import DEBUG
from logging import FileHandler
from logging import Formatter
import threading


# Initialises the logger.
#
# Allows custom logging configuration to be set.
#
# WARNING:
# Calling this multiple times will result in undesired behaviour
# such as duplicated log output.
#
def init(level=DEBUG,
         handler=FileHandler("DIPLA.log"),
         format_="%(asctime)s - %(levelname)s - %(name)s - %(message)s"):
    handler.setFormatter(Formatter(format_))
    logger = getLogger()
    logger.setLevel(level)
    logger.addHandler(handler)
    return logger
