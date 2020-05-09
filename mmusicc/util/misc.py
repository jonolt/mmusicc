import logging
import mimetypes
import pathlib

import mmusicc.util.allocationmap as am
from mmusicc.formats import mimes


def is_supported_audio(file):
    """Return True if file is a supported audio file."""
    mimetype = mimetypes.guess_type(str(file))

    if mimetype[0] in mimes:
        return True
    else:
        return False


def process_white_and_blacklist(whitelist, blacklist):
    """creates a whitelist from one whitelist and one blacklist.

    Blacklist is processed after whitelist and will remove whitelisted
    items.

    Args:
        whitelist (list of str): whitelist of tags to be imported. Loads all
            tags if None.
        blacklist (list of str): blacklist of tags not to be imported. These
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
                logging.warning(
                    "Warning can not remove {}. "
                    "It is not in the whitelist.".format(t)
                )
                continue
    return whitelist


def swap_base(root_a, path_a, root_b):
    """removes the root part of path_a and attaches the remainder to root
    of root_b crating path_b.

    Args:
        root_a (pathlib.Path): Root path of a.
        path_a (pathlib.Path): Full path of a.
        root_b (pathlib.Path): Root path of b.

    Returns:
        (pathlib.Path): Full path of path_b.

    """
    relative_path = path_a.relative_to(root_a)
    path_b = root_b.joinpath(relative_path)
    return path_b


def get_the_right_one(list_path, match_path, drop_suffix=True):
    """return the most matching path out of a list of (absolute) paths

    with has the most common elements beginning at the leaves of the tree.
    Basically finds matching relative paths with unknown working directory.
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
        match_path = match_path.with_suffix("")

    match_parts = match_path.parts

    i = 0
    while len(list_path) > 1:
        i += 1
        list_new = list()
        for path in list_path:
            if path.with_suffix("").parts[-i] == match_parts[-i]:
                list_new.append(path)
            else:
                pass
        list_path = list_new

        if i > 100:
            raise Exception("loop count to high")

    if len(list_path) == 0:
        raise KeyError("could not find matching entry")

    return list_path[0]
