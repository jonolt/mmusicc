#  Copyright (c) 2020 Johannes Nolte
#  SPDX-License-Identifier: GPL-3.0-or-later

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
        self._changed_tags = None

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
        self._changed_tags = list()

        audio = self._file
        if audio.tags is None:
            audio.add_tags()

        meta = self.dict_meta.copy_not_none()

        # handle write empty policy
        for key, value in list(meta.items()):
            if Empty.is_empty(value):
                if write_empty:
                    meta[key] = ""
                else:
                    self._changed_tags.append((key, audio[key], "*"))
                    del meta[key]
                    del audio[key]

        cover_keys = list()

        for key in meta.keys():
            tag = meta.get(key)
            if isinstance(tag, AlbumArt):
                cover_keys.append(key)
                continue
            self._set_value(audio, key, tag)

        new_art = [meta.get(key) for key in cover_keys]
        if hasattr(audio, "pictures"):
            org_art = [_to_album_art(cover) for cover in audio.pictures]
            clear = False
            for art in org_art.copy():
                if art not in new_art:
                    self._changed_tags.append(("albumart", art, "*"))
                    org_art.remove(art)
                    clear = True
            if clear:
                # clear all
                audio.clear_pictures()
                # add what was cleared to much
                [audio.add_picture(_album_art_to_picture(art)) for art in org_art]
            for art in new_art:
                if art not in org_art:
                    self._changed_tags.append(("albumart", "*", art))
                    audio.add_picture(_album_art_to_picture(art))
        else:
            org_art = dict()
            for block in audio.get("metadata_block_picture", []):
                org_art[_to_album_art(block)] = block

            for art in org_art.keys():
                if art not in new_art:
                    self._changed_tags.append(("albumart", art, "*"))
                    audio["metadata_block_picture"].remove(org_art.get(art))
            for art in new_art:
                if art not in org_art:
                    self._changed_tags.append(("albumart", "*", art))
                    if "metadata_block_picture" not in audio:
                        audio[
                            "metadata_block_picture"
                        ] = _album_art_to_picture_metablock(art)
                    else:
                        audio["metadata_block_picture"].append(
                            _album_art_to_picture_metablock(art)
                        )

            if audio.get("metadata_block_picture") is None:
                pass
            elif len(audio.get("metadata_block_picture", [])) > 0:
                meta["metadata_block_picture"] = "to not delete"
            else:
                del audio["metadata_block_picture"]

        if remove_existing:
            for key in [k for k in audio if k not in meta]:
                self._changed_tags.append((key, audio[key], "*"))
                del audio[key]

        if len(self._changed_tags) == 0:
            return

        # self._file.update(meta)
        self._file.save()

    def _set_value(self, dictionary, key, value):
        try:
            org = dictionary[key]
            dictionary[key] = value
            new = dictionary[key]
            if not new == org:
                self._changed_tags.append((key, org, new))
        except KeyError:
            dictionary[key] = value
            self._changed_tags.append((key, "*", value))


class OggFile(VCFile):
    """File type specific subclass of VCFile"""

    format = "Ogg Vorbis"
    mimes = ["audio/vorbis", "audio/ogg", "audio/x-ogg"]
    MutagenType = OggVorbis


class FLACFile(VCFile):
    """File type specific subclass of VCFile"""

    format = "FLAC"
    mimes = ["audio/flac", "audio/x-flac"]
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
