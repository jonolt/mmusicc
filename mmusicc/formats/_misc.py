import logging
import os

from mmusicc import util


class AudioFileError(Exception):
    """Base error for AudioFile, mostly IO/parsing related operations"""


class MutagenBug(AudioFileError):
    """Raised in is caused by a mutagen bug, so we can highlight it"""


mimes = set()
"""A set of supported mime types"""

loaders = {}
"""A dict mapping file extensions to loaders (func returning an AudioFile)"""

types = set()
"""A set of AudioFile subclasses/implementations"""


def init():
    """Load/Import all formats.

    Before this is called loading a file and unpickling will not work.
    """

    global mimes, loaders, types

    base = util.get_module_dir()
    formats = util.importhelper.load_dir_modules(base, package=__package__)

    module_names = []
    for form in formats:
        name = form.__name__

        for ext in form.extensions:
            loaders[ext] = form.loader

        types.update(form.types)

        if form.extensions:
            for type_ in form.types:
                mimes.update(type_.mimes)
            module_names.append(name.split(".")[-1])

    s = ", ".join(sorted(module_names))

    logging.info("Initialized modules. Supported formats: {}.".format(s))

    if not loaders:
        raise SystemExit("No formats found!")


def get_loader(filename):
    """Returns a callable which takes a filename and returns
    AudioFile or raises AudioFileError, or returns None.
    """
    ext = os.path.splitext(filename)[-1]
    return loaders.get(ext.lower())


# noinspection PyPep8Naming
def MusicFile(filename):
    """Returns a AudioFile instance or None"""
    loader = get_loader(filename)
    if loader is not None:
        return loader(filename)
    else:
        logging.error("Filetype not supported")


def ext_supported(filename):
    """Returns True if the file extension is supported"""

    return get_loader(filename) is not None
