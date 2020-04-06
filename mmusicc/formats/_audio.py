import logging

from mmusicc.util.misc import MetadataDict
from mmusicc.util.path import PATH, hash_filename


class AudioFile:
    """Base class for all audio files wrapping tags and audio stream info

    Attributes:
        file_path        (str): file path of file.
        _dict_meta       (dict): metadata from file (the parsed one)
        unprocessed_tag (dict): metadata that could'nt be associated. Manly
        used to manually update the association list with new tags/tag names.
    """

    def __init__(self, file_path):
        self.set_file_path(file_path)
        self._dict_meta = MetadataDict()
        self.unprocessed_tag = dict()
        self._file = None

    @property
    def file_path(self):
        return getattr(self, PATH)

    def set_file_path(self, path):
        tmp_fn_hash = hash_filename(path)
        for key in hash_filename(path):
            setattr(self, key, tmp_fn_hash[key])

    @property
    def dict_meta(self):
        return self._dict_meta

    @dict_meta.setter
    def dict_meta(self, value):
        if isinstance(value, MetadataDict):
            self._dict_meta = value
        else:
            raise TypeError("only MetadataDict allowed")

    def file_read(self):
        """reads file tags into AudioFile tag dictionary."""
        raise NotImplementedError

    def file_save(self, remove_existing=False, write_empty=False):
        """saves file tags to AudioFile from tag dictionary.

        Args:
            remove_existing (bool): if true clear all tags before writing.
                Defaults to False.
            write_empty     (bool): if true write empty tags, exact effect
                depends on comment type. Either the tag entire will not exist
                or overwritten with None/Null/"". Defaults to False.
        """
        raise NotImplementedError

    def check_file_path(self):
        file_path = self.file_path
        if self.file_path != self._file.filename:
            self._file.filename = file_path
            logging.warning("File paths do not match!")
            return False
        return True
