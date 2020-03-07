import logging
import os
import re

import mmusicc.util.allocationmap as am
from mmusicc.database import MetaDB
from mmusicc.formats import MusicFile
from mmusicc.util.misc import check_is_audio, process_white_and_blacklist
from mmusicc.util.path import PATH, hash_filename


class MetadataDict(dict):
    """Dictionary containing tags as keys, values can be reset.

    Args:
        init_value (object, optional): initial value of all values,
            defaults to None.
    """

    def __init__(self, init_value=None):
        super().__init__()
        self._init_value = init_value
        for key in am.list_tags:
            self[key] = init_value

    def reset(self):
        for key in list(self):
            self[key] = self._init_value


class MetadataMeta(type):

    # def __init__(cls, *args, **kwargs):
    def __init__(cls, name, bases, nmspc):
        super(MetadataMeta, cls).__init__(name, bases, nmspc)
        cls._dry_run = False
        cls._database = None
        # cls._delete_existing = False

    @property
    def dry_run(cls):
        return cls._dry_run

    @dry_run.setter
    def dry_run(cls, value):
        cls._dry_run = value
        if cls._dry_run:
            logging.log(25, "Running in Dry Run mode. "
                            "No data will be written.")

    @property
    def is_linked_database(cls):
        if cls._database:
            return True
        return False

    def link_database(cls, file_path):
        if not cls._database:
            cls._database = MetaDB(file_path)
        else:
            raise Exception("Database already linked")

    def unlink_database(cls):
        if cls._database:
            cls._database = None
        else:
            raise Exception("No Database linked")

    # prep for future class property
    # @property
    # def delete_existing(cls):
    #     return cls._delete_existing
    #
    # @delete_existing.setter
    # def delete_existing(cls, value):
    #     cls._delete_existing = value
    #     if cls._dry_run:
    #         logging.log(25, "Existing Metadata will be deleted!")


class Metadata(metaclass=MetadataMeta):
    """Class containing Metadata Information,

    either from a linked file or loaded from a database.

    Args:
        file_path  (str, optional): path to an supported audio file, can be set
            later with 'link_audio_file()' too. Defaults to None.
        read tags (bool, optional): enables automatic reading of metadata from
            file. Defaults to True.
    """

    write_empty = True

    _database = None

    def __init__(self, file_path=None, read_tag=True):

        if not am.list_tags:
            raise Exception("MmusicC not initialized! Please Initialize first")

        self._audio = None

        self.dict_data = MetadataDict()

        if not file_path:
            pass
        elif os.path.exists(file_path):
            self.link_audio_file(file_path)
        else:
            raise FileNotFoundError("Error File does not exist")

        if file_path and read_tag:
            self.read_tags()

        self.dict_auto_fill_org = None

    @property
    def file_path(self):
        return getattr(self, PATH)

    def _set_file_path(self, path):
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
        self._set_file_path(file_path)
        self._audio = MusicFile(file_path)

    def read_tags(self, remove_other=False):
        """read metadata from linked audio file

        Args:
            remove_other (bool, optional): If False, overwrites only new tag
            values read from the file and lets others unchanged. If True,
            resets dictionary to initial state, which removes already exiting
            tag values. Defaults to False.
        Raises:
            Exception: if no file is linked
        """
        if not self._audio:
            raise Exception("no file_path linked")
        self._audio.file_read()
        if remove_other:
            self.dict_data.reset()
        self.dict_data.update(self._audio.dict_meta)

    def write_tags(self, remove_other=False):
        """write metadata to linked audio file

        Args:
            remove_other (bool, optional): If False, overwrites only new
            tag values writen the file and lets others unchanged. If True,
            clears all metadata from file before writing. Defaults to False.
        Raises:
            Exception: if no file is linked
        """
        if not self._audio:
            raise Exception("no file_path linked")
        if remove_other:
            self._audio.dict_meta = dict()
        self._audio.dict_meta.update(self.dict_data)
        self._audio.file_save(remove_existing=remove_other)

    def import_tags(self, source_meta, whitelist=None, blacklist=None,
                    remove_other=False):
        """Imports metadata from another Metadata object.

        Args:
            source_meta          (Metadata): Metadata object containing the
                tags to be imported.
            whitelist (list<str>, optional): whitelist of tags to be imported.
                If None, loads all tags (except blacklisted). Defaults to None.
            blacklist (list<str>, optional): blacklist of tags not to be
                imported. Applied after whitelist. If None, no tags are
                blacklisted. Defaults to None.
            remove_other   (bool, optional): If False, overwrites only new
                tag values and lets others unchanged. If True, deletes all
                other tag values, which are not imported. Defaults to False.
        """
        tags = process_white_and_blacklist(whitelist, blacklist)
        for tag in am.list_tags:
            if tag in tags:
                self.dict_data[tag] = source_meta.dict_data[tag]
            else:
                if remove_other:
                    self.dict_data[tag] = None

    def import_tags_from_db(self,
                            primary_key=None,
                            whitelist=None,
                            blacklist=None,
                            remove_other=False,):
        """Imports metadata from the database.

        Args:
            primary_key         (str, None): unique identifier of the item
                which data has to be loaded (eg. Filepath).
            whitelist (list<str>, optional): whitelist of tags to be imported.
                If None, loads all tags (except blacklisted). Defaults to None.
            blacklist (list<str>, optional): blacklist of tags not to be
                imported. Applied after whitelist. If None, no tags are
                blacklisted. Defaults to None.
            remove_other   (bool, optional): If False, overwrites only new
                tag values and lets others unchanged. If True, deletes all
                other tag values, which are not imported. Defaults to False.

            Raises:
             Exception: if no database linked to class
            """

        if not primary_key:
            if self.file_path_set:
                keys = self._database.get_list_of_primary_keys()
                key_str, ext = os.path.splitext(self.file_path)
                subs = None
                # tries to get a unique match beginning at leave
                while len(keys) > 1:
                    key_str, sub = os.path.split(key_str)
                    if subs:
                        subs = os.path.join(sub, subs)
                    else:
                        subs = sub
                    keys = [path for path in keys if subs in path]
                    # for path in keys:
                    #     if subs not in path:
                    #         keys.remove(path)
                if len(keys) == 0:
                    raise KeyError("could not find matching entry")
                primary_key = keys[0]

        tags = process_white_and_blacklist(whitelist, blacklist)
        if not Metadata._database:
            raise Exception("no database linked")
        else:
            if remove_other:
                self.dict_data.reset()
            data = self._database.read_meta(primary_key, tags)
            if data:
                self.dict_data.update(data)
            else:
                logging.warning("database read failed, no data imported. "
                                "File might not be in database")

    def export_tags_to_db(self, root_dir=None):
        """saves all tags to database.

         This is the secure way. Data not wanted does not have to be loaded,
         but all data can still be accessed in case it is needed again.

         Raises:
             Exception: if no database linked to class
         """
        if not Metadata._database:
            raise Exception("no database linked")
        if self.file_path_set:
            self._database.insert_meta(self.dict_data, self.file_path)
        else:
            pass

    def auto_fill_tags(self):
        """Automatic fill/autocomplete tags with in config file defined rules.

        This future is intended to fix small consistency errors in metadata,
        like missing album artists or leading 0 before a single digit
        tracknumber.
        """
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


class GroupMetadata(Metadata):
    """Class holding one ore many Metadata Objects. Subclasses Metadata and

    overwrites Metadata functions so that you don't have to care if you have a
    File or a Folder (like an album). Tags in dict are a summary of the tags of
    the contained metadata. If all values of a tag are identical the value is
    used, otherwise a Div object is created which indicates different values
    (and also got a list of all the differences).

    Args:
        list_metadata (list<Metadata> or list<str>): list of Metadata objects
            or file paths.
    """

    def __init__(self, list_metadata):
        super().__init__(None)
        if isinstance(list_metadata[0], Metadata):
            self.list_metadata = list_metadata
        else:
            self.list_metadata = list()
            for file_path in list_metadata:
                if check_is_audio(file_path):
                    self.list_metadata.append(Metadata(file_path))
                else:
                    logging.warning("File '{}' is no audio file"
                                    .format(file_path))
        self.read_tags()

        self.dict_auto_fill_org = None

    def auto_fill_tags(self):
        """Super-Method applied to all Objects in list. See Metadata."""
        if not self.dict_auto_fill_org:
            self.dict_auto_fill_org = MetadataDict(init_value=False)
        for metadata in self.list_metadata:
            metadata.auto_fill_tags()
        self.__compare_tags()

    def read_tags(self, remove_other=False):
        """See super function"""
        for metadata in self.list_metadata:
            metadata.read_tags(remove_other=remove_other)
        self.__compare_tags()

    def __compare_tags(self):
        """compares tag values of all objects in list and creates a Div object,
        which indicates different values (and also got a list of all the
        differences).
        """
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
        """Super-Method applied to all Objects in list. See Metadata."""
        for metadata in self.list_metadata:
            metadata.write_tags(remove_other=remove_other)

    def import_tags(self, source_meta, whitelist=None, blacklist=None,
                    remove_other=False):
        """Super-Method applied to all Objects in list. See Metadata.

        Args:
            source_meta (GroupMetadata): group metadata object.
            whitelist (list<str>, optional): See Metadata.import_tags().
            blacklist (list<str>, optional): See Metadata.import_tags().
            remove_other   (bool, optional): See Metadata.import_tags().
        """
        # tags = Metadata.process_white_and_blacklist(whitelist, blacklist)

        for metadata_self in self.list_metadata:
            for metadata_source in source_meta.list_metadata:
                # noinspection PyUnresolvedReferences
                if metadata_self.file_path == metadata_source.file_path:
                    metadata_self.import_tags(
                        metadata_source,
                        whitelist=whitelist,
                        blacklist=blacklist,
                        remove_other=remove_other)

    def import_tags_from_db(self,
                            whitelist=None,
                            blacklist=None,
                            remove_other=False,
                            root_dir=None):
        """Super-Method applied to all Objects in list. See Metadata."""
        for metadata in self.list_metadata:
            metadata.import_tags_from_db(primary_key=None,
                                         whitelist=whitelist,
                                         blacklist=blacklist,
                                         remove_other=remove_other)

    def export_tags_to_db(self, root_dir=None):
        """Super-Method applied to all Objects in list. See Metadata."""
        for metadata in self.list_metadata:
            metadata.export_tags_to_db()


class AlbumMetadata(GroupMetadata):
    """Special case of GroupMetadata where Metadata list is created from a
    Folder/Album path. Skips non audio files.

    Args:
        path_album: filepath of album or folder to be accessed as group.
    """

    def __init__(self, path_album):
        list_metadata = list()
        for file in os.listdir(path_album):
            file_path = os.path.join(path_album, file)
            if check_is_audio(file_path):
                list_metadata.append(file_path)
        super().__init__(list_metadata)


class Empty(object):
    """object representing a tag without an value.

    It is a placeholder to be able to change the character/object which
    represents the Emptiness in the Database or at mutagen.
    """

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
    """
    Object Representing a group different values. Provides rich comparison.

    Still Under Construction.

    Args:
        key                      (str, optional): dictionary key which values
            to represent
        list_metadata (list<Metadata>, optional): list of Metadata object
            containing the values.
    """

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
