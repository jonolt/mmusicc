import mutagen
from mutagen.flac import FLAC
from mutagen.oggvorbis import OggVorbis

from mmusicc.formats._audio import AudioFile
from mmusicc.formats._misc import AudioFileError
from mmusicc.formats._util import scan_dictionary
from mmusicc.util.allocationmap import dict_tags_str

extensions = [".ogg", ".oga", ".flac"]
# loader   see bottom
# types    see bottom
ogg_formats = [FLAC, OggVorbis]


class MutagenVCFile(AudioFile):
    format = "Unknown Mutagen + vorbiscomment"
    MutagenType = None

    can_change_images = True

    def __init__(self, file_path, audio):
        super().__init__(file_path)
        self._file = audio

    def file_read(self):

        dict_tmp = dict()
        tags = self._file.tags.copy()
        for tag in tags:
            tag_key = tag[0]
            tag_val = tag[1]
            if tag_key in dict_tmp:
                if isinstance(dict_tmp[tag_key], str):
                    dict_tmp[tag_key] = [dict_tmp[tag_key]]
                dict_tmp[tag_key].append(tag_val)
            else:
                dict_tmp[tag_key] = tag_val

        self.unprocessed_tag.update(
            scan_dictionary(dict_tmp, self.dict_meta, dict_tags_str))

    def file_save(self, remove_existing=False):

        self.check_file_path()

        if self._file.tags is None:
            self._file.add_tags()

        audio = self._file
        new_tag = self.dict_meta

        if remove_existing:
            to_remove = [z for z in audio if z not in new_tag]
            for z in to_remove:
                del (audio[z])

        self._file.update(new_tag)
        self._file.save()


class OggFile(MutagenVCFile):
    format = "Ogg Vorbis"
    mimes = ["audio/vorbis", "audio/ogg; codecs=vorbis"]
    MutagenType = OggVorbis


class FLACFile(MutagenVCFile):
    format = "FLAC"
    mimes = ["audio/x-flac", "application/x-flac"]
    MutagenType = FLAC


types = []
for var in list(globals().values()):
    if getattr(var, 'MutagenType', None):
        types.append(var)


def loader(filename):
    """
    Returns:
        AudioFile
    Raises:
        AudioFileError
    """
    audio = mutagen.File(filename, options=ogg_formats)
    if audio is None:
        raise AudioFileError("file type could not be determined")
    mutagen_type = type(audio)
    for xiph in [FLACFile, OggFile]:
        if mutagen_type is getattr(xiph, "MutagenType", None):
            return xiph(filename, audio)
    raise AudioFileError("file type could not be determined")
