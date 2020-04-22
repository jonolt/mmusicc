import logging


def init(path_config):
    """initialize all modules, which must be initialized

    can be done individually too.

    Args:
        path_config (str): path to allocation map config yaml file. Can be
            None, use at own risk!
    """
    init_logging()
    logging.log(25, "testing mmusicc log level. remove in future commit")
    init_formats()
    if path_config:
        init_allocationmap(path_config)


def init_allocationmap(path_config):
    """initialize allocation map of tags.

    Args:
        path_config (str): path to allocation map config yaml file
    """
    from mmusicc.util import allocationmap

    allocationmap.init_allocationmap(path_config)


def init_formats():
    """initialize formats module"""
    from mmusicc.formats import init

    init()


def init_logging(level=25):
    """initialize logger"""
    from mmusicc.util import init_logger

    init_logger(level=level)
