import mutagen
from mutagen.flac import FLAC
from mutagen.oggvorbis import OggVorbis

from mmusicc.formats._audio import AudioFile
from mmusicc.formats._misc import AudioFileError
from mmusicc.formats._util import scan_dictionary

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

        dummy_dict = dict(self._file.tags.copy())

        self.unprocessed_tag.update(
            scan_dictionary(dummy_dict, self.dict_meta,
                            MutagenVCFile.dict_tags_str))

    def file_save(self):
        pass


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
