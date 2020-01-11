import mutagen
from mutagen.flac import FLAC, FLACNoHeaderError
from mutagen.oggvorbis import OggVorbis

from ._audio import AudioFile
from ._misc import AudioFileError

extensions = [".ogg", ".oga", ".flac"]
# loader   see bottom
# types    see bottom
ogg_formats = [FLAC, OggVorbis]


class MutagenVCFile(AudioFile):
    format = "Unknown Mutagen + vorbiscomment"
    MutagenType = None

    can_change_images = True

    def __init__(self):
        super().__init__()


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
    if audio is None and FLAC is not None:
        # FLAC with ID3
        try:
            audio = FLAC(filename)
        except FLACNoHeaderError:
            pass
    if audio is None:
        raise AudioFileError("file type could not be determined")
    Kind = type(audio)
    for klass in globals().values():
        if Kind is getattr(klass, 'MutagenType', None):
            return klass(filename, audio)
    raise AudioFileError("file type could not be determined")
