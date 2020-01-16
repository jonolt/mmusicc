# from mutagen.mp3 import MP3
import mutagen

from mmusicc.formats._audio import AudioFile
from mmusicc.formats._util import scan_dictionary, text_parser_get
from mmusicc.metadata import Empty
from mmusicc.util.allocationmap import dict_id3_tags

# from ._constants import PATH

extensions = [".mp3", ".mp2", ".mp1", ".mpg", ".mpeg"]
# loader   see bottom
# types    see bottom


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

            if frame_id in ["TIPL", "TMCL", "IPLS"]:
                val = frame.people
                if isinstance(val, list):
                    val = [item for sublist in val for item in sublist]
            else:
                val = frame.text
                if isinstance(val, list):
                    if len(val) == 1:
                        val = val[0]
                if isinstance(val, mutagen.id3.ID3TimeStamp):
                    val = val.text
                elif Empty.is_empty(val):
                    val = Empty()

            if frame_id == "TXXX":
                tags_txxx[frame.desc] = val
            else:
                try:
                    tag_key = dict_id3_tags.get(frame_id)
                    if tag_key:
                        self.dict_meta[tag_key] = text_parser_get(val)
                    else:
                        raise KeyError("just to run exception code ;-)")
                except KeyError:
                    self.unprocessed_tag[frame.HashKey] = val

        if len(tags_txxx) > 0:
            self.unprocessed_tag.update(
                scan_dictionary(tags_txxx, self.dict_meta, ignore_none=True))

    def file_save(self):
        pass


loader = MP3File
types = [MP3File]
