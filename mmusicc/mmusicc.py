#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Dec 23 12:30:45 2019

@author: johannes



"""
import os

import mutagen
import sqlalchemy
import yaml
from mutagen.flac import FLAC
from mutagen.id3 import ID3
from sqlalchemy import Column, String, Integer
from sqlalchemy import orm
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class Metadata(Base):
    __tablename__ = 'mediaElement'
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
    # TODO same again with int to show autofill changes
    # TODO store numbers as int
    # TODO add option to change between normal and dash notation in id3 tag (and write to vorbis tags)
    # TODO mark autofill fields
    # TORY = Column(String(4))  # Orginal Release Year
    # TOPE = Column(String(127))  # Original Artist/Performer

    association_dict_id3_flac = {
        'TALB': ['ALBUM'],
        'TDRC': ['DATE', 'YEAR'],
        'TPE1': ['ARTIST'],
        'TPE2': ['ALBUMARTIST', 'ALBUM ARTIST'],
        'TRCK': ['TRACKNUMBER'],
        'TIT2': ['TITLE'],
        'TCON': ['GENRE'],
        'USLT': ['LYRICS', 'UNSYNCEDLYRICS'],
        'COMM': ['DESCRIPTION'],
        'TBPM': [],
        'TCOM': ['COMPOSER'],
        'TPOS': ['DISCNUMBER'],
        'TSRC': ['ISRC'],
        'DISCID': ['DISCID'],  # no official ID3 tag
        'DISKTOT': ['DISCTOTAL'],
        'TRKTOT': ['TRACKTOTAL', 'TOTALTRACKS'],
    }

    association_dict_flac_id3 = dict()

    @classmethod
    def __init_association_dict_flac_id3(cls):
        a = cls.association_dict_id3_flac.keys()
        for key in a:
            values = cls.association_dict_id3_flac.get(key)
            for value in values:
                # print("dict {}={}".format(key, value))
                cls.association_dict_flac_id3[value] = key
                # print(key,  v,  cls.association_dict_flac_id3)

    def __init__(self, file, autofill=False, tracktotal=None, disctotal=None):
        Metadata.__init_association_dict_flac_id3()
        self.autofill = autofill
        self.tracktotal = tracktotal
        self.disctotal = disctotal
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
                self._mp3 = ID3(file)
                self.__scan_mp3()
            elif ext == ".flac":
                self._flac = FLAC(file)
                self.__scan_flac()
        except mutagen.MutagenError:
            print('scanning File "{}" failed!'.format(file))

    def log_to_db(self, msg):
        if self._log:
            self._log = (self._log + '\n' + msg)
        else:
            self._log = msg

    def __scan_flac(self):
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

    def __scan_mp3(self):
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

    def __log_to_db_values_do_not_match(self, tag, meta, scan):
        self.log_to_db("{} do not match metadata -> {} != {} <- folder anaylysis".format(tag, meta, scan))

    def get_tag(self, str_tag):
        if self._mp3:
            return self.__get_id3_tag(str_tag)
        elif self._flac:
            return self.__get_flac_tag(str_tag)

    def __get_id3_tag(self, str_tag):
        # try:
        try:
            val = self.dummy_dict.pop(str_tag).text[0]
            return val
        except KeyError:
            return None
        #    return val  # self._mp3.getall(str_tag)[0].text[0]
        # except IndexError:
        #    return None

    def __get_flac_tag(self, str_tag_id3, join=True):
        know_associations = Metadata.association_dict_id3_flac.get(str_tag_id3)
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

    @classmethod
    def save_tag_association_yaml(cls, path=None):
        if path and os.path.exists:
            filedir = path
        else:
            filedir = os.path.curdir
        filepath = os.path.join(filedir, "tag_association.yaml")
        print(filepath)
        with open(filepath, 'w') as outfile:
            yaml.dump(cls.association_dict_id3_flac, outfile, default_flow_style=False)

    @classmethod
    def load_tag_association_yaml(cls, path=None, append=True):
        if path and os.path.exists(path):
            filedir = path
        else:
            filedir = os.path.curdir
        filepath = os.path.join(filedir, "tag_association.yaml")
        if os.path.exists(filepath):
            with open(filepath, 'r') as stream:
                try:
                    new_dict = yaml.safe_load(stream)
                    if append:
                        new_dict = cls._add_new_to_dict(cls.association_dict_id3_flac, new_dict)
                    cls.association_dict_id3_flac = new_dict
                except yaml.YAMLError as exc:
                    print(exc)
        else:
            print("No 'tag_association.yaml' file found, using hardcoded values")

    @staticmethod
    def _add_new_to_dict(old_dict, new_dict):
        for key in new_dict.keys():
            if key in old_dict.keys():
                vals = new_dict.get(key)
                for val in vals:
                    if val not in old_dict.get(key):
                        old_dict.get(key).append(val)
            else:
                print("Key '{}' can't be processed".format(key))
        return old_dict


class MusicManager:

    def __init__(self, session):
        self._session = session

    def scan_tags(self, gen, autofill=True):
        while True:
            try:
                source_dir, dirnames, filenames = next(gen)
            except StopIteration:
                break
            if not dirnames:
                target_dir = os.path.join(target_root, *source_dir.split("/")[2:])
                if not os.path.exists(target_dir):
                    pass
                if autofill:
                    tracktotal = len(list(filter(lambda x: ".flac" in x or ".mp3" in x, filenames)))
                    # TODO LOW auto find disctotal
                for filename in filenames:
                    if not os.path.splitext(filename)[1] == '.flac' and not os.path.splitext(filename)[1] == '.mp3':
                        # print(filename)
                        continue
                    source_path = os.path.join(source_dir, filename)
                    target_path = source_path
                    # target_path = os.path.join(target_dir, os.path.splitext(filename)[0] + ".mp3")
                    meta = Metadata(target_path, autofill=autofill, tracktotal=tracktotal, disctotal=None)
                    self._session.add(meta)
                    self._session.commit()

    @staticmethod
    def create_session(project_folder, db_file):
        """create a session and the db-file if not exist"""
        if not os.path.exists(project_folder):
            if not os.path.exists(project_folder):
                os.makedirs(project_folder)
        engine = 'sqlite:///' + db_file
        some_engine = sqlalchemy.create_engine(engine)
        Base.metadata.create_all(some_engine,
                                 Base.metadata.tables.values(), checkfirst=True)
        Session = orm.sessionmaker(bind=some_engine)
        return Session()


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
    if os.path.exists(db_file):
        os.remove(db_file)

    gen = os.walk(source_root)

    session = MusicManager.create_session(project_folder, db_file)
    mm = MusicManager(session)
    mm.scan_tags(gen)
