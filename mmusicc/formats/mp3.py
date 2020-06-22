#  Copyright (c) 2020 Johannes Nolte
#  SPDX-License-Identifier: GPL-3.0-or-later

import copy
import logging

import mutagen

import mmusicc.util.allocationmap as am
from mmusicc.formats._audio import AudioFile
from mmusicc.util.metadatadict import Empty, scan_dictionary, AlbumArt
from mmusicc.util.util import text_parser_get, join_str_list

extensions = [".mp3", ".mp2", ".mp1", ".mpg", ".mpeg"]
"""list of all extensions associated with this module"""
# loader   see bottom
# types    see bottom


def _to_album_art(frame):
    album_art = AlbumArt()
    album_art.desc = frame.desc
    album_art.ptype = frame.type
    album_art.data = frame.data
    album_art.mime = frame.mime
    return album_art


class MP3File(AudioFile):
    """Tag object for mp3 files using ID3 tag standard.

    Instance created by loader (at the bottom of this code) which in this case
    is this class itself (vgl. xiph).

    Args:
        file_path      (str): file path of represented audio file
    """

    format = "MP3"  # "or MPEG-1/3"
    mimes = ["audio/mp3", "audio/x-mp3", "audio/mpeg", "audio/mpg", "audio/x-mpeg"]

    def __init__(self, file_path):
        super().__init__()
        self._file = mutagen.File(file_path)
        self._changed_tags = None

    def file_read(self):
        """reads file tags into AudioFile tag dictionary (dict_meta).

        First tries to associate ID3 tags, than takes all txxx tags and runs
        them through the scan dictionary function.
        """
        tags_txxx = dict()

        for frame in self._file.values():

            frame_type = type(frame)
            frame_type_parent = frame_type.mro()[1]

            # handle each frame depending on parent class
            if frame.FrameID == "APIC":
                tag_val = _to_album_art(frame)
            elif frame_type is mutagen.id3.TXXX:
                tags_txxx[frame.desc] = frame.text[0]
                continue
            elif frame_type_parent is mutagen.id3.TextFrame:
                tag_val = frame.text[0]
            elif frame_type_parent is mutagen.id3.PairedTextFrame:
                tmp_key = "PairedTextFrame not supported:" + frame.HashKey
                self.unprocessed_tag[tmp_key] = frame.people
                continue
            elif frame_type_parent is mutagen.id3.NumericPartTextFrame:
                tag_val = frame.text[0]
            elif frame_type_parent is mutagen.id3.NumericTextFrame:
                tag_val = frame.text[0]
            elif frame_type_parent is mutagen.id3.TimeStampTextFrame:
                tag_val = frame.text[0].get_text()
            elif frame_type_parent is mutagen.id3.Frame:
                tag_val = frame.text
            else:
                raise Exception("frame not implemented %s", frame.HashKey)

            if Empty.is_empty(tag_val):
                tag_val = Empty()

            tag_key = am.dict_id32tag.get(frame.FrameID)
            if tag_key:
                if isinstance(tag_val, Empty) or isinstance(tag_val, AlbumArt):
                    val = tag_val
                else:
                    val = text_parser_get(tag_val)
                    if len(val) == 1:
                        val = val[0]
                self.dict_meta[tag_key] = val
            else:
                self.unprocessed_tag[frame.HashKey] = tag_val

        if len(tags_txxx) > 0:
            unprocessed_txxx = scan_dictionary(tags_txxx, self.dict_meta)
            # restore original tag hash to be able to delete it
            restored_txxx = dict()
            for key in tags_txxx:
                if key.casefold() in unprocessed_txxx:
                    restored_txxx["TXXX:" + key] = tags_txxx[key]
            self.unprocessed_tag.update(restored_txxx)

        return self

    def file_save(
        self, remove_existing=False, write_empty=False, remove_v1=False, dry_run=False
    ):
        """saves file tags from tag dictionary (dict_meta) to AudioFile.

        Note:
            write_empty may have no effect. Since mutagen will not load empty
            tags it can't be checked. Correction or Info is appreciated.

        Args:
            remove_existing ('bool', optional): if true clear all tags on file
                before writing. Defaults to False.
            write_empty     (bool): Only affects TXXX tags. Existing tags will
                always be set to None. If true create empty TXXX tags with
                value none. If false no tag will be created or existing
                TXXX tag on file will be deleted. Defaults to False.
            remove_v1       ('bool'): If True, remove existing ID3.V1 tags.
                Defaults to False.
            dry_run (bool): if true, do anything but saving to file. Defaults to False

        Returns:
            int: 1 if data was saved to file, zero if nothing was changed on file.
        """
        self._changed_tags = list()

        if not dry_run:
            audio = self._file
        else:
            audio = copy.deepcopy(self._file)

        if audio.tags is None:
            audio.add_tags()

        if audio.tags is None:
            audio.add_tags()

        tags_self = self.dict_meta.copy()
        tags_audio = list(audio.tags)

        for tag_key, value in tags_self.items():

            id3_tag = am.dict_tag2id3.get(tag_key)
            # load existing frame (or not)
            if id3_tag == "TXXX":
                txxx_tags = audio.tags.getall("TXXX")
                for tx in txxx_tags:
                    if tag_key in tx.desc.casefold():
                        frame = [tx]
                        break
                else:
                    frame = []
            else:
                frame = audio.tags.getall(id3_tag)
            if frame:
                if len(frame) > 1:
                    raise Exception(f"to many tags of {id3_tag} found")
                else:
                    frame = frame[0]
                tags_audio.remove(frame.HashKey)
                # if it exists, check if it has to be deleted
                if Empty.is_empty(value) and not write_empty:
                    self._changed_tags.append(("delall", frame.FrameID, value, "*"))
                    audio.tags.delall(frame.FrameID)
                    continue
                elif value is None:
                    if remove_existing:
                        self._changed_tags.append(("delall", frame.FrameID, value, "*"))
                        audio.tags.delall(frame.FrameID)
                    continue
            else:
                if value is None:
                    continue
                # if it does not exist, create a new one and add it to file
                frame = eval("mutagen.id3.{}()".format(id3_tag))
                audio.tags.add(frame)

            if Empty.is_empty(value):
                value = ""

            frame_type = type(frame)
            frame_type_parent = frame_type.mro()[1]

            if frame_type is mutagen.id3.TXXX:
                if tag_key not in frame.desc.casefold():
                    self._set_value(frame, "desc", tag_key)

            if frame.FrameID == "APIC":
                self._fill_apic_frame_with_albumart(frame, value)
            elif frame_type_parent is mutagen.id3.PairedTextFrame:
                # text frame support dropped
                continue
            else:
                if isinstance(value, list):
                    value = join_str_list(value)
                self._set_value(frame, "text", value)
            if not frame.encoding:
                self._set_value(frame, "encoding", mutagen.id3.Encoding.UTF16)
            try:
                lang = frame.lang
                if not lang:
                    self._set_value(frame, "lang", "eng")
            except AttributeError:
                pass

        if remove_existing:
            for tag, value in (
                MP3File(self.file_path).file_read().unprocessed_tag.items()
            ):
                tags_audio.remove(tag)
                audio.tags.delall(tag)
                self._changed_tags.append(("delall", tag, value, "*"))

        # make sure that every tag was checked
        # it is possible a tag is neither in loaded nor in the unprocessed tags list
        # this happened when a mp3 file had the to comment tags COMM and TXXX:COM,
        # where one off them overwrote the other.
        if not len(tags_audio) == 0:
            if remove_existing:
                for tag in tags_audio:
                    audio.tags.delall(tag)
                    self._changed_tags.append(("delall", tag, "N.A.", "*"))
                    logging.info(f"tags mismatch. Tags {tags_audio} were overlooked.")
            else:
                logging.warning(f"tags mismatch. Tags {tags_audio} were overlooked.")

        if len(self._changed_tags) == 0:
            return 0

        if remove_v1:
            v1 = 0  # ID3v1 tags will be removed
        else:  # 1  # ID3v1 tags will be updated  but not added
            v1 = 2  # ID3v1 tags will be created and / or updated

        logging.debug(f"changed tag: {self._changed_tags}")

        if not dry_run:
            audio.save(v1=v1, v2_version=4, v23_sep=None)
            logging.debug(f"File '{self.file_path}' saved.")

        return 1

    def _fill_apic_frame_with_albumart(self, frame, album_art):
        self._set_value(frame, "desc", album_art.desc)
        self._set_value(frame, "type", album_art.ptype)
        self._set_value(frame, "data", album_art.data)
        self._set_value(frame, "mime", album_art.mime)

    def _set_value(self, frame, attr, value):
        org = getattr(frame, attr)
        setattr(frame, attr, value)
        new = getattr(frame, attr)
        if not org == new:
            self._changed_tags.append((frame, attr, org, new))


types = [MP3File]
"""list of all subclasses of AudioFile in this module"""

loader = MP3File
"""class alias for dynamic loading of available AudioFile subclasses"""
