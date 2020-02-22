import logging
import mimetypes
import os
import re

import mmusicc.util.allocationmap as am
from mmusicc.database import MetaDB
from mmusicc.formats import MusicFile
from mmusicc.util.path import PATH, hash_filename


# TODO move filepath to Metadata


class MetadataDict(dict):

    def __init__(self, init_value=None):
        super().__init__()
        self._init_value = init_value
        for key in am.list_tags:
            self[key] = init_value

    def reset(self):
        for key in list(self):
            self[key] = self._init_value


class Metadata:

    dry_run = False
    path_config_yaml = "config.yaml"
    write_empty = True

    _database = None

    def __init__(self, file, read_tag=True):
        """
        file can be None, this is tu support album Metadata

        """

        if not am.list_tags:
            am.init_allocationmap(Metadata.path_config_yaml)

        self._audio = None

        self.dict_data = MetadataDict()

        if not file:
            pass
        elif os.path.exists(file):
            self.link_audio_file(file)
        else:
            raise FileNotFoundError("Error File does not exist")

        if file and read_tag:
            self.read_tags()

        self.dict_auto_fill_org = None

    @property
    def database_linked(self):
        return Metadata._database_linked()

    @classmethod
    def _database_linked(cls):
        if cls._database:
            return True
        return False

    @classmethod
    def link_database(cls, file_path):
        if not cls._database:
            cls._database = MetaDB(file_path)
        else:
            raise Exception("Database already linked")

    @classmethod
    def unlink_database(cls):
        if cls._database:
            cls._database = None
        else:
            raise Exception("No Database linked")

    @property
    def file_path(self):
        return getattr(self, PATH)

    def set_file_path(self, path):
        tmp_fn_hash = hash_filename(path)
        for key in hash_filename(path):
            setattr(self, key, tmp_fn_hash[key])

    @property
    def file_path_set(self):
        if self.file_path:
            return True
        return False

    @property
    def audio_file_linked(self):
        if self._audio:
            return True
        return False

    def link_audio_file(self, file_path):
        self.set_file_path(file_path)
        self._audio = MusicFile(file_path)

    def read_tags(self, remove_other=False):
        if not self._audio:
            raise Exception("no file linked")
        self._audio.file_read()
        if remove_other:
            self.dict_data.reset()
        self.dict_data.update(self._audio.dict_meta)

    def write_tags(self, remove_other=True):
        if not self._audio:
            raise Exception("no file linked")
        if remove_other:
            self._audio.dict_meta = dict()
        self._audio.dict_meta.update(self.dict_data)
        self._audio.file_save(remove_existing=remove_other)

    def import_tags(self, source_meta, whitelist=None, blacklist=None,
                    remove_other=False):
        """import metadata from source meta object"""
        tags = Metadata.process_white_and_blacklist(whitelist, blacklist)
        for tag in am.list_tags:
            if tag in tags:
                self.dict_data[tag] = source_meta.dict_data[tag]
            else:
                if remove_other:
                    self.dict_data[tag] = None

    def load_tags_db(self, primary_key=None, whitelist=None, blacklist=None,
                     remove_other=False):
        if not primary_key:
            if self.file_path_set:
                primary_key = self.file_path
        tags = Metadata.process_white_and_blacklist(whitelist, blacklist)
        if not Metadata._database:
            raise Exception("no database linked")
        else:
            if remove_other:
                self.dict_data.reset()
            self.dict_data.update(self._database.read_meta(primary_key, tags))

    def save_tags_db(self):
        if not Metadata._database:
            raise Exception("no database linked")
        if self.file_path_set:
            self._database.insert_meta(self.dict_data, self.file_path)
        else:
            pass

    def auto_fill_tags(self):
        if not self.dict_auto_fill_org:
            self.dict_auto_fill_org = MetadataDict(init_value=False)
        for tag in list(am.dict_auto_fill_rules):
            rule = am.dict_auto_fill_rules.get(tag)
            val_test = self.dict_data.get(rule[0])
            val_regex = rule[1]
            try:
                val_parse = self.dict_data.get(rule[2])
            except KeyError:
                val_parse = rule[2]
            if val_regex is None:
                if isinstance(val_test, Empty):
                    self.dict_auto_fill_org[tag] = self.dict_data[tag]
                    self.dict_data[tag] = val_parse
            elif isinstance(val_regex, str):
                if not isinstance(val_test, str):
                    val_test = str(val_test)
                m = re.search(val_regex, val_test)
                if m:
                    self.dict_auto_fill_org[tag] = self.dict_data[tag]
                    self.dict_data[tag] = eval(val_parse)

    @staticmethod
    def process_white_and_blacklist(whitelist, blacklist):
        if not whitelist:
            whitelist = am.list_tags
        if blacklist:
            for t in blacklist:
                try:
                    whitelist.pop(whitelist.index(t))
                except ValueError:
                    logging.warning("warning {} not in whitelist".format(t))
                    continue
        return whitelist

    @staticmethod
    def check_is_audio(file):
        mimetype = mimetypes.guess_type(file)
        if mimetype[0] and "audio" in mimetype[0]:
            return True
        else:
            return False


class GroupMetadata(Metadata):

    def __init__(self, list_metadata):
        super().__init__(None)
        self.list_metadata = list_metadata
        self.read_tags()

        self.dict_auto_fill_org = None

    def auto_fill_tags(self):
        if not self.dict_auto_fill_org:
            self.dict_auto_fill_org = MetadataDict(init_value=False)
        for metadata in self.list_metadata:
            metadata.auto_fill_tags()
        self.__compare_tags()

    def read_tags(self, remove_other=False):
        for metadata in self.list_metadata:
            metadata.read_tags(remove_other=remove_other)
        self.__compare_tags()

    def __compare_tags(self):
        for key in am.list_tags:
            first = True
            for metadata in self.list_metadata:
                data = metadata.dict_data.get(key)
                if first:
                    self.dict_data[key] = data
                    first = False
                else:
                    if self.dict_data[key] == data:
                        pass
                    else:
                        self.dict_data[key] = Div(key, self.list_metadata)
                        break

    def write_tags(self, remove_other=True):
        for metadata in self.list_metadata:
            metadata.write_tags(remove_other=remove_other)

    def import_tags(self, source_meta, whitelist=None, blacklist=None,
                    remove_other=False):

        # tags = Metadata.process_white_and_blacklist(whitelist, blacklist)

        for metadata_self in self.list_metadata:
            for metadata_source in source_meta.list_metadata:
                if metadata_self.file_name == metadata_source.file_name:
                    metadata_self.import_tags(
                        metadata_source,
                        whitelist=whitelist,
                        blacklist=blacklist,
                        remove_other=remove_other)

    def load_tags_db(self, primary_key=None, whitelist=None, blacklist=None,
                     remove_other=False):
        for metadata in self.list_metadata:
            metadata.load_tags_db(primary_key=primary_key,
                                  whitelist=whitelist,
                                  blacklist=blacklist,
                                  remove_other=remove_other)

    def save_tags_db(self):
        for metadata in self.list_metadata:
            metadata.save_tags_db()


class AlbumMetadata(GroupMetadata):

    def __init__(self, path_album):
        list_metadata = list()
        for file in os.listdir(path_album):
            Metadata.check_is_audio(file)
            if Metadata.check_is_audio(file):
                file_path = os.path.join(path_album, file)
                list_metadata.append(Metadata(file_path))
        super().__init__(list_metadata)


class Empty(object):
    value = ""

    def __repr__(self):
        return "<none>"

    def __eq__(self, other):
        if isinstance(other, Empty):
            return True
        else:
            return False

    @staticmethod
    def is_empty(text):
        if text is None or isinstance(text, Empty):
            if isinstance(text, str) and text.strip() == "":
                return True
        return False


class Div(object):

    def __init__(self, key=None, list_metadata=None):
        self._dict_values = dict()
        self._diff = None
        self._key_tag = None  # maybe not needed
        if key and list_metadata:
            self.add_metadata(key, list_metadata)

    def __repr__(self):
        return "<div>"

    def __eq__(self, other):
        if not isinstance(other, Div):
            return False
        equal = None
        for meta_a in list(self._dict_values):
            for meta_b in list(other._dict_values):
                if meta_a.file_name == meta_b.file_name:
                    if not (self._dict_values.get(meta_a)
                            == other._dict_values.get(meta_b)):
                        equal = False
        if equal is None:
            equal = False
        return equal

    def add_metadata(self, key_tag, list_metadata):
        self._key_tag = key_tag
        for metadata in list_metadata:
            self.add_value(metadata, metadata.dict_data.get(self._key_tag))

    def add_value(self, obj, val):
        self._dict_values[obj] = val
