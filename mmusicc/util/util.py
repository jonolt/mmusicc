from mmusicc.util.metadatadict import Empty

SPLIT_CHAR = ['/', '\n', ';']
JOIN_CHAR = ' ; '


def join_str_list(str_list):
    """joins a list of strings with a globally defined separator

    used for recombining multiple values in one tag field (e.g. Composer).

    Args:
        str_list (list<str>): list of strings to be joined
    """
    return JOIN_CHAR.join(str_list)


def text_parser_get(text):
    """splits a text string at globally defined split chars (recursive).

    Also strips whitespaces from the strings.

    Args:
        text (str or list<str>): source string to be split. Or source list
            which contents to be split.
    Returns:
        str OR list<str>: String when single value in string else list of
            values in string.
    """
    if isinstance(text, list):
        tmp_text = list()
        for t in text:
            tmp_text.append(text_parser_get(t))
        return tmp_text
    elif isinstance(text, str):
        for c in SPLIT_CHAR:
            tmp_text = text.split(c)
            if len(tmp_text) > 1:
                text = tmp_text
                break
        if isinstance(text, str):
            return text.strip()
        elif len(text) == 1:
            return text[0].strip()
        else:
            return [t.strip() for t in text]
    elif isinstance(text, Empty):
        pass
    else:
        raise ValueError("text wrong value")
