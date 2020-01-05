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

Base = declarative_base()


class Metadata(Base):

    __tablename__ = 'meta'
    _id = Column(Integer, primary_key=True, name="id")
    _file = Column(String(1023))
    _log = Column(String(1023))
    _unproccessed_tags = Column(String(8191))
    TALB = Column(String(127))  # Album
    TDRC = Column(String(4))  # Year
    TPE1 = Column(String(127))  # Artist (Lead Artist/Performer/Soloist/Group)
    TPE2 = Column(String(127))  # Album Artist (Band/Orchestra/Accompaniment)
    TRCK = Column(String(127))  # Track Number
    TIT2 = Column(String(127))  # Title (Song)
    TCON = Column(String(127))  # Content type (Genre)
    USLT = Column(String(4095))  # Unsynchronised lyrics/text transcription
    COMM = Column(String(255))  # User comment
    TBPM = Column(String(127))  # Beats per minute
    TCOM = Column(String(127))  # Composer
    TPOS = Column(String(4))  # Part of set (CD-Nummer)
    TSRC = Column(String(127))  # International Standard Recording Code
    DISCID = Column(String(127))
    DISKTOT = Column(String(4))
    TRKTOT = Column(String(4))

    class_initialized = False
    # TODO same again with int to show autofill changes
    # TODO store numbers as int
    # TODO add option to change between normal and dash notation in id3 tag (and write to vorbis tags)
    # TODO mark autofill fields
    # TORY = Column(String(4))  # Orginal Release Year
    # TOPE = Column(String(127))  # Original Artist/Performer

    path_config_yaml = "config.yaml"
    list_displ_tags = None
    list_id3_tags = dict()
    dict_id3_to_vorbis = dict()
    dict_id3_to_str = dict()

    @classmethod
    def init_class(cls):
        if not os.path.exists(cls.path_config_yaml):
            raise FileNotFoundError("config file not found")
        with open(cls.path_config_yaml, 'r') as f:
            cls.dict_config = yaml.safe_load(f)
        cls.list_displ_tags = [None]*20
        for key, value in cls.dict_config.items():
            pos = value[0]
            id3_tag = value[1]
            assertions = value[2]
            cls.dict_id3_to_vorbis[id3_tag] = key
            strings = []
            if key not in assertions:
                strings.append(key)
            for val in assertions:
                strings.append(val)
            cls.dict_id3_to_str[id3_tag] = strings
            cls.list_displ_tags[pos] = key
        cls.list_id3_tags = list(cls.dict_id3_to_vorbis.keys())
        cls.class_initialized = True

    @property
    def file(self):
        return self._file

    @property
    def path_struct(self):
        struct = list()
        tmp = self._file
        while len(tmp) > 1:
            tmp, apnd = os.path.split(tmp)
            struct.append(apnd)
        struct[0] = os.path.splitext(struct[0])[0]
        return struct

    def __init__(self, file, autofill=False, tracktotal=None, disctotal=None):
        if not Metadata.class_initialized:
            Metadata.init_class()
        self.autofill = autofill
        self.tracktotal = tracktotal
        self.disctotal = disctotal
        self.write_empty = True
        self._mp3 = None
        self._flac = None
        self._log = None
        self._unproccessed_tags = None
        self.dummy_dict = None
        if os.path.exists(file):
            self._file = file
        else:
            raise FileNotFoundError("Error File does not exist")
        try:
            ext = os.path.splitext(self._file)[1]
            if ext == ".mp3":
                try:
                    #self._mp3 = ID3(file)
                    self._mp3 = ID3()
                    self._mp3.load(file)
                except mutagen.id3.ID3NoHeaderError:
                    print("no header found")
                self.__read_tag_mp3()
            elif ext == ".flac":
                self._flac = FLAC(file)
                self.__read_tag_flac()
        except mutagen.MutagenError as ex:
            print('scanning File "{}" failed!'.format(file))
        print(self.path_struct)

    def log_to_db(self, msg):
        if self._log:
            self._log = (self._log + '\n' + msg)
        else:
            self._log = msg

    def import_tag(self, source_meta, whitelist=None, blacklist=None):
        if not whitelist:
            whitelist = Metadata.list_id3_tags
        if blacklist:
            for t in blacklist:
                try:
                    whitelist.pop(whitelist.index(t))
                except ValueError:
                    print("warning {} not in whitelist".format(t))
                    continue
        if "TALB" in whitelist:
            self.TALB = source_meta.TALB
        if "TDRC" in whitelist:
            self.TDRC = source_meta.TDRC
        if "TPE1" in whitelist:
            self.TPE1 = source_meta.TPE1
        if "TPE2" in whitelist:
            self.TPE2 = source_meta.TPE2
        if "TRCK" in whitelist:
            self.TRCK = source_meta.TRCK
        if "TIT2" in whitelist:
            self.TIT2 = source_meta.TIT2
        if "TCON" in whitelist:
            self.TCON = source_meta.TCON
        if "USLT" in whitelist:
            self.USLT = source_meta.USLT
        if "COMM" in whitelist:
            self.COMM = source_meta.COMM
        if "TBPM" in whitelist:
            self.TBPM = source_meta.TBPM
        if "TCOM" in whitelist:
            self.TCOM = source_meta.TCOM
        if "TPOS" in whitelist:
            self.TPOS = source_meta.TPOS
        if "TSRC" in whitelist:
            self.TSRC = source_meta.TSRC
        if "DISKID" in whitelist:
            self.DISKID = source_meta.DISKID
        #if "DISKTOT" in whitelist:
        #    self.DISKTOTD = source_meta.DISKTOTD
        #if "TRKTOT" in whitelist:
        #    self.TRKTOT = source_meta.TRKTOT

    def write_tag(self, confirm=True, delete=False, whitelist=None, blacklist=None):
        # TODO convert blacklist to whitelist
        if not whitelist:
            whitelist = Metadata.list_id3_tags
        if blacklist:
            for t in blacklist:
                whitelist.pop(t)
        if isinstance(self._mp3, mutagen.id3.ID3):
            self.__write_tag_mp3(confirm=confirm, delete_all_first=True, tags=whitelist)
        elif isinstance(self._flac, mutagen.flac.FLAC):
            self.__write_tag_flac(confirm=confirm, delete_all_first=True, tags=whitelist)

    def __write_tag_flac(self, tags, confirm=True, delete_all_first=True):

        if isinstance(tags, str):
            tags = [tags]

        if isinstance(tags, str):
            tags = [tags]

        if delete_all_first:
            self._flac.delete()

        if not self._flac.tags:
            self._flac.add_tags()

        for tag in tags:
            eval_tmp = eval("self.{0}".format(tag))
            str_tmp = self.repl_none(eval_tmp)
            self._flac.tags[self.dict_id3_to_vorbis[tag]] = str_tmp
        #    print(eval("self.{0}".format(tag)))
        #    exec("self._flac.tags['{0}'] = self.{0}".format(tag))

        #if 'TALB' in tags:
        #    self._flac.tags['TALB'] = self.TALB


        self._flac.save()


    def __write_tag_mp3(self, tags, confirm=True, delete_all_first=True):

        if isinstance(tags, str):
            tags = [tags]

        if isinstance(tags, str):
            tags = [tags]

        if delete_all_first:
            self._mp3.delete()

        if 'TALB' in tags:
            self._mp3.add(mutagen.id3.TALB(text=self.TALB))
        if 'TDRC' in tags:
            self._mp3.add(mutagen.id3.TDRC(text=self.TDRC))
        if 'TPE1' in tags:
            self._mp3.add(mutagen.id3.TPE1(text=self.TPE1))
        if 'TPE2' in tags:
            self._mp3.add(mutagen.id3.TPE2(text=self.TPE2))
        if 'TRCK' in tags:
            self._mp3.add(mutagen.id3.TRCK(text=self.TRCK))
        if 'TIT2' in tags:
            self._mp3.add(mutagen.id3.TIT2(text=self.TIT2))
        if 'TCON' in tags:
            self._mp3.add(mutagen.id3.TCON(text=self.TCON))
        if 'USLT' in tags:
            self._mp3.add(mutagen.id3.USLT(text=self.USLT))
        if 'COMM' in tags:
            self._mp3.add(mutagen.id3.COMM(text=self.repl_none(self.COMM)))
        if 'TBPM' in tags:
            self._mp3.add(mutagen.id3.TBPM(text=[self.repl_none(self.TBPM)]))
        if 'TCOM' in tags:
            self._mp3.add(mutagen.id3.TCOM(text=[self.repl_none(self.TCOM)]))
        if 'TPOS' in tags:
            self._mp3.add(mutagen.id3.TPOS(text=self.TPOS))
        if 'TSRC' in tags:
            self._mp3.add(mutagen.id3.TSRC(text=self.TSRC))
        #if 'DISCID' in tags:
        #    self._mp3.add(mutagen.id3.TALB(text=self.TALB))
        #if 'DISKTOT' in tags:
        #    self._mp3.add(mutagen.id3.TALB(text=self.TALB))
        #if 'TRKTOT' in tags:
        #    self._mp3.add(mutagen.id3.TALB(text=self.TALB))
        #self._mp3.add(mutagen.id3.TALB(text=[u"new value"]))

        self._mp3.save(v1=2, v2_version=4)

    @staticmethod
    def repl_none(string):
        if not string:
            return ""
        return string

    def delete_tag(self, confirm=True, delete=False, tags=None):
        if self._mp3:
            self.__delete_tag_mp3(confirm=confirm, delete=False, tags=tags)
        elif self._flac:
            self.__delete_tag_flac(confirm=confirm, delete=False, tags=tags)

        # delete(filething=None)

    def __delete_tag_flac(self, confirm=True, tags=None):
        pass
        # self._flac.delete()

    def __delete_tag_mp3(self, confirm=True, tags=None):
        pass
        # self._flac.delete()

    def read_tag(self):
        if isinstance(self._mp3, mutagen.id3.ID3):
            self.__read_tag_mp3()
        elif self._flac:
            self.__read_tag_flac()

    def __read_tag_flac(self):
        if not self._flac.tags:
            return
        self.dummy_dict = dict(self._flac.tags.copy())
        self.TALB = self.__get_flac_tag("TALB")
        self.TDRC = self.__get_flac_tag("TDRC")
        self.TPE1 = self.__get_flac_tag("TPE1")
        self.TPE2 = self.__get_flac_tag("TPE2")
        if self.autofill and not self.TPE2:
            self.TPE2 = self.TPE1
        self.TRCK = self.__get_flac_tag("TRCK")
        self.TRKTOT = self.__get_flac_tag("TRKTOT")
        if self.tracktotal:
            if self.autofill and not self.TRKTOT:
                self.TRKTOT = self.tracktotal
            elif not self.tracktotal == int(self.TRKTOT):
                self.__log_to_db_values_do_not_match("TRKTOT", self.TRKTOT, self.tracktotal)
        self.TIT2 = self.__get_flac_tag("TIT2")
        self.TCON = self.__get_flac_tag("TCON")
        self.USLT = self.__get_flac_tag("USLT")  # SYLT
        self.COMM = self.__get_flac_tag("COMM")
        self.TBPM = self.__get_flac_tag("TBPM")
        self.TCOM = self.__get_flac_tag("TCOM")
        self.TPOS = self.__get_flac_tag("TPOS")
        self.DISKTOT = self.__get_flac_tag("DISKTOT")
        if self.disctotal:
            if self.autofill and not self.DISKTOT:
                self.DISKTOT = self.disctotal
            elif not self.disctotal == self.DISKTOT:
                self.__log_to_db_values_do_not_match("DISKTOT", self.DISKTOT, self.disctotal)
        self.TSRC = self.__get_flac_tag("TSRC")
        self.DISCID = self.__get_flac_tag("DISCID")
        if self.dummy_dict:
            self._unproccessed_tags = str(self.dummy_dict)

    def __read_tag_mp3(self):
        self.dummy_dict = dict(self._mp3.items().copy())
        for key in self.dummy_dict.keys():
            if "APIC:" in key:
                self.dummy_dict.pop(key)
                break
        self.TALB = self.__get_id3_tag("TALB")
        tmp_tdrc = self.__get_id3_tag("TDRC")
        if tmp_tdrc:
            self.TDRC = str(tmp_tdrc.year)
        self.TPE1 = self.__get_id3_tag("TPE1")
        self.TPE2 = self.__get_id3_tag("TPE2")
        if self.autofill and not self.TPE2:
            self.TPE2 = self.TPE1
        self.TRCK = self.__get_id3_tag("TRCK")
        self.TRKTOT = self.__get_id3_tag("TRKTOT")
        if self.autofill and self.TRCK and "/" in self.TRCK:
            tmp = self.TRCK.split('/')
            self.TRCK = tmp[0]
            # TODO check if already filled with tag (unwahrscheinlich)
            self.TRKTOT = tmp[1]
        if self.autofill and self.tracktotal:
            if not self.TRKTOT:
                self.TRKTOT = self.tracktotal
            elif not self.tracktotal == int(self.TRKTOT):
                self.__log_to_db_values_do_not_match("TRKTOT", self.TRKTOT, self.tracktotal)
        self.TIT2 = self.__get_id3_tag("TIT2")
        self.TCON = self.__get_id3_tag("TCON")
        self.USLT = self.__get_id3_tag("USLT")
        self.COMM = self.__get_id3_tag("COMM")
        self.TBPM = self.__get_id3_tag("TBPM")
        self.TCOM = self.__get_id3_tag("TCOM")
        self.TPOS = self.__get_id3_tag("TPOS")
        self.DISKTOT = self.__get_id3_tag("DISKTOT")
        if self.autofill and self.TPOS and "/" in self.TPOS:
            tmp = self.TPOS.split('/')
            self.TPOS = tmp[0]
            # TODO check if already filled with tag (unwahrscheinlich)
            self.DISKTOT = tmp[1]
        if self.autofill and self.disctotal:
            if self.DISKTOT and not self.disctotal == self.DISKTOT:
                self.__log_to_db_values_do_not_match("DISKTOT", self.DISKTOT, self.disctotal)
            else:
                self.DISKTOT = self.disctotal
        self.TSRC = self.__get_id3_tag("TSRC")
        self.DISCID = self.__get_id3_tag("DISCID")
        if self.dummy_dict:
            self._unproccessed_tags = str(self.dummy_dict)

    def __get_id3_tag(self, str_tag):
        try:
            val = self.dummy_dict.pop(str_tag).text[0]
            return val
        except KeyError:
            return None

    def __get_flac_tag(self, str_tag_id3, join=True):
        know_associations = Metadata.dict_id3_to_str.get(str_tag_id3)
        ret_val = []
        ret_key = []
        for k in know_associations:
            try:
                if self.dummy_dict:
                    val = self.dummy_dict.pop(k)
                else:
                    val = self._flac.tags.get(k)
                if val:
                    ret_val.append(val)
                    ret_key.append(k)
            except KeyError:
                continue
        if len(ret_val) == 0:
            return None
        else:
            if len(ret_val) > 1:
                i = 0
                j = 0
                while i < len(ret_val):
                    while j < len(ret_val):
                        if i == j:
                            j += 1
                            continue
                        if ret_val[i] == ret_val[j]:
                            self.log_to_db("dropped duplicate pair {}:{}, cheeping {}:{}"
                                           .format(ret_val[i], ret_key[i], ret_val[j], ret_key[j]))
                            ret_val.remove(ret_val[i])
                        j += 1
                    i += 1
                if join:
                    return ';'.join(ret_val)
                else:
                    return ret_val
            return ret_val[0]

    def __log_to_db_values_do_not_match(self, tag, meta, scan):
        self.log_to_db("{} do not match metadata -> {} != {} <- folder anaylysis".format(tag, meta, scan))


class MusicManager:

    suported_files = [".mp3", ".flac"]

    def __init__(self):
        self._session = None
        self._source_path = None
        self._source_type = None
        self._source = None
        self._target_path = None
        self._target_type = None
        self._target = None
        self.overwrite_dict = OverwriteDict()

    @property
    def source_path(self):
        return self._source_path

    @source_path.setter
    def source_path(self, path):
        self._source_path = path
        self._source_type = self.get_object_type(path)
        if self._source_type:
            self.fetch_source()
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
        self._target_path = path
        self._target_type = self.get_object_type(path)
        if self._target_type:
            self.fetch_target()
        else:
            print("path not valid: {}".format(path))

    @property
    def target(self):
        # TODO formatting of different types
        return self._target

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

        if fetch_source:
            self._source = data
        else:
            self._target = data

    def __fetch_db(self):
        return self._session.query(Metadata).all()

    def __fetch_folder(self, path):
        list_meta = list()
        gen = os.walk(path)
        while True:
            try:
                source_dir, dirnames, filenames = next(gen)
            except StopIteration:
                break
            if not dirnames:
                list_meta.extend(self.__fetch_album(source_dir))
        return list_meta

    def __fetch_album(self, path):
        list_meta = list()
        for file in os.listdir(path):
            if os.path.splitext(file)[1] in MusicManager.suported_files:
                file_path = os.path.join(path, file)
                list_meta.append(Metadata(file_path))
        return list_meta

    def __fetch_file(self, path):
        return [Metadata(path)]

    def _compare_tui(self):
        if self.target and self.source:
            self.tui = tui.Tui(self).main()
        else:
            if not self.target:
                print("target not defined")
            if not self.source:
                print("source not defined")

    def write_tags(self, confirm=True, sql_query=None):
        if sql_query:
            meta_list1 = self._session.execute(text("SELECT * FROM meta")).fetchall()
            raise Exception("not working returns row_proxy, not metadata obj")
        #else:
        meta_list = self._session.query(Metadata).all()

        if not confirm:
            input("Metadata will be Overwriten without backup. Confirm")

        for meta in meta_list:
            if os.path.exists(meta.file):
                meta.write_tag(confirm=confirm)

    @staticmethod
    def create_session(db_file):
        """create a session and the db-file if not exist"""
        if not os.path.exists(db_file):
            if not os.path.exists(os.path.basename(db_file)):
                os.makedirs(os.path.basename(db_file))
        engine = 'sqlite:///' + db_file
        some_engine = sqlalchemy.create_engine(engine)
        Base.metadata.create_all(some_engine,
                                 Base.metadata.tables.values(), checkfirst=True)
        Session = orm.sessionmaker(bind=some_engine)
        return Session()


class OverwriteDict(dict):

    def __init__(self):
        super().__init__()
        if not Metadata.class_initialized:
            Metadata.init_class()
        for key in Metadata.dict_id3_to_vorbis.keys():
            self[key] = False
        self.enable_count = 0

    @property
    def all_state(self):
        if self.enable_count == 0:
            return False
        elif self.enable_count == len(Metadata.dict_id3_to_vorbis):
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