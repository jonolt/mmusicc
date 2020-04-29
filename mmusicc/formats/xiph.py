import base64

import mutagen
from mutagen.flac import FLAC, Picture
from mutagen.oggvorbis import OggVorbis

from mmusicc.formats._audio import AudioFile
from mmusicc.formats._misc import AudioFileError
from mmusicc.util.metadatadict import Empty, scan_dictionary, AlbumArt

extensions = [".ogg", ".oga", ".flac"]
"""list of all extensions associated with this module"""
# loader   see bottom
# types    see bottom
ogg_formats = [FLAC, OggVorbis]


def _to_album_art(picture_or_data):
    if isinstance(picture_or_data, str):
        picture = Picture(base64.b64decode(picture_or_data))
    else:
        picture = picture_or_data
    album_art = AlbumArt()
    album_art.desc = picture.desc
    album_art.ptype = picture.type
    album_art.data = picture.data
    album_art.mime = picture.mime
    return album_art


def _album_art_to_picture(album_art):
    pic = Picture()
    pic.desc = album_art.desc
    pic.type = album_art.ptype
    pic.data = album_art.data
    pic.mime = album_art.mime
    return pic


def _album_art_to_picture_metablock(album_art):
    return base64.b64encode(_album_art_to_picture(album_art).write()).decode("ascii")


class VCFile(AudioFile):
    """Tag object for all files using tags of the xiph v-comment tag standard.

    Instance created by loader (at the bottom of this code).

    Args:
        audio (mutagen.File): file as mutagen file object.
    """

    format = "Unknown Mutagen + vorbiscomment"
    MutagenType = None

    can_change_images = True

    def __init__(self, audio):
        super().__init__()
        self._file = audio

    def file_read(self):
        """reads file tags into AudioFile tag dictionary (dict_meta)."""
        if self._file.tags:
            tags = self._file.tags.as_dict()

            pictures = list()
            for data in tags.pop("metadata_block_picture", []):
                pictures.append(_to_album_art(data))
            try:
                for pic in self._file.pictures:
                    pictures.append(_to_album_art(pic))
            except AttributeError:
                pass

            if pictures:
                tags.update({"albumart": pictures})

            for key in tags.keys():
                if len(tags[key]) == 1:
                    tags[key] = tags[key][0]
            self.unprocessed_tag.update(scan_dictionary(tags, self._dict_meta))

    def file_save(self, remove_existing=False, write_empty=False):
        """saves file tags from tag dictionary (dict_meta) to AudioFile.

            if no value changes the file is not saved, therefore there will be
            no changes at file (mtime does not change). When remove_existing
            is set, the file is saved, when unprocessed tags exists.

        Args:
            remove_existing (bool): if true clear all tags on file before
                writing. Defaults to False.
            write_empty     (bool): if true write empty tags an therefore
                create a tag with content "". If false no tag will be created
                and existing tags on file that would be overwritten with ""
                will be deleted. Defaults to False.

        Note:
            A tag not existing in dict_meta or being None in dict_meta will not be
            deleted and es kept unchanged. The (possible empty) tag will be deleted,
            when an Empty value is in source and write_empty is False.
        """
        audio = self._file
        if audio.tags is None:
            audio.add_tags()

        new_tag = self.dict_meta.copy_not_none()
        tag_remove = list()
        for key in new_tag.keys():
            if new_tag[key] is None:
                tag_remove.append(key)
            elif Empty.is_empty(new_tag[key]):
                if write_empty:
                    new_tag[key] = ""
                else:
                    tag_remove.append(key)

        for key in tag_remove:
            del new_tag[key]

        new_cover_keys = list()

        tag_equal = list()
        for key in new_tag.keys():
            tag = new_tag.get(key)
            if isinstance(tag, AlbumArt):
                new_cover_keys.append(key)
                continue
            elif isinstance(tag, str):
                tag = [tag]
            if audio.tags.get(key) == tag:
                tag_equal.append(key)

        has_metadata_block_picture = 0
        picture_attribute = False
        new_covers = [new_tag.pop(key) for key in new_cover_keys]
        try:
            old_covers = [_to_album_art(cover) for cover in self._file.pictures]
            picture_attribute = True
        except AttributeError:
            old_covers = [
                _to_album_art(cover)
                for cover in self._file.get("metadata_block_picture", [])
            ]
            if old_covers:
                has_metadata_block_picture = 1

        if not old_covers == new_covers and old_covers is not []:
            tag_equal.clear()
            if picture_attribute:
                [audio.add_picture(pic) for pic in new_covers]
            else:
                metablock = [
                    _album_art_to_picture_metablock(cover) for cover in new_covers
                ]
                new_tag["metadata_block_picture"] = metablock

        if len(tag_equal) == len(new_tag):
            tag_count_all = (
                len(tag_equal) + len(self.unprocessed_tag) + has_metadata_block_picture
            )
            if tag_count_all == len(audio.tags.keys()):
                if remove_existing and len(self.unprocessed_tag):
                    pass
                else:
                    return

        tag_del = [z for z in audio if z in tag_remove]
        if remove_existing:
            tag_del.extend([z for z in audio if z not in new_tag])

        for z in set(tag_del):
            del audio[z]

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
"""list of all subclasses of AudioFile in this module"""
for var in list(globals().values()):
    if getattr(var, "MutagenType", None):
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
            return xiph(audio)
    raise AudioFileError("file type could not be determined")
