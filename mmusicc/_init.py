#  Copyright (c) 2020 Johannes Nolte
#  SPDX-License-Identifier: GPL-3.0-or-later

"""
recommended init order:
- init_logging
- init_formats
- init_allocationmap
"""


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


def init_logging(level=25, file_path=None):
    """initialize logger"""
    from mmusicc.util import init_logger

    return init_logger(level=level, file_path=file_path)
