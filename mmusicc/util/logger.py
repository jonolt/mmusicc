import logging.config
import logging


def init_logger(level):
    # noinspection PyPep8
    config = {
        "version": 1,
        "formatters": {
            "simple": {
                "format":
                    '%(asctime)s %(levelname)-8s %(module)-13s %(message)s',
            }
        },
        "handlers": {
            "console": {
                "class": 'logging.StreamHandler',
                # "level": level if level == logging.DEBUG else logging.ERROR,
                "level": level,
                "formatter": 'simple',
                "stream": 'ext://sys.stdout',
            },
        },
        "root": {
            "level": level,
            "handlers": ['console'],
        }
    }
    logging.config.dictConfig(config)
    logging.debug("Initialized logger")
    logging.addLevelName(25, "MMUSICC")
