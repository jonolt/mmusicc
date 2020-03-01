import logging

from mmusicc.metadata import Empty
from mmusicc.util.allocationmap import dict_str2tag

SPLIT_CHAR = ['|', '\n', ";"]
JOIN_CHAR = ";"


def join_str_list(str_list):
    """joins a list of strings with a globally defined separator

    used for recombining multiple values in one tag field (e.g. Composer).

    Args:
        str_list (list<str>): list of strings to be joined
    """
    return JOIN_CHAR.join(str_list)


def scan_dictionary(dict_tags, dict_data, ignore_none=False):
    """Scan a dictionary (dict_tags) for tags and fill dict_data with them.

    Args:
        dict_tags             (dict): dictionary (tag_str: value) items to be
            imported.
        dict_data             (dict): dictionary to be filled with imported tag
            values.
        ignore_none (bool, optional): if True, skip emtpy values, otherwise
            write an empty value (Empty Instance). Defaults to False.
    Returns:
        dict<str, str>: dictionary with all tags whose name could not be
            associated with.
    """

    # Make a copy of the source dictionary, so it is unchanged
    dict_dummy = dict_tags.copy()
    dict_dummy = {k.casefold(): v for k, v in dict_dummy.items()}

    dict_tmp = dict()

    # find a tag for each key in scanned dictionary
    for key_str in list(dict_dummy):
        try:
            tag_key = dict_str2tag[key_str]
        except KeyError:
            continue
        try:
            tag_val = dict_dummy.pop(key_str)
            if tag_val:
                if tag_key not in dict_tmp:
                    dict_tmp[tag_key] = list()
                dict_tmp[tag_key].append((key_str, tag_val))
        except KeyError:
            continue

    for tag_key, kv_pairs in dict_tmp.items():
        if len(kv_pairs) > 1:
            # take the list and check if entries a double
            i = 0
            j = 0
            while i < len(kv_pairs):
                while j < len(kv_pairs):
                    if i == j:
                        j += 1
                        continue
                    if kv_pairs[i][1] == kv_pairs[j][1]:
                        logging.info(
                            "dropped duplicate pair {}:{}"
                            ", keeping {}:{}"
                            .format(kv_pairs[i][0], kv_pairs[i][1],
                                    kv_pairs[j][0], kv_pairs[j][1]))
                        kv_pairs.remove(kv_pairs[i])
                    j += 1
                i += 1
            tag_val = [kv_pairs[i][1] for i in range(len(kv_pairs))]
        else:
            tag_val = kv_pairs[0][1]
            tag_val = text_parser_get(tag_val)

        if Empty.is_empty(tag_val):
            tag_val = Empty()

        if ignore_none and Empty.is_empty(tag_val):
            continue

        dict_data[tag_key] = tag_val

    return dict_dummy


def text_parser_get(text):
    """splits a text string at globally defined split chars (recursive).

    Args:
        text (str): source string to be split.
    Returns:
        list<str>: List of strings.
    """
    if isinstance(text, list):
        tmp_text = list()
        for t in text:
            tmp_text.append(text_parser_get(t))
        return tmp_text
    elif isinstance(text, str):
        for c in SPLIT_CHAR:
            tmp_text = text.split(c)
            if len(tmp_text) > 0:
                text = tmp_text
                break
        if len(text) == 1:
            return text[0]
        else:
            return text
    else:
        raise ValueError("text wrong value")
