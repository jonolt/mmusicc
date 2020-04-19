import hashlib
import pathlib


def assert_compare_files_metadata(file_a, file_b):
    pass


def save_files_hash_and_mtime(list_files, touch=False) -> dict:
    """save hashes to be used in compare_files_hash and mtime
        touches files before getting time when touch=True
    """
    if not isinstance(list_files, list):
        list_files = [list_files]
    hash_dict = dict()
    for file in list_files:
        file = pathlib.Path(file)
        if touch:
            file.touch()
        hash_dict[file] = (hash_file(file),
                           file.stat().st_mtime,
                           file.stat().st_atime)
    return hash_dict


def cmp_files_hash_and_time(list_files, hash_dict):
    """compares hashes and mtime to check if file was changed. Counts changed
        files (changed hash adds +1, changed mtime adds +100 to result)
    """
    if not isinstance(list_files, list):
        list_files = [list_files]
    try:
        exit_code = 0
        for file in list_files:
            file = pathlib.Path(file)
            # file has changed (content or metadata) (and was also accessed)
            if not hash_dict.get(file)[0] == hash_file(file):
                exit_code += 10000
            # file was accessed (or overwritten with original)
            if not hash_dict.get(file)[1] == file.stat().st_mtime:
                exit_code += 100
            if not hash_dict.get(file)[1] == file.stat().st_atime:
                exit_code += 1
        return exit_code
    except KeyError:
        raise Exception("hash dict not complete, key can not be checked")


def hash_file(path) -> str:
    """return sha1 hash of file"""
    # noinspection PyPep8Naming
    BUF_SIZE = 65536  # 64kb
    sha1 = hashlib.sha1()
    with open(path, 'rb') as f:
        while True:
            data = f.read(BUF_SIZE)
            if not data:
                break
            sha1.update(data)
    return sha1.hexdigest()
