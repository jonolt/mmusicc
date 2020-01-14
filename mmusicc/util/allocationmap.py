import yaml
import os


def get_dictionaries(path=None):
    list_tui_tags = list()
    list_tags = list()
    dict_tags_id3 = dict()
    dict_id3_tags = dict()
    dict_tags_str = dict()
    dict_auto_fill_rules = dict()
    dict_test_read = None

    if not path:
        path = os.path.abspath("../config.yaml")

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
        # test answer string
        if len(value) == 6:
            if not dict_test_read:
                dict_test_read = dict()
            dict_test_read[key] = value[5]

        list_tags.append(key)
        list_tui_tags[pos - 1] = key
        dict_tags_id3[key] = id3_tag
        dict_id3_tags[id3_tag] = key
        strings = []
        if key not in assertions:
            strings.append(key)
        for val in assertions:
            strings.append(val)
        dict_tags_str[key] = strings

    i = len(list_tui_tags) - 1
    while list_tui_tags[i] is None:
        list_tui_tags.pop(i)
        i -= 1

    return {
        "dict_config": dict_config,
        "list_tags_sorted": list_tui_tags,
        "list_tags": list_tags,
        "dict_tags_id3": dict_tags_id3,
        "dict_id3_tags": dict_id3_tags,
        "dict_tags_str": dict_tags_str,
        "dict_auto_fill_rules": dict_auto_fill_rules,
        "dict_test_read": dict_test_read,
    }
