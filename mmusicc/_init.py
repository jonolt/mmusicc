import logging


def init():
    _init_logging()
    logging.log(25, "testing mmusicc log level. remove in future commit")
    _init_formats()
    logging.debug("Initialized mmusicc")


def _init_formats():
    from mmusicc.formats import init
    init()


def _init_logging():
    from mmusicc.util import init_logger
    init_logger(logging.DEBUG)
