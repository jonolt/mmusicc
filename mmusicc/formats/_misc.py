# Copyright 2016 Christoph Reiter
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.

import os
import sys

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

        # Migrate pre-0.16 library, which was using an undocumented "feature".
        sys.modules[name.replace(".", "/")] = form
        # Migrate old layout
        if name.startswith("quodlibet."):
            sys.modules[name.split(".", 1)[1]] = form

    # This can be used for the quodlibet.desktop file
    desktop_mime_types = "MimeType=" + \
        ";".join(sorted({m.split(";")[0] for m in mimes})) + ";"
    print(desktop_mime_types)

    s = ", ".join(sorted(module_names))
    print("Supported formats: %s" % s)

    if not loaders:
        raise SystemExit("No formats found!")


def get_loader(filename):
    """Returns a callable which takes a filename and returns
    AudioFile or raises AudioFileError, or returns None.
    """

    ext = os.path.splitext(filename)[-1]
    return loaders.get(ext.lower())


def MusicFile(filename):
    """Returns a AudioFile instance or None"""

    loader = get_loader(filename)
    if loader is not None:
        return loader(filename)
    else:
        print("Filetype not supported")


def ext_supported(filename):
    """Returns True if the file extension is supported"""

    return get_loader(filename) is not None
