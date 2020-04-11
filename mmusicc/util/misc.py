import logging
import mimetypes
import pathlib

import mmusicc.util.allocationmap as am


def check_is_audio(file):
    """Return True if file is a audio file."""
    mimetype = mimetypes.guess_type(str(file))
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


def swap_base(root_a, path_a, root_b):
    """removes the root part of path_a and attaches the remainder to root
        of root_b crating path_b.

    Args:
        root_a (pathlib.Path): root path
        path_a (pathlib.Path): full path
        root_b (pathlib.Path): root path

    Returns:
        (pathlib.Path):

    """
    relative_path = path_a.relative_to(root_a)
    path_b = root_b.joinpath(relative_path)
    return path_b


def get_the_right_one(list_path, match_path, drop_suffix=True):
    """return the most matching path out of a list of (absolute) paths

    with has the most common elements beginning at the leaves of the tree.
    All string paths are automatically converted to pathlib Paths.

    Args:
        list_path (list of pathlib.Path or list of str):
            list of paths to be compared.
        match_path                (str or pathlib.Path):
            path to be matched.
        drop_suffix                    (bool, optional):
            if True, compare paths without extensions (if path points to a
            file). Defaults to True.

    Returns:
        pathlib.Path: Path from list which matches the match_path the most.

    Exceptions:
        KeyError: if not matching entry has been found.

    Example:
        >>> list_path = ['fuu/bar/mmusicc.flac', 'fuu/rab/mmusicc.ogg']
        >>> match_path = 'root/bar/mmusicc.ogg'
        >>> get_the_right_one(list_path, match_path)
        'fuu/bar/mmusicc.flac'
    """

    list_path = list_path.copy()
    for i in range(len(list_path)):
        list_path[i] = pathlib.Path(list_path[i])

    if not isinstance(match_path, pathlib.Path):
        match_path = pathlib.Path(match_path)
    if drop_suffix:
        match_path = match_path.with_suffix('')

    match_parts = match_path.parts

    i = 0
    while len(list_path) > 1:
        i += 1
        list_new = list()
        for path in list_path:
            if path.with_suffix('').parts[-i] == match_parts[-i]:
                list_new.append(path)
            else:
                pass
        list_path = list_new

        if i > 100:
            raise Exception("loop count to high")

    if len(list_path) == 0:
        raise KeyError("could not find matching entry")

    return list_path[0]


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
