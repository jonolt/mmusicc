#  Copyright (c) 2023 Johannes Nolte
#  SPDX-License-Identifier: GPL-3.0-or-later

if __name__ == "__main__":
    import os
    import pathlib
    import shlex
    from mmusicc.__main__ import main

    working_dir = "~/Drives/Music/.management/"
    options = '-h'
    options = options + " --dry-run"

    os.chdir(working_dir)

    cmd_argv = shlex.split(options, comments=False, posix=True)
    main(cmd_argv)
