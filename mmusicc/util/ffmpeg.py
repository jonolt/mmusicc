"""
Module adapted and copied from:
https://github.com/Ch00k/ffmpy

"""

import errno
import logging
import subprocess


class FFmpeg(object):
    """Wrapper for `FFmpeg <https://www.ffmpeg.org/>`.

    Args:
        source     (str): path to source file
        target     (str): path to target file
        options    (str): string containing options for ffmpeg as use in
            console (arguments separated by space)
        executable (str, optional): path to ffmpeg executable. Defaults to
            'ffmpeg': Can be overwritten in case e.g libav is used.
    """

    def __init__(self, source, target, options=None, executable="ffmpeg"):
        """Initialize ffmpeg command line wrapper.

        """
        self.executable = executable
        self._cmd = [executable]

        self._cmd.extend(["-i", source])
        if options:
            self._cmd.extend(options.split())
        self._cmd.extend([target])

        self.cmd = subprocess.list2cmdline(self._cmd)
        self.process = None

    def __repr__(self):
        return "<{0!r} {1!r}>".format(self.__class__.__name__, self.cmd)

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
                logging.error(
                    "ffmpeg path not found. either ffmpeg is not "
                    "installed are not at the standard path."
                )
                raise FFExecutableNotFoundError(
                    "Executable '{0}' not found".format(self.executable)
                )
            else:
                raise

        catchers = ["Input #0", "Stream #0:", "Output #0"]

        for line in process_result.stderr.decode().split("\n"):
            for catch in catchers:
                if catch in line:
                    logging.log(25, line.strip())

        logging.debug(process_result.stderr.decode())

        if process_result.returncode != 0:
            logging.error(
                "command \n{}\n produced the following error:\n {}".format(
                    self.cmd, process_result.stderr
                )
            )
            raise FFRuntimeError(
                self.cmd,
                process_result.returncode,
                process_result.stdout,
                process_result.stderr,
            )


class FFExecutableNotFoundError(Exception):
    """Raise when ffmpeg executable was not found."""


class FFRuntimeError(Exception):
    """Raise when ffmpeg command line execution returns a non-zero exit code.

    """

    def __init__(self, cmd, exit_code, stdout, stderr):
        self.cmd = cmd
        self.exit_code = exit_code
        self.stdout = stdout
        self.stderr = stderr

        message = "`{0}` exited with status {1}\n\nSTDOUT:\n{2}\n\nSTDERR:\n{3}".format(
            self.cmd, exit_code, (stdout or b"").decode(), (stderr or b"").decode()
        )

        super(FFRuntimeError, self).__init__(message)
