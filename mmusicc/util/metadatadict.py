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
            return '{}: {}'.format(self.role, self.name)

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
                    if not (self._dict_values.get(meta_a)
                            == other._dict_values.get(meta_b)):
                        equal = False
        if equal is None:
            equal = False
        return equal

    def add_metadata(self, key_tag, list_metadata):
        """Adds the values of a key of a metadata objects to div list.

        Args:
            key_tag (str): Key of values to be added.
            list_metadata (list of Metadata): List of metadtata which values to
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


def scan_dictionary(dict_tags, dict_data):
    """Scan a dictionary (dict_tags) for tags and fill dict_data with them.

    Args:
        dict_tags             (dict): dictionary (tag_str: value) items to be
            imported.
        dict_data             (dict): dictionary to be filled with imported tag
            values.
    Returns:
        dict<str, str>: dictionary with all tags whose name could not be
            associated with.

    TODO add string_parser and handle duplicate entries
    """

    # Make a copy of the source dictionary, so it is unchanged
    dict_dummy = dict_tags.copy()
    dict_dummy = {k.casefold(): v for k, v in dict_dummy.items()}

    # will be filled with list so the same tag can have multiple values
    dict_tmp = dict()

    # find a tag for each key in scanned dictionary
    for key_str in list(dict_dummy):
        try:
            tag_key = am.dict_str2tag[key_str]
        except KeyError:
            continue
        try:
            tag_val = dict_dummy.pop(key_str)
            if tag_key not in dict_tmp:
                dict_tmp[tag_key] = list()
            dict_tmp[tag_key].append((key_str, tag_val))
        except KeyError:
            continue

    # evaluate later if this code is needed, maybe delete it somewhen
    #
    # for tag_key, kv_pairs in dict_tmp.items():
    #     if len(kv_pairs) > 1:
    #         # take the list and check if entries a double
    #         i = 0
    #         j = 0
    #         while i < len(kv_pairs):
    #             while j < len(kv_pairs):
    #                 if i == j:
    #                     j += 1
    #                     continue
    #                 if kv_pairs[i][1] == kv_pairs[j][1]:
    #                     logging.info(
    #                         "dropped duplicate pair {}:{}"
    #                         ", keeping {}:{}"
    #                         .format(kv_pairs[i][0], kv_pairs[i][1],
    #                                 kv_pairs[j][0], kv_pairs[j][1]))
    #                     kv_pairs.remove(kv_pairs[i])
    #                 j += 1
    #             i += 1
    #         tag_val = [kv_pairs[i][1] for i in range(len(kv_pairs))]
    #     else:
    #         tag_val = kv_pairs[0][1]
    #         tag_val = text_parser_get(tag_val)

        if Empty.is_empty(tag_val):
            tag_val = Empty()

        # val = text_parser_get(tag_val)
        # if len(val) == 1:
        #     val = val[0]
        dict_data[tag_key] = tag_val

    return dict_dummy
