#  Copyright (c) 2023 Johannes Nolte
#  SPDX-License-Identifier: GPL-3.0-or-later
import pathlib
import shlex

from mmusicc.__main__ import main

if __name__ == "__main__":

    source_path = pathlib.Path("~/Desktop/test_mmusicc/The_Open_Door_(2006)").parent

    target_path = pathlib.Path("~/Desktop/test_mmusicc_target")
    whitelist_path = "~/Music/Music/whitelist_minimal.txt"

    cmd_bash = f'-s {str(source_path)} -t {str(target_path)} -f .mp3 --white-list-tags {str(whitelist_path)} --delete-existing-metadata --delete-files --ffmpeg-options "-codec:a libmp3lame -qscale:a 2 -codec:v copy" -v'
    cmd_argv = shlex.split(cmd_bash, comments=False, posix=True)

    main(cmd_argv)
