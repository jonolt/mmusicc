import mutagen
from mutagen.flac import FLAC
from mutagen.oggvorbis import OggVorbis

from mmusicc.formats._audio import AudioFile
from mmusicc.formats._misc import AudioFileError
from mmusicc.formats._util import scan_dictionary
from mmusicc.metadata import Empty

extensions = [".ogg", ".oga", ".flac"]
# loader   see bottom
# types    see bottom
ogg_formats = [FLAC, OggVorbis]


class VCFile(AudioFile):
    """Tag object for all files using tags of the xiph v-comment tag standard.

    Instance created by loader (at the bottom of this code).

    Args:
        file_path      (str): file path of represented audio file.
        audio (mutagen.File): file as mutagen file object.
    """
    format = "Unknown Mutagen + vorbiscomment"
    MutagenType = None

    can_change_images = True

    def __init__(self, file_path, audio):
        super().__init__(file_path)
        self._file = audio

    def file_read(self):
        """reads file tags into AudioFile tag dictionary."""
        dict_tmp = dict()
        if self._file.tags:
            tags = self._file.tags.copy()
        else:
            tags = []
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
            scan_dictionary(dict_tmp, self.dict_meta))

    def file_save(self, remove_existing=False, write_empty=True):
        """saves file tags to AudioFile from tag dictionary.

        Args:
            remove_existing (bool): if true clear all tags on file before
                writing. Defaults to False.
            write_empty     (bool): if true write empty tags an therefore
                create a tag with content "". If false no tag will be created
                and existing tags on file that would be overwritten with ""
                will be deleted. Defaults to True.
        """
        self.check_file_path()

        if self._file.tags is None:
            self._file.add_tags()

        audio = self._file
        new_tag = self.dict_meta
        tag_del = list()
        for key in new_tag.keys():
            if Empty.is_empty(new_tag[key]):
                if write_empty:
                    new_tag[key] = ""
                else:
                    tag_del.append(key)

        for key in tag_del:
            del new_tag[key]

        # tag_del may have elements with value none, but can still be
        # overwritten, since the tag_del values are a subset of not in new_tag.
        if remove_existing:
            tag_del = [z for z in audio if z not in new_tag]

        for z in tag_del:
            del (audio[z])

        self._file.update(new_tag)
        self._file.save()


class OggFile(VCFile):
    """File type specific subclass of VCFile"""
    format = "Ogg Vorbis"
    mimes = ["audio/vorbis", "audio/ogg; codecs=vorbis"]
    MutagenType = OggVorbis


class FLACFile(VCFile):
    """File type specific subclass of VCFile"""
    format = "FLAC"
    mimes = ["audio/x-flac", "application/x-flac"]
    MutagenType = FLAC


# list of subclasses of Audio File.
# Dynamically fills the supported type list with the above defined classes.
types = []
for var in list(globals().values()):
    if getattr(var, 'MutagenType', None):
        types.append(var)


def loader(file_path):
    """loads the given file into a VCFile object and returns it.

    Args:
        file_path (str): path of file to be loaded.
    Returns:
        AudioFile: VCFile tag objects with given file loaded.
    Raises:
        AudioFileError: if file type could not be determined.
    """
    audio = mutagen.File(file_path, options=ogg_formats)
    if audio is None:
        raise AudioFileError("file type could not be determined")
    mutagen_type = type(audio)
    for xiph in [FLACFile, OggFile]:
        if mutagen_type is getattr(xiph, "MutagenType", None):
            # initialize a VCFile Instance and return it
            return xiph(file_path, audio)
    raise AudioFileError("file type could not be determined")
