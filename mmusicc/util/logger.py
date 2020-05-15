#  Copyright (c) 2020 Johannes Nolte
#  SPDX-License-Identifier: GPL-3.0-or-later

import logging
import logging.config


def init_logger(level=25):
    """Initialise Python Logger (function may be extended in future)"""

    if len(logging.getLogger().handlers):
        logging.debug("Logger Already Initialized, Skipping.")
        return

    # noinspection PyPep8
    config = {
        "version": 1,
        "formatters": {
            "simple": {
                "format": "%(asctime)s.%(msecs)03d %(levelname)-8s %(module)-13s %(message)s",
                "datefmt": "%H:%M:%S",
            },
            "short": {
                "format": "%(asctime)s.%(msecs)03d %(message)s",
                "datefmt": "%H:%M:%S",
            },
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                # "level": level if level == logging.DEBUG else logging.ERROR,
                "level": level,
                "formatter": "short" if level == 25 else "simple",
                "stream": "ext://sys.stdout",
            },
        },
        "root": {"level": level, "handlers": ["console"],},
    }
    logging.config.dictConfig(config)
    logging.debug("Initialized logger")
    logging.addLevelName(25, "mmusicc")
