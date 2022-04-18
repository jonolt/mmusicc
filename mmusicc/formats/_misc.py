"""

Attributes:
    mimes (set): A set of supported mime types. Empty until init.
    types (set): A set of AudioFile subclasses. Empty until init.
    loaders(dict): A dict mapping file extensions to loaders
        (function returning an AudioFile object). Empty until init.

"""


import logging
import mimetypes
import os

import mutagen

from mmusicc import util
from mmusicc.formats._audio import AudioFile

mimes = set()

loaders = {}

types = set()


def init():
    """Initialize the formats' module, loading all formats for loader.

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


def is_supported_audio(file):
    """Return True if file is a supported audio file."""
    mimetype = mimetypes.guess_type(str(file))

    if mimetype[0] in mimes:
        return True
    else:
        return False


def is_audio(file):
    """Return True if file is a supported audio file."""
    mimetype = mimetypes.guess_type(str(file))
    if mimetype[0] is None:
        return False
    return mimetype[0].startswith("audio")


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
        if is_audio(file_path):
            logging.debug(f"loading UnsupportedAudio with file {file_path}")
            return UnsupportedAudio(file_path)
        else:
            logging.error("File is not a audio!")
            raise NoAudioFileError("File is not a audio!")


class UnsupportedAudio(AudioFile):
    def __init__(self, file_path):
        super().__init__()
        self._file = mutagen.File(file_path)
        if self._file is None:
            raise NoAudioFileError(
                f"file of mime type '{mimetypes.guess_type(file_path)}' is no audio file"
            )

    def __repr__(self):
        return str(self._file)

    def file_read(self):
        logging.debug("trying to read metadata from unsupported audio file")

    def file_save(self, remove_existing=False, write_empty=False, dry_run=False):
        logging.warning("trying to save metadata to unsupported audio file")
        return 0


class NoAudioFileError(Exception):
    """file is not an audio file"""


class AudioFileError(Exception):
    """Base error for AudioFile, mostly IO/parsing related operations"""


class MutagenBug(AudioFileError):
    """Raised in is caused by a mutagen bug, so we can highlight it"""
