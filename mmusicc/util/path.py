import os

DIRNAME = '__dirname'
DIRPATH = '__dirpath'
EXTENSION = '__ext'
FILENAME = "__filename"
FILENAME_NO_EXT = '__filename_no_ext'
PARENT_DIR = '__parent_dir'
PATH = "__path"

FILETAGS = [PATH, FILENAME, EXTENSION, DIRPATH, DIRNAME, FILENAME_NO_EXT,
            PARENT_DIR]

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
