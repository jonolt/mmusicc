"""
Definitions for this documentation:

- TAG
    string of tag used in program (e.g. MetadataDict), also TAG display name.
- STRING(s)
    string used in the files for the TAGS. Can be a list to match
    different variants (e.g. comment, description).
- ID3
    frame names of ID3 tag standard


Attributes:
    list_tags     (list of tags): list of all recognized TAGs.
    dict_tag2id3          (dict): dict mapping TAG to ID3.
    dict_id32tag          (dict): dict mapping ID3 to TAG.
    dict_tag2strs         (dict): dict mapping TAG to STRING(s).
    dict_str2tag          (dict): dict mapping STRING to TAG.

"""


import logging
import os

import yaml

list_tui_tags = list()
list_tags = list()
dict_tag2id3 = dict()  # tag: id3
dict_id32tag = dict()  # id3: tag
dict_tag2strs = dict()  # tag: strs (list)
dict_str2tag = dict()  # str: tag
dict_auto_fill_rules = dict()


def init_allocationmap(path, force=False):
    """Initialize allocation map from config file.

    Creates dicts as lookup tables as global variables.

    Args:
        path             (str): path of yaml file containing a mapping for
            the allocation table
        force (bool, optional): if True, initializes the allocationmap even if
            it is already initialized, otherwise skips. Defaults to False.
    """

    global list_tui_tags
    global list_tags
    global dict_tag2id3
    global dict_id32tag
    global dict_tag2strs
    global dict_str2tag
    global dict_auto_fill_rules

    if len(list_tags) > 0:
        if force:
            logging.debug(
                "allocationmap Already Initialized, " "Continue (force option set)."
            )
            # reset all lists and dicts
            list_tui_tags = list()
            list_tags = list()
            dict_tag2id3 = dict()
            dict_id32tag = dict()
            dict_tag2strs = dict()
            dict_str2tag = dict()
            dict_auto_fill_rules = dict()
        else:
            logging.debug("allocationmap Already Initialized, Skipping.")
            return

    path = os.path.abspath(os.path.expanduser(path))
    if not os.path.exists(path):
        raise FileNotFoundError("config file not found '{}'".format(path))
    with open(path, "r") as f:
        dict_config = yaml.safe_load(f)
    max_pos = max(dict_config.values(), key=lambda x: int(x[0]))[0]
    if len(list_tui_tags) < max_pos:
        list_tui_tags = [None] * max_pos
    for key, value in dict_config.items():
        key = key.casefold()
        pos = value[0]
        id3_tag = value[1]
        if len(value) >= 3:
            assertions = set([v.casefold() for v in value[2]])
        else:
            assertions = set()
        if len(value) >= 4:
            if value[3]:
                if len(value[3]) == 3:
                    value[3][0] = value[3][0].casefold()
                    if not value[3][1]:
                        value[3][2] = value[3][2].casefold()
                dict_auto_fill_rules[key] = value[3]
        if len(value) >= 5:
            # placeholder for additional future
            pass

        list_tags.append(key)
        list_tui_tags[pos - 1] = key
        dict_tag2id3[key] = id3_tag
        dict_id32tag[id3_tag] = key
        strings = []
        if key not in assertions:
            strings.append(key)
        for val in assertions:
            strings.append(val)
        dict_tag2strs[key] = strings
        for string in strings:
            dict_str2tag[string] = key

    i = len(list_tui_tags) - 1
    while list_tui_tags[i] is None:
        list_tui_tags.pop(i)
        i -= 1

    logging.debug("allocationmap Initialized, found tags: {}".format(list_tags))


def get_tags_from_strs(tags):
    """Convert a list of STRING(s) to list of TAGs.

    Args:
        tags (list of str): STRING(s).

    Returns:
        list of str: TAGs.
    """
    ret_tag = list()
    for string in tags:
        try:
            ret_tag.append(dict_str2tag[string])
        except KeyError:
            raise KeyError(
                "String '{}' could not be associated with any tag.".format(string)
            )
    return ret_tag
