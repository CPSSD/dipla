import logging
import threading


LOGGER_INITIALISED = False


def get_logger(logger_name):

    logger = logging.getLogger(logger_name)
    
    global LOGGER_INITIALISED

    if not LOGGER_INITIALISED:
        logger.setLevel(logging.DEBUG)
        file_handler = logging.FileHandler("DIPLA.LOG")
        file_handler.setLevel(logging.DEBUG)
        formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
        LOGGER_INITIALISED = True

    return logger



class ThreadedLogBoy(threading.Thread):

    def run(self):
        logger = get_logger(__name__)
        logger.debug("hi")
        logger.info("boys")
        logger.warning("there")
        logger.error("is")
        logger.critical("mario")




if __name__ == "__main__":
    l = get_logger(__name__)
    l.debug("Testing 123")
    logboy = ThreadedLogBoy()
    logboy.start()
