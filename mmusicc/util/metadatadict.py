import enum
from collections import defaultdict

from mmusicc.util.util import text_parser_get
from . import allocationmap as am


class MetadataDict(dict):
    """Dictionary containing tags as keys, values can be reset.

    Args:
        init_value (object, optional): initial value of all values,
            defaults to None.
    """

    def __init__(self, init_value=None):
        super().__init__()
        self._init_value = init_value
        for key in am.list_tags:
            self[key] = init_value

    def import_builtin_dict(self, b_dict) -> dict:
        """Import a dictionary into the MetadataDict, mapping TAGs.

        Args:
            b_dict (dict): any dictionary with tag, value pairs

        Returns:
            list: key value pairs that could't be imported.
        """
        rest = scan_dictionary(b_dict, self)
        return rest

    def reset(self):
        """Reset all values to initial values, defines at instance creation."""
        for key in list(self):
            self[key] = self._init_value

    def copy_not_none(self):
        """Returns a copy of the dictionary omitting items with value None.

        Returns:
            dict: copy of dict items which value is not None.
        """
        return {k: v for k, v in self.items() if v is not None}

    def convert_none2empty(self):
        """can be used to remove/add all tags that have no value"""
        raise NotImplementedError()


def metadatadict(b_dict) -> MetadataDict:
    """Returns a MetadataDict from the dict, unknown tags are dropped"""
    m_dict = MetadataDict()
    m_dict.import_builtin_dict(b_dict)
    return m_dict


class PairedText(object):
    """Proxy object for mutagen.id3.PairedTextFrames. Experimental not used."""

    def __init__(self, role, name):
        if role == "":
            role = None
        self.role = role
        self.name = name

    def __repr__(self):
        if not self.role:
            return self.name
        else:
            return "{}: {}".format(self.role, self.name)

    def __iter__(self):
        return [self.role, self.name]


class Empty(object):
    """Object representing the emptiness of a existing tag without an value."""

    value = ""

    def __repr__(self):
        return "<empty>"

    def __eq__(self, other):
        if isinstance(other, Empty):
            return True
        else:
            return False

    def __hash__(self):
        return 42

    @staticmethod
    def is_empty(text) -> bool:
        """Returns True if text is instance Empty or a empty string ''."""
        if isinstance(text, Empty):
            return True
        if isinstance(text, str) and text.strip() == "":
            return True
        return False

    @staticmethod
    def is_empty_or_none(text) -> bool:
        """Returns True if text is instance Empty, a empty string or None."""
        if text is None or Empty.is_empty(text):
            return True
        return False


class AlbumArt(object):
    def __init__(self):
        self.ptype = 0
        self.mime = u""
        self.desc = u""  # filename
        self.data = b""

    def __eq__(self, other):
        if isinstance(other, AlbumArt):
            return self.data_hash == other.data_hash and self.ptype == other.ptype
        else:
            return False

    def __repr__(self):
        return self.desc

    def __hash__(self):
        return hash((self.data_hash, self.ptype, self.desc))

    # might be useful in ne feature
    # def size(self):
    #     from PIL import Image
    #     import io
    #     img = Image.open(io.BytesIO(self.data))
    #     return img.size

    @property
    def data_hash(self):
        # not good but better than nothing
        return len(self.data)


class PictureType(enum.Enum):
    """Enumeration of image types defined by the ID3 standard for the APIC
    frame, but also reused in WMA/FLAC/VorbisComment.
    """

    OTHER = 0
    """Other"""

    FILE_ICON = 1
    """32x32 pixels 'file icon' (PNG only)"""

    OTHER_FILE_ICON = 2
    """Other file icon"""

    COVER_FRONT = 3
    """Cover (front)"""

    COVER_BACK = 4
    """Cover (back)"""

    LEAFLET_PAGE = 5
    """Leaflet page"""

    MEDIA = 6
    """Media (e.g. label side of CD)"""

    LEAD_ARTIST = 7
    """Lead artist/lead performer/soloist"""

    ARTIST = 8
    """Artist/performer"""

    CONDUCTOR = 9
    """Conductor"""

    BAND = 10
    """Band/Orchestra"""

    COMPOSER = 11
    """Composer"""

    LYRICIST = 12
    """Lyricist/text writer"""

    RECORDING_LOCATION = 13
    """Recording Location"""

    DURING_RECORDING = 14
    """During recording"""

    DURING_PERFORMANCE = 15
    """During performance"""

    SCREEN_CAPTURE = 16
    """Movie/video screen capture"""

    FISH = 17
    """A bright coloured fish"""

    ILLUSTRATION = 18
    """Illustration"""

    BAND_LOGOTYPE = 19
    """Band/artist logotype"""

    PUBLISHER_LOGOTYPE = 20
    """Publisher/Studio logotype"""


class Div(object):
    """
    Object Representing a group different values. Provides rich comparison.

    Still Under Construction.

    Args:
        key                      (str, optional): Dictionary key which values
            to represent
        list_metadata (list<Metadata>, optional): List of Metadata object
            containing the values.
    """

    def __init__(self, key=None, list_metadata=None):
        self._dict_values = dict()
        self._diff = None
        self._key_tag = None  # maybe not needed
        if key and list_metadata:
            self.add_metadata(key, list_metadata)

    def __repr__(self):
        return "<div>"

    def __eq__(self, other):
        if not isinstance(other, Div):
            return False
        equal = None
        for meta_a in list(self._dict_values):
            for meta_b in list(other._dict_values):
                if meta_a.file_name == meta_b.file_name:
                    if not (
                        self._dict_values.get(meta_a) == other._dict_values.get(meta_b)
                    ):
                        equal = False
        if equal is None:
            equal = False
        return equal

    def add_metadata(self, key_tag, list_metadata):
        """Adds the values of a key of a metadata objects to div list.

        Args:
            key_tag (str): Key of values to be added.
            list_metadata (list of Metadata): List of metadata which values to
                be added.
        """
        self._key_tag = key_tag
        for metadata in list_metadata:
            self.add_value(metadata, metadata.get_tag(self._key_tag))

    def add_value(self, metadata, value):
        """Adds one value to the Div object.
        
        Args:
            metadata: Metadata object the value belongs too.
            value: Value that is different.
        """
        self._dict_values[metadata] = value


def scan_dictionary(dict_tags, dict_data, parse_text=False):
    """Scan a dictionary (dict_tags) for tags and fill dict_data with them.

    Args:
        dict_tags (dict): dictionary (tag_str: value) items to be imported.
        dict_data   (dict): dictionary to be filled with imported tag values.
        parse_text  (bool): if True, pass values to text_parser_get else return value
            as it is. Defaults to False.
    Returns:
        dict<str, str>: dictionary with all tags whose name could not be
            associated with.
    """

    # Make a copy of the source dictionary, so it is unchanged
    dict_dummy = dict_tags.copy()
    dict_dummy = {k.casefold(): v for k, v in dict_dummy.items()}

    # filled with list so the same tag can have multiple values
    dict_tmp = defaultdict(list)

    # find a tag for each key in scanned dictionary
    for key_str in list(dict_dummy):
        try:
            tag_key = am.dict_str2tag[key_str]
            tag_val = dict_dummy.pop(key_str)
        except KeyError:
            continue

        if Empty.is_empty(tag_val):
            tag_val = Empty()

        if parse_text:
            dict_tmp[tag_key].extend(text_parser_get(tag_val))
        else:
            dict_tmp[tag_key].append(tag_val)

    for key, value in dict_tmp.items():
        if len(value) == 1:
            dict_data[key] = value[0]
        else:
            dict_data[key] = value

    return dict_dummy
