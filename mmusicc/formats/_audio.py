import logging

from mmusicc.formats._constants import *
from mmusicc.util.path import hash_filename


class AudioFile:

    def __init__(self, file_path):
        self.set_file_path(file_path)
        self.dict_meta = dict()
        self.unprocessed_tag = dict()
        self._file = None

    @property
    def file_path(self):
        return getattr(self, PATH)

    def set_file_path(self, path):
        tmp_fn_hash = hash_filename(path)
        for key in hash_filename(path):
            setattr(self, key, tmp_fn_hash[key])

    def file_read(self):
        raise NotImplementedError

    def file_save(self, remove_existing=False):
        raise NotImplementedError

    def check_file_path(self):
        file_path = self.file_path
        if self.file_path != self._file.filename:
            self._file.filename = file_path
            logging.warning("File paths do not match!")
            return False
        return True
