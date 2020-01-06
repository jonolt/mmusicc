#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Dec 23 12:30:45 2019

@author: johannes


"""
import os
import enum

import mutagen
import sqlalchemy
import yaml
from mutagen.flac import FLAC
from mutagen.id3 import ID3
from sqlalchemy import Column, String, Integer
from sqlalchemy import orm
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import text

from mmusicc.tui import Tui
from mmusicc import tui
from mmusicc.metadata import Metadata, AlbumMetadata, Div


class MusicManager:

    # TODO add option if album will be handeld as albnom or each single file

    suported_files = [".mp3", ".flac"]

    def __init__(self):
        self._session = None
        self._source_path = None
        self._source_type = None
        self._source = None
        self._target_path = None
        self._target_type = None
        self._target = None
        self.dict_overwrite = OverwriteDict()
        self.dict_diff = MetadataDict()

    @property
    def dict_meta_source(self):
        return self.source[0].dict_data

    @property
    def dict_meta_target(self):
        return self.target[0].dict_data

    @property
    def source_path(self):
        return self._source_path

    @source_path.setter
    def source_path(self, path):
        if not path:
            self._source_path = None
            self._source_type = None
            self._source = None
            self.dict_diff.reset()
            return
        self._source_path = path
        self._source_type = self.get_object_type(path)
        if self._source_type:
            self.fetch_source()
            self.update_dict_diff()
        else:
            print("path not valid: {}".format(path))

    @property
    def source(self):
        # TODO formatting of different types
        return self._source

    @property
    def target_path(self):
        return self._target_path

    @target_path.setter
    def target_path(self, path):
        if not path:
            self._target_path = None
            self._target_type = None
            self._target = None
            self.dict_diff.reset()
            return
        self._target_path = path
        self._target_type = self.get_object_type(path)
        if self._target_type:
            self.fetch_target()
            self.update_dict_diff()
        else:
            print("path not valid: {}".format(path))

    @property
    def target(self):
        # TODO formatting of different types
        return self._target

    def update_dict_diff(self):
        if self.source and self.target:
            self.__update_dict_diff_and_over()
        return

    def __update_dict_diff_and_over(self):
        self.dict_overwrite.reset()
        for tag in Metadata.list_tags:
            meta_s = self.dict_meta_source.get(tag)
            meta_t = self.dict_meta_target.get(tag)
            if meta_s == meta_t:
                self.dict_diff[tag] = DiffType.unchanged
            elif not meta_t:
                self.dict_diff[tag] = DiffType.new
            elif not meta_s:
                self.dict_diff[tag] = DiffType.deleted
            else:
                self.dict_diff[tag] = DiffType.overwrite
            if isinstance(meta_t, Div) and isinstance(meta_s, Div):
                self.dict_overwrite[tag] = False

    def get_object_type(self, path):
        path = os.path.expanduser(path)
        media_type = None
        if os.path.isfile(path):
            ext = os.path.splitext(path)[1]
            if ext == ".db3":
                media_type = MediaType.database
                self._session = MusicManager.create_session(path)
            elif os.path.exists(path):
                if ext in MusicManager.suported_files:
                    media_type = MediaType.file
        elif os.path.isdir(path):
            if os.path.exists(path):
                gen = os.walk(path, topdown=True)
                (dirpath, dirnames, filenames) = next(gen)
                if dirnames and filenames:
                    media_type = MediaType.undefined
                elif dirnames:
                    media_type = MediaType.folder
                elif filenames:
                    media_type = MediaType.album
        return media_type

    def fetch_target(self):
        self.__fetch(fetch_source=False)

    def fetch_source(self):
        self.__fetch(fetch_source=True)

    def __fetch(self, fetch_source=True):
        if fetch_source:
            media_type = self._source_type
            path = self._source_path
        else:
            media_type = self._target_type
            path = self._target_path
        if media_type == MediaType.database:
            self._session = MusicManager.create_session(path)
            data = self.__fetch_db()
            # TODO funtion to sort list into folder structure
        elif media_type == MediaType.folder:
            data = self.__fetch_folder(path)
        elif media_type == MediaType.album:
            data = self.__fetch_album(path)
        elif media_type == MediaType.file:
            data = self.__fetch_file(path)
        else:
            raise Exception("Data cant be loaded")

        if fetch_source:
            self._source = data
        else:
            self._target = data

    def __fetch_db(self):
        raise NotImplementedError
        # return self._session.query(Metadata).all()

    def __fetch_folder(self, path):
        raise NotImplementedError
        # list_meta = list()
        # gen = os.walk(path)
        # while True:
        #     try:
        #         source_dir, dirnames, filenames = next(gen)
        #     except StopIteration:
        #         break
        #     if not dirnames:
        #         list_meta.extend(self.__fetch_album(source_dir))
        # return list_meta

    def __fetch_album(self, path):
        return [AlbumMetadata(path)]

    def __fetch_file(self, path):
        return [Metadata(path)]

    def compare_tui(self):
        if self.target and self.source:
            tui.Tui(self, ret=True).main()
        else:
            if not self.target:
                print("target not defined")
            if not self.source:
                print("source not defined")

    """
    @staticmethod
    def create_session(db_file):
        #create a session and the db-file if not exist
        if not os.path.exists(db_file):
            if not os.path.exists(os.path.basename(db_file)):
                os.makedirs(os.path.basename(db_file))
        engine = 'sqlite:///' + db_file
        some_engine = sqlalchemy.create_engine(engine)
        Base.metadata.create_all(some_engine,
                                 Base.metadata.tables.values(), checkfirst=True)
        Session = orm.sessionmaker(bind=some_engine)
        return Session()
    """


class MetadataDict(dict):

    def __init__(self, init_value=None):
        super().__init__()
        self._init_value = init_value
        if not Metadata.class_initialized:
            Metadata.init_class()
        for key in Metadata.list_tags:
            self[key] = init_value

    def reset(self):
        for key in list(self):
            self[key] = self._init_value

class OverwriteDict(MetadataDict):

    def __init__(self, whitelist=None, blacklist=None):
        super().__init__(init_value=False)
        self.enable_count = 0
        self.tags_whitelist = Metadata.process_white_and_blacklist(whitelist=whitelist, blacklist=blacklist)
        self.reset()

    def reset(self):
        super().reset()
        for tag in self.tags_whitelist:
            self[tag] = True

    @property
    def all_state(self):
        if self.enable_count == 0:
            return False
        elif self.enable_count == len(self):
            return True
        else:
            return None

    def enable(self, key):
        if not self[key]:
            self[key] = True
            self.enable_count += 1

    def disable(self, key):
        if self[key]:
            self[key] = False
            self.enable_count -= 1

    def toggle(self, key):
        if self[key]:
            self.disable(key)
        else:
            self.enable(key)

    def enable_all(self):
        for key in self.keys():
            self.enable(key)

    def disable_all(self):
        for key in self.keys():
            self.disable(key)

    def toggle_all(self):
        if isinstance(self.all_state, type(None)) or self.all_state:
            self.disable_all()
        else:
            self.enable_all()


class MediaType(enum.Enum):
    database = 0,
    file = 1,
    album = 2,
    folder = 3,
    undefined = 42

class DiffType(enum.Enum):
    unchanged = 1,  # normal
    overwrite = 2,  # red
    deleted = 3,    # magenta
    new = 4,        # green

"""
if __name__ == "__main__":

    project_folder = "/home/johannes/Desktop/MusicManager"
    source_root = "/home/johannes/Desktop/MusicManager/media"
    target_root = "/home/johannes/Desktop/MusicManager/test"
    # source_root = target_root
    # source_root = "/home/johannes/Drives/SteamLinux/Music_20191225"
    #source_root = "/home/johannes/CloudStation/Music/MusicMp3"
    #project_folder = source_root

    # Metadata.load_tag_association_yaml(project_folder)
    # Metadata.save_tag_association_yaml(project_folder)

    db_file = os.path.join(project_folder, 'mmproject.db3')
    #if os.path.exists(db_file):
    #    os.remove(db_file)

    gen = os.walk(source_root)


    #mm.source_path = "/home/johannes/Desktop/MusicManager/media/Abrahma/Reflections_In_The_Bowels_Of_A_Bird_(2015)"
    #print(len(mm.source))
    #mm.source_path = "/home/johannes/Desktop/MusicManager/media/Infected_Rain"
    #print(len(mm.source))
    #mm.source_path = "/home/johannes/Desktop/MusicManager/media"
    #print(len(mm.source))
    #mm.source_path = "/home/johannes/Desktop/MusicManager/mmproject.db3"
    #print(len(mm.source))

    #mm.scan_tags(gen)
    #mm.write_tags()
"""