#  Copyright (c) 2020 Johannes Nolte
#  SPDX-License-Identifier: GPL-3.0-or-later

import distutils.util
import logging
import sys

if __package__ is None and not hasattr(sys, "frozen"):
    # direct call of __main__.py
    import os.path

    path = os.path.realpath(os.path.abspath(__file__))
    sys.path.insert(0, os.path.dirname(os.path.dirname(path)))


def main(args=None):

    if args is None:
        args = sys.argv[1:]

    import mmusicc
    from mmusicc.util.logger import del_log_file, get_log_file

    try:
        m = mmusicc.MmusicC(args)
        if get_log_file():
            if not m.pre_result_logfile and m.error > 0:
                if distutils.util.strtobool(
                    input(
                        "One or more errors occurred during synchronisation.\n"
                        "Save log file to current working directory? [y/n] "
                    )
                ):
                    print(f"Log file can be found at: {get_log_file().resolve()}")
                else:
                    del_log_file()
            else:
                del_log_file()

        sys.exit(0)

    except Exception:
        logging.error("Exception occurred", exc_info=True)
        if "--log-file" in args:
            print("A error occurred in python, stack trace saved to log file.")
        else:
            if get_log_file():
                if distutils.util.strtobool(
                    input(
                        "A error occurred in python, save log file with stack trace to "
                        "current working directory? [y/n] "
                    )
                ):
                    print(f"Log file can be found at: {get_log_file().resolve()}")
                else:
                    del_log_file()

        sys.exit(1)


if __name__ == "__main__":
    main()
