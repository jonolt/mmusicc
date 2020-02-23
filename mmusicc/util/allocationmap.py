import os

import yaml

list_tui_tags = list()
list_tags = list()
dict_tag_id3 = dict()  # id3 from tag
dict_id3_tag = dict()  # tag from id3
dict_strs_tag = dict()  # tags (as list) from str
dict_tag_str = dict()  # str from tags
dict_auto_fill_rules = dict()


def init_allocationmap(path):
    """initialize allocation map from config file.

    Creates dicts as lookup tables as global variables.

    Args:
        path (str): path of yaml file containing the allocation table
    """

    global list_tui_tags
    global list_tags
    global dict_tag_id3
    global dict_id3_tag
    global dict_strs_tag
    global dict_tag_str
    global dict_auto_fill_rules

    path = os.path.abspath(os.path.expanduser(path))
    if not os.path.exists(path):
        raise FileNotFoundError("config file not found '{}'".format(path))
    with open(path, 'r') as f:
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
        dict_tag_id3[key] = id3_tag
        dict_id3_tag[id3_tag] = key
        strings = []
        if key not in assertions:
            strings.append(key)
        for val in assertions:
            strings.append(val)
        dict_strs_tag[key] = strings
        for string in strings:
            dict_tag_str[string] = key

    i = len(list_tui_tags) - 1
    while list_tui_tags[i] is None:
        list_tui_tags.pop(i)
        i -= 1
