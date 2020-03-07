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
