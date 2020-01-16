from mmusicc.formats._constants import *
from mmusicc.util.path import hash_filename


class AudioFile:

    # TODO put in config file
    chars_split = ['|', '\n']
    char_join = ['|']  # only for mp3 an when flac join is true

    def __init__(self, file_path):
        self.set_file_path(file_path)
        self.dict_meta = dict()
        self.unprocessed_tag = dict()

    @property
    def file_path(self):
        return getattr(self, PATH)

    def set_file_path(self, path):
        tmp_fn_hash = hash_filename(path)
        for key in hash_filename(path):
            setattr(self, key, tmp_fn_hash[key])

    def file_read(self):
        raise NotImplementedError

    def file_save(self):
        raise NotImplementedError

    def import_tag(self):
        """Import tag from other audio file"""
        pass
