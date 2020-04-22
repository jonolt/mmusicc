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
                "format": "%(asctime)s %(levelname)-8s %(module)-13s %(message)s",
            }
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                # "level": level if level == logging.DEBUG else logging.ERROR,
                "level": level,
                "formatter": "simple",
                "stream": "ext://sys.stdout",
            },
        },
        "root": {"level": level, "handlers": ["console"],},
    }
    logging.config.dictConfig(config)
    logging.debug("Initialized logger")
    logging.addLevelName(25, "mmusicc")
