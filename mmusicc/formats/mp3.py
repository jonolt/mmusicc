import mutagen

import mmusicc.util.allocationmap as am
from mmusicc.formats._audio import AudioFile
from mmusicc.util.metadatadict import Empty, PairedText, scan_dictionary, AlbumArt
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


def _fill_apic_frame_with_albumart(frame, album_art):
    frame.desc = album_art.desc
    frame.type = album_art.ptype
    frame.data = album_art.data
    frame.mime = album_art.mime


class MP3File(AudioFile):
    """Tag object for mp3 files using ID3 tag standard.

    Instance created by loader (at the bottom of this code) which in this case
    is this class itself (vgl. xiph).

    Args:
        file_path      (str): file path of represented audio file
    """

    format = "MPEG-1/2"
    mimes = ["audio/mp3", "audio/x-mp3", "audio/mpeg", "audio/mpg", "audio/x-mpeg"]

    def __init__(self, file_path):
        super().__init__()
        self._file = mutagen.File(file_path)

    def file_read(self, drop_role=True):
        """reads file tags into AudioFile tag dictionary (dict_meta).

        First tries to associate ID3 tags, than takes all txxx tags and runs
        them through the scan dictionary function.

        Args:
            drop_role (bool): if True, drop the role of paired text frame and
                save as a list of strings. If False, save the
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
                tag_val = list()
                for role, name in frame.people:
                    if drop_role:
                        tag_val.append(name)
                    else:
                        tag_val.append(PairedText(role, name))
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
            self.unprocessed_tag.update(scan_dictionary(tags_txxx, self.dict_meta))

    def file_save(self, remove_existing=False, write_empty=False, remove_v1=False):
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
        """

        audio = self._file
        if audio.tags is None:
            self._file.add_tags()

        if remove_existing:
            audio.delete()

        if audio.tags is None:
            audio.add_tags()

        new_tags = self.dict_meta.copy_not_none()
        tag_remove = list()
        for tag_key, value in new_tags.items():

            id3_tag = am.dict_tag2id3.get(tag_key)

            # load existing frame (or not)
            frame = audio.get(id3_tag)
            if frame:
                # if it exists, check if it has to be deleted
                if Empty.is_empty(value) and not write_empty:
                    tag_remove.append(tag_key)
                    audio.tags.delall(frame.FrameID)
                    continue
            else:
                # if it does not exist, create a new one and add it to file
                frame = eval("mutagen.id3.{}()".format(id3_tag))
                audio.tags.add(frame)

            if Empty.is_empty(value):
                value = u""

            frame_type = type(frame)
            frame_type_parent = frame_type.mro()[1]

            if frame_type is mutagen.id3.TXXX:
                frame.desc = tag_key

            if frame.FrameID == "APIC":
                _fill_apic_frame_with_albumart(frame, value)
            elif frame_type_parent is mutagen.id3.PairedTextFrame:
                if isinstance(value, str):
                    value = [value]
                for t in value:
                    if isinstance(t, str):
                        frame.people.append([u"", t])
                    elif isinstance(t, list) and len(t) == 2:
                        frame.people.append(t)
                    elif isinstance(t, PairedText):
                        frame.people.append(list(t))
                    else:
                        raise ValueError("cant parse paired text")
            else:
                if isinstance(value, list):
                    value = join_str_list(value)
                frame.text = value
            frame.encoding = mutagen.id3.Encoding.UTF8
            try:
                lang = frame.lang
                if not lang:
                    frame.lang = "XXX"
            except AttributeError:
                pass

        if remove_v1:
            v1 = 0  # ID3v1 tags will be removed
        else:  # 1  # ID3v1 tags will be updated  but not added
            v1 = 2  # ID3v1 tags will be created and / or updated

        audio.save(v1=v1, v2_version=4, v23_sep=None)


types = [MP3File]
"""list of all subclasses of AudioFile in this module"""

loader = MP3File
"""class alias for dynamic loading of available AudioFile subclasses"""
