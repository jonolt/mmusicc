#  Copyright (c) 2020 Johannes Nolte
#  SPDX-License-Identifier: GPL-3.0-or-later

import datetime
import logging
import logging.config
import pathlib
import shutil
import textwrap


def copy_log_file(path_target):
    """copy current log file of FileHandler to target path

    Returns:
        pathlib.Path: actual path of target
    """
    org_log_path = getattr(logging.Logger, "manager").root.handlers[1].baseFilename
    path_target = pathlib.Path(path_target)
    if path_target.exists():
        path_target = path_target.parent.joinpath(
            path_target.stem
            + datetime.datetime.now().strftime("-%Y%m%d-%H%M%S")
            + path_target.suffix
        )
    shutil.copyfile(org_log_path, path_target)
    return path_target


def del_log_file():
    """delete current log file of FileHandler"""
    if get_log_file():
        get_log_file().unlink()


def get_log_file():
    """
    Returns:
        pathlib.Path: path of file logged to by FileHandler
    """
    manager = getattr(logging.Logger, "manager")

    if not manager.root.handlers:
        return None

    if "LogCaptureHandler" in str(manager.root.handlers):
        # mmusicc was started from pytest. pytest adds a LogCaptureHandler to logger.
        # Which causes init logger to think the logger is already initialized and does
        # not add root or file handlers. Since it is not wanted when testing anyway,
        # this is quite convenient. As there is no file handler there is no file.
        return None

    return pathlib.Path(
        getattr(logging.Logger, "manager").root.handlers[1].baseFilename
    )


class MultiLineFormatter(logging.Formatter):
    def format(self, record):
        message = record.msg
        record.msg = ""
        header = super().format(record)
        msg = textwrap.indent(message, " " * len(header)).lstrip()
        record.msg = message
        return header + msg


def generate_logger_config(file_path, log_level):
    return {
        "version": 1,
        "formatters": {
            "simple": {
                "()": MultiLineFormatter,
                "format": "%(asctime)s.%(msecs)03d %(levelname)-8s %(module)-13s %(message)s",  # noqa
                "datefmt": "%H:%M:%S",
            },
            "short": {
                "()": MultiLineFormatter,
                "format": "%(asctime)s.%(msecs)03d %(message)s",
                "datefmt": "%H:%M:%S",
            },
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "level": log_level,
                "formatter": "short" if log_level == 25 else "simple",
                "stream": "ext://sys.stdout",
            },
            "file_handler": {
                "class": "logging.FileHandler",
                "filename": str(file_path),
                "formatter": "simple",
                "level": "DEBUG",
                "mode": "a",
            },
        },
        "root": {
            "level": "DEBUG",
            "handlers": ["console", "file_handler"],
        },
    }


def init_logger(level=25, file_path=None):
    """Initialise Python Logger (function may be extended in future)

    Args:
        level (int): log level for console output
        file_path(str or pathlib.Path or None): file path of log file. If None a
            logfile with a unique name is created at the current working directory,
            which must be deleted manually. If path exits log is append to file.
            Defaults to None.

    Returns:
        pathlib.Path: path of log file
    """
    # when run from the console there will be no handlers
    # FIXME is this really necessary?
    if len(logging.getLogger().handlers):
        logging.debug("Logger Already Initialized, Skipping.")
        return

    if not file_path:
        file_path = pathlib.Path(
            "mmusicc" + datetime.datetime.now().strftime("-%Y%m%d-%H%M%S") + ".log"
        )

    file_path = pathlib.Path(file_path)
    file_path = file_path.expanduser().resolve()

    config = generate_logger_config(file_path, level)
    logging.config.dictConfig(config)
    logging.debug("Initialized logger")
    logging.addLevelName(25, "mmusicc")

    return file_path
