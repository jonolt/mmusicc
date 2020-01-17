# import logging
import mutagen

from mmusicc.formats._audio import AudioFile
from mmusicc.formats._util import (scan_dictionary, text_parser_get,
                                   join_str_list)
from mmusicc.metadata import Empty
from mmusicc.util.allocationmap import dict_id3_tags, dict_tags_id3

extensions = [".mp3", ".mp2", ".mp1", ".mpg", ".mpeg"]
# loader   see bottom
# types    see bottom

PAIRED_TEXT_FRAMES = ["TIPL", "TMCL", "IPLS"]


class MP3File(AudioFile):

    format = "MPEG-1/2"
    mimes = ["audio/mp3", "audio/x-mp3", "audio/mpeg", "audio/mpg",
             "audio/x-mpeg"]

    def __init__(self, file_path):
        super().__init__(file_path)
        self._file = mutagen.File(file_path)

    def file_read(self):
        tags_txxx = dict()

        for frame in self._file.values():
            frame_id = frame.FrameID
            if frame_id == "APIC":
                continue

            if frame_id in PAIRED_TEXT_FRAMES:
                tag_val = frame.people
                if isinstance(tag_val, list):
                    # val = [item for sublist in val for item in sublist]
                    flat_list = list()
                    for sublist in tag_val:
                        if sublist[0] == u'':
                            flat_list.append(sublist[1])
                        elif sublist[1] == u'':
                            flat_list.append(sublist[0])
                        else:
                            flat_list.extend(sublist)
                    tag_val = flat_list
            else:
                tag_val = frame.text
                if isinstance(tag_val, list):
                    if len(tag_val) == 1:
                        tag_val = tag_val[0]
                if isinstance(tag_val, mutagen.id3.ID3TimeStamp):
                    tag_val = tag_val.text
                elif Empty.is_empty(tag_val):
                    tag_val = Empty()

            if frame_id == "TXXX":
                tags_txxx[frame.desc] = tag_val
            else:
                try:
                    tag_key = dict_id3_tags.get(frame_id)
                    if tag_key:
                        self.dict_meta[tag_key] = text_parser_get(tag_val)
                    else:
                        raise KeyError("just to run exception code ;-)")
                except KeyError:
                    self.unprocessed_tag[frame.HashKey] = tag_val

        if len(tags_txxx) > 0:
            self.unprocessed_tag.update(
                scan_dictionary(tags_txxx, self.dict_meta, ignore_none=True))

    def file_save(self, remove_existing=False, remove_v1=False):

        if not self.check_file_path():
            self._file.tags.filename = self.file_path

        if self._file.tags is None:
            self._file.add_tags()

        audio = self._file

        if audio.tags is None:
            audio.add_tags()
        tags = audio.tags

        if remove_existing:
            for t in list(tags):
                del(tags[t])

        for tag_key, value in self.dict_meta.items():
            id3_tag = dict_tags_id3.get(tag_key)
            frame = eval("mutagen.id3.{}()".format(id3_tag))
            if frame.FrameID == "TXXX":
                frame.desc = tag_key
            MP3File.set_frame_text(frame, value)
            audio.tags.add(frame)

        if remove_v1:
            v1 = 0  # ID3v1 tags will be removed
        else:  # 1  # ID3v1 tags will be updated  but not added
            v1 = 2  # ID3v1 tags will be created and / or updated

        audio.save(v1=v1, v2_version=4, v23_sep=None)

    @staticmethod
    def set_frame_text(frame, text):
        if frame.FrameID in PAIRED_TEXT_FRAMES:  # hasattr(frame, "people"):
            paired_text = list()
            if isinstance(text, str):
                text = [text]
            for t in text:
                if isinstance(t, str):
                    paired_text.append([u'', t])
                elif isinstance(t, list) and len(t) == 2:
                    paired_text.append(t)
                else:
                    raise ValueError("cant parse paired text")
            frame.people = mutagen.id3.PairedTextFrame(
                mutagen.id3.Encoding.UTF8, paired_text).people
        else:
            if isinstance(text, list):
                text = join_str_list(text)
            frame.text = text
        frame.encoding = mutagen.id3.Encoding.UTF8
        try:
            lang = frame.lang
            if not lang:
                frame.lang = "XXX"
        except AttributeError:
            pass


loader = MP3File
types = [MP3File]
