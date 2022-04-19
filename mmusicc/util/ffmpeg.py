#  Copyright (c) 2020 Johannes Nolte
#  SPDX-License-Identifier: GPL-3.0-or-later

import errno
import json
import logging
import subprocess
import typing


class FFmpeg(object):
    """Wrapper for `FFmpeg <https://www.ffmpeg.org/>`.

    Args:
        source     (pathlib.path): path to source file
        target     (pathlib.path): path to target file
        options    (str): string containing options for ffmpeg as use in
            console (arguments separated by space)
        executable (str, optional): path to ffmpeg executable. Defaults to
            'ffmpeg': Can be overwritten in case e.g. libav is used.
    """

    def __init__(self, source, target, options=None, executable="ffmpeg"):
        """Initialize ffmpeg command line wrapper."""
        self.executable = executable
        self._source = source
        self._target = target
        self._cmd = [executable]
        self.exit_status = -1

        self._cmd.extend(["-i", str(source)])
        if options:
            self._cmd.extend(options.split())
        self._cmd.append(str(target))

        self.cmd = subprocess.list2cmdline(self._cmd)
        self.process = None

    def __repr__(self):
        return "<{0!r} {1!r}>".format(self.__class__.__name__, self.cmd)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if not self.exit_status == 0:
            if self._target.exists():
                self._target.unlink()

    def run(self):
        """Execute ffmpeg command line. Log stderr output.

        Raises:
            FFRuntimeError           : in case ffmpeg command exits with a
                non-zero code.
            FFExecutableNotFoundError: in case the executable path passed
                as not valid.
        """

        try:
            process_result = subprocess.run(self._cmd, stderr=subprocess.PIPE)
        except OSError as e:
            if e.errno == errno.ENOENT:
                raise FFExecutableNotFoundError(
                    "Executable '{0}' not found".format(self.executable)
                )
            else:
                raise

        logging.debug(process_result.stderr.decode())

        self.exit_status = process_result.returncode
        if self.exit_status != 0:
            raise FFRuntimeError(
                self.cmd,
                process_result.returncode,
                process_result.stdout,
                process_result.stderr,
            )


class FFProbeResult(typing.NamedTuple):
    return_code: int
    std_out_json: str
    error: str


def ffprobe(file_path) -> FFProbeResult:
    command_array = [
        "ffprobe",
        "-v",
        "quiet",
        "-print_format",
        "json",
        "-show_format",
        "-show_streams",
        file_path,
    ]
    result = subprocess.run(
        command_array,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        universal_newlines=True,
    )
    return FFProbeResult(
        return_code=result.returncode, std_out_json=result.stdout, error=result.stderr
    )


def audio_format_name(file_path):
    result = ffprobe(file_path)
    if result.return_code == 0:
        return json.loads(result.std_out_json)["format"]["format_name"]
    return False


class FFExecutableNotFoundError(Exception):
    """Raise when ffmpeg executable was not found."""


class FFRuntimeError(Exception):
    """Raise when ffmpeg command line execution returns a non-zero exit code."""

    def __init__(self, cmd, exit_code, stdout, stderr):
        self.cmd = cmd
        self.exit_code = exit_code
        self.stdout = (stdout or b"").decode()
        self.stderr = (stderr or b"").decode()

        message = "`{0}` exited with status {1}\n\nSTDOUT:\n{2}\n\nSTDERR:\n{3}".format(
            self.cmd, exit_code, stdout, stderr
        )

        super(FFRuntimeError, self).__init__(message)
