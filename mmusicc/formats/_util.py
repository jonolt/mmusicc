from mmusicc.metadata import Empty
from mmusicc.util.allocationmap import dict_str_tags


def scan_dictionary(dict_tags, dict_data, ignore_none=False):

    dict_dummy = dict_tags.copy()
    dict_dummy = {k.casefold(): v for k, v in dict_dummy.items()}

    dict_tmp = dict()

    for key_str in list(dict_dummy):
        try:
            key = dict_str_tags[key_str]
        except KeyError:
            continue
        try:
            val = dict_dummy.pop(key_str)
            if val:
                dict_tmp[key] = [(key_str, val)]
        except KeyError:
            continue

    for key, kv_pairs in dict_tmp.items():
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
                        print(
                            "dropped duplicate pair {}:{}"
                            + ", cheeping {}:{}"
                            .format(kv_pairs[i][1], kv_pairs[i][2],
                                    kv_pairs[j][1], kv_pairs[j][2]))
                        kv_pairs.remove(kv_pairs[i])
                    j += 1
                i += 1
            val = [kv_pairs[i][1] for i in range(len(kv_pairs))]
        else:
            val = kv_pairs[0][1]
            val = text_parser_get(val)

        if Empty.is_empty(val):
            val = Empty()

        if ignore_none and Empty.is_empty(val):
            continue

        dict_data[key] = val

    return dict_dummy


def text_parser_get(text):
    if isinstance(text, list):
        tmp_text = list()
        for t in text:
            tmp_text.append(text_parser_get(t))
        return tmp_text
    elif isinstance(text, str):
        # TODO replace char list with constant
        for c in ['|', '\n']:
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
