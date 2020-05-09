import hashlib
import os
import pathlib
import time

from mmusicc import Metadata
from mmusicc.util.misc import swap_base, is_supported_audio


def cmp_files_metadata(base_a, base_b, ext_b=None):
    """return number of files with identical metadata."""
    equals = 0
    for root, dirs, files in os.walk(base_a, topdown=True):
        audio_files = [file for file in files if is_supported_audio(file)]
        for path_a in audio_files:
            path_a = pathlib.Path(root).joinpath(path_a)
            path_b = swap_base(base_a, path_a, base_b)
            if ext_b:
                path_b = path_b.with_suffix(ext_b)
            if Metadata(path_a).dict_data == Metadata(path_b).dict_data:
                equals += 1
    return equals


def save_files_hash_and_mtime(list_files, touch=False) -> dict:
    """save hashes to be used in compare_files_hash and mtime
        touches files before getting time when touch=True
    """
    if not isinstance(list_files, list):
        if os.path.isdir(list_files):
            list_files = get_file_list_tree(list_files)
        else:
            list_files = [list_files]
    hash_dict = dict()
    for file in list_files:
        file = pathlib.Path(file)
        if touch:
            file.touch()
        hash_dict[file] = (hash_file(file), file.stat().st_mtime, file.stat().st_atime)
    return hash_dict


def cmp_files_hash_and_time(list_files, hash_dict):
    """compares hashes and mtime to check if file was changed. Counts changed
        files (changed hash adds +1, changed mtime adds +100 to result)
    """
    if not isinstance(list_files, list):
        if os.path.isdir(list_files):
            list_files = get_file_list_tree(list_files)
        else:
            list_files = [list_files]
    try:
        time.sleep(0.01)
        exit_code = 0
        for file in list_files:
            file = pathlib.Path(file)
            # file has changed (content or metadata) (and was also accessed)
            if not hash_dict.get(file)[0] == hash_file(file):
                exit_code += 10000
                # the file system is not fast enough updating the metadata. Since access
                # seems to be faster and you can only modify a file by accessing it,
                # add a delay to make sure metadata gets updated.
                i = 0
                while i < 10 and hash_dict.get(file)[1] == file.stat().st_mtime:
                    time.sleep(0.02)
                    i += 1
            # file was accessed (or overwritten with original)
            if not hash_dict.get(file)[1] == file.stat().st_atime:
                exit_code += 1
            if not hash_dict.get(file)[1] == file.stat().st_mtime:
                exit_code += 100
        return exit_code
    except KeyError:
        raise Exception("hash dict not complete, key can not be checked")


def hash_file(path) -> str:
    """return sha1 hash of file"""
    # noinspection PyPep8Naming
    BUF_SIZE = 65536  # 64kb
    sha1 = hashlib.sha1()
    with open(path, "rb") as f:
        while True:
            data = f.read(BUF_SIZE)
            if not data:
                break
            sha1.update(data)
    return sha1.hexdigest()


def get_file_list_tree(tree_root, depth=None, ret_base=False):
    """return a list off all files in folder (at given search depth)"""
    if not depth:
        depth = 100
    files = sorted(tree_root.resolve().rglob("*"))
    base_length = len(tree_root.parts)

    max_len_parts_a = base_length + depth
    for i in sorted(range(len(files)), reverse=True):
        if len(files[i].parts) > max_len_parts_a:
            files.pop(i)
        elif files[i].is_dir():
            files.pop(i)
    if ret_base:
        return files, base_length
    return files
