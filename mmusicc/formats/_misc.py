"""

Attributes:
    mimes (set): A set of supported mime types. Empty until init.
    types (set): A set of AudioFile subclasses. Empty until init.
    loaders(dict): A dict mapping file extensions to loaders
        (function returning an AudioFile object). Empty until init.

"""


import logging
import os

from mmusicc import util

mimes = set()

loaders = {}

types = set()


def init():
    """Initialize the formats module, loading all formats for loader.

    Before this is called loading a file and unpickling will not work.
    If the module was already initialized, the initialisation is skipped.
    """

    global mimes, loaders, types

    if loaders:
        logging.debug("Formats Already Initialized, Skipping.")
        return

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


def get_loader(file_path):
    """Returns a callable which takes a filename and returns AudioFile

    or raises AudioFileError, or returns None.

    Args:
        file_path (str or pathlib.Path): file to get loader for.
    Returns:
        obj: callable object which can handle given file.

    """
    ext = os.path.splitext(file_path)[-1]
    return loaders.get(ext.lower())


# noinspection PyPep8Naming
def MusicFile(file_path):
    """Returns a AudioFile instance or None if file type is not supported

    Note:
        Make sure that allocationmap is initialized before loading any files.

    Args:
        file_path (pathlib.Path): path of file to load as MusicFile

    Returns:
        AudioFile: audio file instance of file in specified path
    """
    loader = get_loader(file_path)
    if loader is not None:
        return loader(file_path)
    else:
        logging.error("FileType not supported")
        raise Exception(
            "FileType '{}' not supported. Supported Loaders: {}".format(
                os.path.splitext(str(file_path))[-1], str(loaders)
            )
        )


class AudioFileError(Exception):
    """Base error for AudioFile, mostly IO/parsing related operations"""


class MutagenBug(AudioFileError):
    """Raised in is caused by a mutagen bug, so we can highlight it"""
