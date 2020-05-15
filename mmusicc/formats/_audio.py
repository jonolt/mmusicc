#  Copyright (c) 2020 Johannes Nolte
#  SPDX-License-Identifier: GPL-3.0-or-later

import pathlib

from mmusicc.util.metadatadict import MetadataDict


class AudioFile:
    """Base class for all audio files wrapping tags and audio stream info.

    Attributes:
        _file       (pathlib.Path): file path of file.
        _dict_meta  (MetadataDict): metadata from file (the parsed one)
        unprocessed_tag     (dict): metadata that could'nt be associated.
            Manly used to manually update the association list with new
            tags/tag names.
    """

    def __init__(self):
        self._dict_meta = MetadataDict()
        self._file = None
        self._changed_tags = None
        self.unprocessed_tag = dict()

    @property
    def file_path(self):
        """pathlib.Path: file path of audio file."""
        return pathlib.Path(self._file.filename)

    @property
    def dict_meta(self):
        """MetadataDict: metadata of the audio file (the parsed one)."""
        return self._dict_meta

    @dict_meta.setter
    def dict_meta(self, value):
        if isinstance(value, MetadataDict):
            self._dict_meta = value
        else:
            raise TypeError("only MetadataDict allowed")

    def file_read(self):
        """reads file tags into AudioFile tag dictionary (dict_meta)."""
        raise NotImplementedError

    def file_save(self, remove_existing=False, write_empty=False, dry_run=False):
        """saves file tags from tag dictionary (dict_meta) to AudioFile.

        Args:
            remove_existing (bool): if true clear all tags before writing.
                Defaults to False.
            write_empty     (bool): if true write tags with Empty Value, if
                false, the tag will not be created and a existing tag will be
                deleted. Behaviour might slightly differ between tag types.
                Defaults to False.
            dry_run (bool): if true, do anything but saving to file. Defaults to False

        Returns:
            int: 1 if data was saved to file, zero if nothing was changed on file.
        """
        raise NotImplementedError
