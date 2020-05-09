#  Copyright (c) 2020 Johannes Nolte
#  SPDX-License-Identifier: GPL-3.0-or-later

import logging
import os
import pathlib
import re

import mmusicc.util.allocationmap as am
from mmusicc.database import MetaDB
from mmusicc.formats import MusicFile
from mmusicc.util.metadatadict import MetadataDict, Empty, Div
from mmusicc.util.misc import (
    is_supported_audio,
    process_white_and_blacklist,
    get_the_right_one,
)


class MetadataMeta(type):
    """Meta Object for Metadata class."""

    def __init__(cls, name, bases, nmspc):
        super(MetadataMeta, cls).__init__(name, bases, nmspc)
        cls._dry_run = False
        cls._database = None
        # cls._delete_existing = False

    @property
    def dry_run(cls):
        """bool: Get or set. If True do everything as usual, but without
        writing data.
        """
        if cls._dry_run:
            logging.log(25, "Running in Dry Run mode. " "No data will be written.")
        return cls._dry_run

    @dry_run.setter
    def dry_run(cls, value):
        cls._dry_run = value

    @property
    def is_linked_database(cls):
        """bool: Get True if a database is linked to class."""
        if cls._database:
            return True
        return False

    def link_database(cls, database_url):
        """Link a database to class.

        Args:
            database_url (str): database url following RFC-1738*. If the sting,
                does not contain '://', a filepath for a sqlite database is
                assumed.

        Raises:
            Exception: if a database is already linked
        """
        if not cls._database:
            cls._database = MetaDB(database_url)
        else:
            raise Exception("Database already linked")

    def unlink_database(cls):
        """Unlink the database from the class.

        Raises:
            Exception: if no database is linked
        """
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
        file_path (str or pathlib.Path, optional): path to an supported audio
            file, can be set later with 'link_audio_file()' too. Defaults to
            None.
        read_tag (bool, optional): enables automatic reading of metadata from
            file at class initialisation. Defaults to True.
    """

    def __init__(self, file_path=None, read_tag=True):

        if not am.list_tags:
            raise Exception("mmusicc not initialized! Please Initialize first")

        self._audio = None

        self._dict_data = MetadataDict()

        if file_path:
            self.link_audio_file(file_path)

            if read_tag:
                self.read_tags()

        self.dict_auto_fill_org = None

    @property
    def file_path(self):
        """pathlib.Path: Get file path of linked audio file."""
        if self._audio:
            return self._audio.file_path
        return None

    @property
    def audio_file_linked(self):
        """bool: Get True if a audio file is linked to instance."""
        if self._audio:
            return True
        return False

    def link_audio_file(self, file_path):
        """Links audio file with given path to instance.

        Args:
            file_path (str or pathlib.Path): file path of audio file.

        Raises:
            FileNotFoundError: if file does not exist.
        """
        file_path = pathlib.Path(file_path)
        if file_path.exists():
            self._audio = MusicFile(file_path)
        else:
            raise FileNotFoundError("Error Audio File does not exist")

    @property
    def unprocessed_tag(self):
        """pathlib.Path: Get file path of linked audio file."""
        if self._audio:
            return self._audio.unprocessed_tag
        return None

    @property
    def dict_data(self):
        """MetadataDict: Get the dict containing tags"""
        return self._dict_data

    def get_tag(self, str_tag_key):
        """Get value of given str_tag_key"""
        return self._dict_data.get(str_tag_key)

    def set_tag(self, str_tag_key, value):
        """Set value of tag with given str_tag_key"""
        self._dict_data[str_tag_key] = value

    def read_tags(self):
        """Read metadata from linked audio file into dict meta.

        Raises:
            Exception: if no file is linked
        """
        if not self._audio:
            raise Exception("no file_path linked")
        self._audio.file_read()
        self._dict_data.update(self._audio.dict_meta)

    def write_tags(self, remove_existing=False, write_empty=False):
        """write metadata to linked audio file

        Args:
            remove_existing (bool, optional): If true clear all tags on file
                before writing. Defaults to False.
            write_empty (bool): if true write empty tags, exact effect
                depends on comment type. Either the tag entries will not exist
                or overwritten with None/Null/"". Defaults to False.
        Raises:
            Exception: if no file is linked
        """
        if not self._audio:
            raise Exception("no file_path linked")
        self._audio.dict_meta.update(self._dict_data)
        if not Metadata.dry_run:
            self._audio.file_save(
                remove_existing=remove_existing, write_empty=write_empty
            )

    def import_tags(self, source_meta, whitelist=None, blacklist=None, skip_none=True):
        """Imports metadata from another Metadata object.

        Args:
            source_meta (Metadata): Metadata object containing the
                tags to be imported.
            whitelist (list of str, optional): whitelist of tags to be
                imported. If None, loads all tags (except blacklisted).
                Defaults to None.
            blacklist (list of str, optional): blacklist of tags not to be
                imported. Applied after whitelist. If None, no tags are
                blacklisted. Defaults to None.
            skip_none (bool, optional): If True, don't overwrite values in
                target, which are None in source. Defaults to True.
        """
        self._import_tags(source_meta._dict_data, whitelist, blacklist, skip_none)

    def _import_tags(self, dict_meta, whitelist, blacklist, skip_none):
        tags = process_white_and_blacklist(whitelist, blacklist)
        for tag in am.list_tags:
            if tag in tags:
                val = dict_meta[tag]
                if not val and skip_none:
                    continue
                self._dict_data[tag] = val

    def import_tags_from_db(
        self, primary_key=None, whitelist=None, blacklist=None, skip_none=True
    ):
        """Imports metadata from the database.

        Args:
            primary_key (str, None): unique identifier of the item
                which data has to be loaded. The save function only uses the
                absolute filepath atm. If value is None, a algorithm takes the
                path of the linked file works and works itself backward
                (beginning at the leave) in the key list of the DB until only
                one key is left, which is used. In other words, its acts like
                the keys are relative file path (with unknown working
                directory). Defaults to None.
            whitelist (list of str, optional): whitelist of tags to be
                imported. If None, loads all tags (except blacklisted).
                Defaults to None.
            blacklist (list of str, optional): blacklist of tags not to be
                imported. Applied after whitelist. If None, no tags are
                blacklisted. Defaults to None.
            skip_none (bool, optional): If True, don't overwrite values in
                target, which are None in source. Defaults to True.

            Raises:
             Exception: if no database linked to class

            """

        if not primary_key and self.file_path:
            keys = self._database.get_list_of_primary_keys()
            primary_key = get_the_right_one(keys, self.file_path)

        if not self._database:
            raise Exception("no database linked")
        else:
            data = self._database.read_meta(str(primary_key))
            if data:
                self._import_tags(data, whitelist, blacklist, skip_none)
            else:
                logging.warning(
                    "database read failed, no data imported. "
                    "File might not be in database"
                )

    def export_tags_to_db(self, root_dir=None):
        """Saves all tags to database.

         This is the secure way. Data not wanted does not have to be loaded,
         but all data can still be accessed in case it is needed again.

         Raises:
             Exception: if no database linked to class
         """
        if not self._database:
            raise Exception("no database linked")
        if self.file_path:
            if not self._dry_run:
                primary_key = str(self.file_path)
                self._database.insert_meta(self._dict_data, primary_key)
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
            val_test = self._dict_data.get(rule[0])
            val_regex = rule[1]
            try:
                val_parse = self._dict_data.get(rule[2])
            except KeyError:
                val_parse = rule[2]
            if val_regex is None:
                if isinstance(val_test, Empty):
                    self.dict_auto_fill_org[tag] = self._dict_data[tag]
                    self._dict_data[tag] = val_parse
            elif isinstance(val_regex, str):
                if not isinstance(val_test, str):
                    val_test = str(val_test)
                m = re.search(val_regex, val_test)
                if m:
                    self.dict_auto_fill_org[tag] = self._dict_data[tag]
                    self._dict_data[tag] = eval(val_parse)


class GroupMetadata(Metadata):
    """Class holding one ore many Metadata Objects. Subclasses Metadata and

    overwrites Metadata functions so that you don't have to care if you have
    one file or a list of files like an album. Tags in dict are a summary of
    the tags of individual values of the contained metadata. If all values of a
    tag are identical the value is in dict as it is, otherwise a Div object is
    created managing different values.

    Args:
        list_metadata (list of Metadata or list of str or list of pathlib.Path):
            list of Metadata objects or file paths.

    Note:
        Not all properties and functions of Metadata are supported (like
        file_path, obviously). Stick with the documented ones.
    """

    def __init__(self, list_metadata):
        super().__init__(None)
        if isinstance(list_metadata[0], Metadata):
            self.list_metadata = list_metadata
        else:
            self.list_metadata = list()
            for file_path in list_metadata:
                if is_supported_audio(file_path):
                    self.list_metadata.append(Metadata(file_path))
                else:
                    logging.warning("File '{}' is no audio file".format(file_path))
        self.read_tags()

        self.dict_auto_fill_org = None

    def get_tag(self, str_tag_key):
        """Super-Method applied to all Objects in list. See Metadata."""
        return self._dict_data.get(str_tag_key)

    def set_tag(self, str_tag_key, value):
        """Super-Method applied to all Objects in list. See Metadata."""
        for metadata in self.list_metadata:
            metadata._dict_data[str_tag_key] = value
        self.__compare_tags()

    def reset_meta(self):
        for metadata in self.list_metadata:
            metadata._dict_data.reset()

    def auto_fill_tags(self):
        """Super-Method applied to all Objects in list. See Metadata."""
        if not self.dict_auto_fill_org:
            self.dict_auto_fill_org = MetadataDict(init_value=False)
        for metadata in self.list_metadata:
            metadata.auto_fill_tags()
        self.__compare_tags()

    def read_tags(self):
        """Super-Method applied to all Objects in list. See Metadata."""
        for metadata in self.list_metadata:
            metadata.read_tags()
        self.__compare_tags()

    def __compare_tags(self):
        """compares tag values of all objects in list and creates a Div object,
        which indicates different values (and also got a list of all the
        differences).
        """
        for key in am.list_tags:
            first = True
            for metadata in self.list_metadata:
                data = metadata._dict_data.get(key)
                if first:
                    self._dict_data[key] = data
                    first = False
                else:
                    if self._dict_data[key] == data:
                        pass
                    else:
                        self._dict_data[key] = Div(key, self.list_metadata)
                        break

    def write_tags(self, remove_existing=False, write_empty=False):
        """Super-Method applied to all Objects in list. See Metadata."""
        for metadata in self.list_metadata:
            metadata.write_tags(
                remove_existing=remove_existing, write_empty=write_empty
            )

    def import_tags(self, source_meta, whitelist=None, blacklist=None, skip_none=True):
        """Super-Method applied to all Objects in list. See Metadata.

        Args:
            source_meta     (GroupMetadata): group metadata object.
            whitelist (list<str>, optional): See Metadata.import_tags().
            blacklist (list<str>, optional): See Metadata.import_tags().
            skip_none      (bool, optional): See Metadata.import_tags().
        """
        paths = dict()
        for sm in source_meta.list_metadata:
            paths[sm.file_path] = sm
        path_keys = list(paths.keys())

        for metadata_self in self.list_metadata:
            key = get_the_right_one(path_keys, metadata_self.file_path)
            metadata_source = paths.get(key)
            metadata_self.import_tags(
                metadata_source,
                whitelist=whitelist,
                blacklist=blacklist,
                skip_none=skip_none,
            )
        self.__compare_tags()

    def import_tags_from_db(
        self, whitelist=None, blacklist=None, root_dir=None, skip_none=True
    ):
        """Super-Method applied to all Objects in list. See Metadata."""
        for metadata in self.list_metadata:
            metadata.import_tags_from_db(
                primary_key=None,
                whitelist=whitelist,
                blacklist=blacklist,
                skip_none=skip_none,
            )
        self.__compare_tags()

    def export_tags_to_db(self, root_dir=None):
        """Super-Method applied to all Objects in list. See Metadata."""
        for metadata in self.list_metadata:
            metadata.export_tags_to_db()

    @property
    def audio_file_linked(self):
        """Do not use this property. Only applies to Metadata."""
        raise NotImplementedError()

    @property
    def unprocessed_tag(self):
        """Super-Method applied to all Objects in list. See Metadata."""
        unprocessed_tags = dict()
        for metadata in self.list_metadata:
            if metadata._audio:
                unprocessed_tags.update(self._audio.unprocessed_tag)
        return unprocessed_tags

    @property
    def file_path(self):
        """Do not use this property. Only applies to Metadata."""
        raise NotImplementedError()

    def link_audio_file(self, file_path):
        """Do not use this property. Only applies to Metadata."""
        raise NotImplementedError()


class AlbumMetadata(GroupMetadata):
    """Special case of GroupMetadata where Metadata list is created from a
    Folder/Album path. Skips non audio files.

    Args:
        path_album: filepath of album or folder to be accessed as group.
    """

    def __init__(self, path_album):
        path_album = pathlib.Path(path_album)
        list_metadata = list()
        for file in os.listdir(path_album):
            file_path = path_album.joinpath(file)
            if is_supported_audio(file_path):
                list_metadata.append(file_path)
        super().__init__(list_metadata)
