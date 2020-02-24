import logging


def init(path_config):
    """initialize all modules, which must be initialized"""
    _init_logging()
    logging.log(25, "testing mmusicc log level. remove in future commit")
    _init_formats()
    logging.debug("Initialized mmusicc")
    _init_allocationmap(path_config)
    logging.debug("Initialized _init_allocationmap")


def _init_allocationmap(path_config):
    from mmusicc.util import allocationmap
    allocationmap.init_allocationmap(path_config)


def _init_formats():
    """initialize formats module"""
    from mmusicc.formats import init
    init()


def _init_logging():
    """initialize logger"""
    from mmusicc.util import init_logger
    init_logger(logging.DEBUG)
