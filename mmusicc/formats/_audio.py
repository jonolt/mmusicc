# from ._constants import PATH
# from ._util import hash_filename
from mmusicc.util.allocationmap import get_dictionaries


class AudioFile:

    # TODO put in config file
    chars_split = ['|', '\n']
    char_join = ['|']  # only for mp3 an when flac join is true
    class_initialized = False

    @classmethod
    def init_class(cls):
        dicts = get_dictionaries()
        cls.dict_config = dicts.get("dict_config")
        # list_tags_sorted can contain none, while list_tags should not
        # cls.list_tags_sorted = dicts.get("list_tags_sorted")
        cls.list_tags = dicts.get("list_tags")
        cls.dict_tags_id3 = dicts.get("dict_tags_id3")
        cls.dict_id3_tags = dicts.get("dict_id3_tags")
        cls.dict_tags_str = dicts.get("dict_tags_str")
        # cls.dict_auto_fill_rules = dicts.get("dict_auto_fill_rules")
        # cls.dict_test_read = dicts.get("dict_test_read")
        cls.class_initialized = True

    def __init__(self, file_path):
        if not AudioFile.class_initialized:
            AudioFile.init_class()
        self.set_file_path(file_path)
        self.dict_meta = dict()
        self.unprocessed_tag = dict()

    @property
    def file_path(self):
        return "fuu"

    def set_file_path(self, path):
        pass
    #    fn_hash = hash_filename(path)
    #    for key in hash_filename(path):
    #        self.__setattr__(key, fn_hash[key])

    def file_read(self):
        raise NotImplementedError

    def file_save(self):
        raise NotImplementedError

    def import_tag(self):
        """Import tag from other audio file"""
        pass

    def set_tag(self, tag, value):
        pass

    def get_image(self):
        pass

    def set_image(self):
        pass

    def text_parser_get(self, text):
        if isinstance(text, list):
            tmp_text = list()
            for t in text:
                tmp_text.append(self.text_parser_get(t))
            return tmp_text
        elif isinstance(text, str):
            for c in AudioFile.chars_split:
                tmp_text = text.split()
                if len(tmp_text) > 0:
                    text = tmp_text
                    break
            return text
        else:
            raise ValueError("text wrong value")
