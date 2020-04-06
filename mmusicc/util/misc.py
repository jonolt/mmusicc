import logging
import mimetypes
import os

import mmusicc.util.allocationmap as am


def check_is_audio(file):
    """Return True if file is a audio file."""
    mimetype = mimetypes.guess_type(file)
    if mimetype[0] and "audio" in mimetype[0]:
        return True
    else:
        return False


def process_white_and_blacklist(whitelist, blacklist):
    """creates a whitelist from one whitelist and one blacklist.

    Blacklist is processed after whitelist and will remove whitelisted
    items.

    Args:
        whitelist (list<str>): whitelist of tags to be imported. Loads all
            tags if None.
        blacklist (list<str>): blacklist of tags not to be imported. These
            items are removed from the whitelist. If none, whitelist is
            returned unprocessed.

    Returns:
        list<str>: whitelist after applying blacklisting.
    """
    if not whitelist:
        whitelist = am.list_tags.copy()
    if blacklist:
        for t in blacklist:
            try:
                whitelist.pop(whitelist.index(t))
            except ValueError:
                logging.warning("Warning can not remove {}. "
                                "It is not in the whitelist.".format(t))
                continue
    return whitelist


def swap_base(root_a, root_b, full_path):
    return os.path.join(root_b, full_path[len(root_a) + 1:])


def path_remove_root(root_a, full_path):
    return full_path[len(root_a) + 1:]


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

        from mmusicc.util.util import scan_dictionary

        rest = scan_dictionary(b_dict, self)
        return rest

    def reset(self):
        for key in list(self):
            self[key] = self._init_value

    def copy_not_none(self):
        return {k: v for k, v in self.items() if v is not None}

    def convert_none2empty(self):
        """can be used to remove/add all tags that have no value"""
        raise NotImplementedError()


def metadatadict(b_dict) -> MetadataDict:
    """returns a MetadataDict from the dict, unknown tags are dropped"""
    m_dict = MetadataDict()
    m_dict.import_builtin_dict(b_dict)
    return m_dict


class PairedText(object):
    """Proxy object for mutagen.id3.PairedTextFrames."""

    def __init__(self, role, name):
        if role == "":
            role = None
        self.role = role
        self.name = name

    def __repr__(self):
        if not self.role:
            return self.name
        else:
            return '{}: {}'.format(self.role, self.name)

    def __iter__(self):
        return [self.role, self.name]


class Empty(object):
    """object representing a tag without an value.

    It is a placeholder to be able to change the character/object which
    represents the Emptiness in the Database or at mutagen.
    """

    value = ""

    def __repr__(self):
        return "<empty>"

    def __eq__(self, other):
        if isinstance(other, Empty):
            return True
        else:
            return False

    @staticmethod
    def is_empty(text):
        if isinstance(text, Empty):
            return True
        if isinstance(text, str) and text.strip() == "":
            return True
        return False

    @staticmethod
    def is_empty_or_none(text):
        if text is None or Empty.is_empty(text):
            return True
        return False


class Div(object):
    """
    Object Representing a group different values. Provides rich comparison.

    Still Under Construction.

    Args:
        key                      (str, optional): dictionary key which values
            to represent
        list_metadata (list<Metadata>, optional): list of Metadata object
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
                    if not (self._dict_values.get(meta_a)
                            == other._dict_values.get(meta_b)):
                        equal = False
        if equal is None:
            equal = False
        return equal

    def add_metadata(self, key_tag, list_metadata):
        self._key_tag = key_tag
        for metadata in list_metadata:
            self.add_value(metadata, metadata.get_tag(self._key_tag))

    def add_value(self, obj, val):
        self._dict_values[obj] = val
