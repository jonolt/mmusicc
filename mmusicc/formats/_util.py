import os
# from stat import ST_SIZE, ST_MTIME, ST_CTIME, ST_ATIME

from ._constants import *
from ..metadata import Empty

fn_hash = {
    PATH: 'filepath',
    FILENAME: 'filename',
    EXTENSION: 'ext',
    DIRPATH: 'dirpath',
    DIRNAME: 'dirname',
    FILENAME_NO_EXT: 'filename_no_ext',
}


def hash_filename(filename):
    """Returns fn_hash object"""
    h = fn_hash.copy()
    filename = os.path.abspath(os.path.expanduser(filename))
    h[PATH] = filename
    h[FILENAME] = os.path.basename(filename)
    h[FILENAME_NO_EXT], h[EXTENSION] = os.path.splitext(h[FILENAME])
    h[DIRPATH] = os.path.dirname(filename)
    h[DIRNAME] = os.path.basename(h[DIRPATH])
    return h


def scan_dictionary(dict_tags, dict_data, dict_tags_str):

    dict_dummy = dict_tags.copy()
    dict_dummy = {k.casefold(): v for k, v in dict_dummy.items()}

    for key in list(dict_dummy):
        ret_val = []
        ret_key = []
        try:
            possible_keys = dict_tags_str[key]
        except KeyError:
            continue
        for k in possible_keys:
            try:
                val = dict_dummy.pop(k)
                if val:
                    ret_val.append(val)
                    ret_key.append(k)
            except KeyError:
                continue
        if len(ret_val) == 0:
            val = None
        else:
            # take the list and check if entries a double
            if len(ret_val) > 1:
                i = 0
                j = 0
                while i < len(ret_val):
                    while j < len(ret_val):
                        if i == j:
                            j += 1
                            continue
                        if ret_val[i] == ret_val[j]:
                            print(
                                "dropped duplicate pair {}:{}"
                                + ", cheeping {}:{}"
                                .format(ret_val[i], ret_key[i],
                                        ret_val[j],
                                        ret_key[j]))
                            ret_val.remove(ret_val[i])
                        j += 1
                    i += 1
            val = ret_val[0]

        if Empty.is_empty(val):
            val = Empty()

        dict_data[key] = val

    return dict_dummy


def getinfo(filename):
    """Gets file info like file-size etc. from filename.

    Returns a dictionary keys, values as puddletag
    wants it.
    ""

    file_info = stat(filename)
    size = file_info[ST_SIZE]
    accessed = file_info[ST_ATIME]
    modified = file_info[ST_MTIME]
    created = file_info[ST_CTIME]
    return ({
        "__size": size,
        '__file_size': str_filesize(size),
        '__file_size_bytes': unicode(size),
        '__file_size_kb': u'%d KB' % long(size / 1024),
        '__file_size_mb': u'%.2f MB' % (size / 1024.0 ** 2),

        "__created": strtime(created),
        '__file_create_date': get_time('%Y-%m-%d', created),
        '__file_create_datetime':
            get_time('%Y-%m-%d %H:%M:%S', created),
        '__file_create_datetime_raw': unicode(created),

        "__modified": strtime(modified),
        '__file_mod_date': get_time('%Y-%m-%d', modified),
        '__file_mod_datetime':
            get_time('%Y-%m-%d %H:%M:%S', modified),
        '__file_mod_datetime_raw': unicode(modified),

        '__accessed': strtime(accessed),
        '__file_access_date': get_time('%Y-%m-%d', accessed),
        '__file_access_datetime':
            get_time('%Y-%m-%d %H:%M:%S', accessed),
        '__file_access_datetime_raw': unicode(accessed),

    })
    """
    pass


_sizes = {0: 'B', 1: 'KB', 2: 'MB', 3: 'GB'}


def str_filesize(size):
    """Convert size in bytes to it's string representation and returns it.

    >>>str_filesize(1024)
    u'1 KB'
    >>>str_filesize(88)
    u'88 B'
    >>>str_filesize(1024**3)
    u'1.00 GB'
    """
    valid = [z for z in _sizes if size / (1024.0**z) > 1]
    val = max(valid)
    if val < 2:
        return u'%d %s' % (size/(1024**val), _sizes[val])
    else:
        return u'%.2f %s' % (size/(1024.0**val), _sizes[val])
