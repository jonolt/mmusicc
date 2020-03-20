import mutagen

from mmusicc.formats._audio import AudioFile
from mmusicc.formats._util import (scan_dictionary, text_parser_get,
                                   join_str_list)
from mmusicc.metadata import Empty
from mmusicc.util.allocationmap import dict_id32tag, dict_tag2id3

extensions = [".mp3", ".mp2", ".mp1", ".mpg", ".mpeg"]
# loader   see bottom
# types    see bottom

PAIRED_TEXT_FRAMES = ["TIPL", "TMCL", "IPLS"]


class MP3File(AudioFile):
    """Tag object for all files using tags of the xiph v-comment tag standard.

    Instance created by loader (at the bottom of this code) which in this case
    is this class itself (vgl. xiph).

    Args:
        file_path      (str): file path of represented audio file
    """

    format = "MPEG-1/2"
    mimes = ["audio/mp3", "audio/x-mp3", "audio/mpeg", "audio/mpg",
             "audio/x-mpeg"]

    def __init__(self, file_path):
        super().__init__(file_path)
        self._file = mutagen.File(file_path)

    def file_read(self):
        """reads file tags into AudioFile tag dictionary.
        First tries to associate ID3 tags, than takes all txxx tags and runs
        them through string parser.
        """
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
                    tag_key = dict_id32tag.get(frame_id)
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
        """saves file tags to AudioFile from tag dictionary.

        Args:
            remove_existing ('bool', optional): if true clear all tags before
                writing. Defaults to False.
            remove_v1       ('bool'): If True, remove existing ID3.V1 tags.
                Defaults to False.
        """
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
            if not value:
                continue
            id3_tag = dict_tag2id3.get(tag_key)
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
    def set_frame_text(frame, content):
        """Writes content into the specified frame.
        Merges Multiple values, sets frame language.

        Args:
            frame (mutagen.id3.Frame): frame to be writen to.
            content  (str, list(str)): content to be writen into the frame.
        Raises:
            ValueError: if text can not be parsed.
        """
        if frame.FrameID in PAIRED_TEXT_FRAMES:  # hasattr(frame, "people"):
            paired_text = list()
            if isinstance(content, str):
                content = [content]
            for t in content:
                if isinstance(t, str):
                    paired_text.append([u'', t])
                elif isinstance(t, list) and len(t) == 2:
                    paired_text.append(t)
                else:
                    raise ValueError("cant parse paired text")
            frame.people = mutagen.id3.PairedTextFrame(
                mutagen.id3.Encoding.UTF8, paired_text).people
        else:
            if isinstance(content, list):
                content = join_str_list(content)
            frame.text = content
        frame.encoding = mutagen.id3.Encoding.UTF8
        try:
            lang = frame.lang
            if not lang:
                frame.lang = "XXX"
        except AttributeError:
            pass


# list of subclasses of Audio File.
types = [MP3File]
# loads the given file into a VCFile object and returns it.
loader = MP3File
