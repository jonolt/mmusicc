import hashlib
import pathlib
from distutils.dir_util import copy_tree

import pytest

from mmusicc import MmusicC
from mmusicc.util.ffmpeg import FFRuntimeError


class Ste:

    def __init__(self, combo, path_s, path_t, path_e, add_args=None):
        self.combo = combo
        self.path_s = path_s
        self.path_t = path_t
        self.path_e = path_e
        self.add_args = add_args


@pytest.fixture
def ste(request, dir_lib_a_flac, dir_lib_test, dir_lib_b_mp3, dir_lib_c_mp3):
    #            session         function      session
    combo = request.param
    if combo == "file-->file":
        return Ste(
            combo,
            dir_lib_a_flac.joinpath(
                "artist_quodlibet/album_bar_-_single_(2020)/01_track1.flac"),
            dir_lib_test.joinpath("01_track1.mp3"),
            dir_lib_b_mp3.joinpath(
                "artist_quodlibet/album_bar_-_single_(2020)/01_track1.mp3"),
        )
    elif combo == "file-->folder":
        return Ste(
            combo,
            dir_lib_a_flac.joinpath(
                "artist_quodlibet/album_bar_-_single_(2020)/01_track1.flac"),
            dir_lib_test,
            dir_lib_b_mp3.joinpath(
                "artist_quodlibet/album_bar_-_single_(2020)/01_track1.mp3"),
        )
    elif combo == "folder-->folder":
        return Ste(
            combo,
            dir_lib_a_flac,
            dir_lib_test,
            dir_lib_b_mp3
        )
    elif combo == "album-->album":
        return Ste(
            combo,
            dir_lib_a_flac.joinpath("artist_puddletag"),
            dir_lib_test,
            dir_lib_b_mp3.joinpath("artist_puddletag"),
            "--album"
        )
    elif combo == "folder-->folder_part":
        # folder with missing files and wrong mata to be updated
        copy_tree(str(dir_lib_c_mp3), str(dir_lib_test))
        return Ste(
            combo,
            dir_lib_a_flac,
            dir_lib_test,
            dir_lib_b_mp3
        )
    else:
        raise ValueError("combo does not exists")


@pytest.mark.parametrize("ste", ["file-->file"], indirect=True)
class TestConversionFileFile:

    @pytest.mark.parametrize("opt_format", ["mp3", "ogg"])
    def test_option_format(self, ste, opt_format):
        # not tested if format can be neglected at file-->file
        run_mmusicc("--only-files",
                    "-s", ste.path_s,
                    "-t", ste.path_t,
                    "-f", opt_format)
        # both cases are converted to mp3 since -f is ignored and the extension
        # is known from the target
        assert pathlib.Path(ste.path_t).is_file()

    def test_ffmpeg_options(self, ste):
        run_mmusicc("--only-files",
                    "-s", ste.path_s,
                    "-t", ste.path_t,
                    # byte objects are not splited but converted to string
                    "--ffmpeg-options", b"-q:a 9",
                    "-f", ".mp3")
        assert pathlib.Path(ste.path_t).is_file()
        # maybe test file size or conversion result

    def test_catch_ffmpeg_error(self, ste):
        with pytest.raises(FFRuntimeError):
            run_mmusicc("--only-files",
                        "-s", ste.path_s,
                        "-t", ste.path_t,
                        # byte objects are not splited but converted to string
                        "--ffmpeg-options", b"-q: fuubar")


@pytest.mark.parametrize("ste", ["file-->folder"], indirect=True)
class TestConversionFileFolder:

    @pytest.mark.parametrize("opt_format", ["mp3", "ogg", ".ogg"])
    def test_option_format(self, ste, opt_format):
        # both extension with and without leading dot can be used
        run_mmusicc("--only-files",
                    "-s", ste.path_s,
                    "-t", ste.path_t,
                    "-f", opt_format)
        if not opt_format == ".ogg":
            opt_format = "." + opt_format
        target_file = ste.path_s.stem + opt_format
        assert pathlib.Path(ste.path_t).joinpath(target_file).is_file()


logic_params = ["folder-->folder", "album-->album", "folder-->folder_part"]


@pytest.mark.parametrize("ste", logic_params, indirect=True)
class TestTreeLogic:

    def test_tree_logic(self, ste):
        org_file_list, _ = get_file_list_tree(ste.path_t)
        saved_file_info = save_files_hash_and_mtime(org_file_list, touch=True)
        run_mmusicc("--only-files",
                    "-s", ste.path_s,
                    "-t", ste.path_t,
                    "-f", ".mp3",
                    ste.add_args)

        if ste.combo == "album-->album":
            compare_file_tree(ste.path_t, ste.path_e, depth=1)
            assert ste.path_t.joinpath("audio_at_artist_level.mp3").is_file()
            assert not ste.path_t.joinpath("album_good_(2018)").exists()
        elif ste.combo == "folder-->folder_part":
            compare_file_tree(ste.path_t, ste.path_e)
            compare_files_hash_and_mtime(org_file_list, saved_file_info)
        else:
            compare_file_tree(ste.path_t, ste.path_e)


def save_files_hash_and_mtime(list_files, touch=False) -> dict:
    # save hashes to be used in compare_files_hash and mtime
    # touches files before getting time when touch=True
    hash_dict = dict()
    for file in list_files:
        if touch:
            file.touch()
        hash_dict[file] = (hash_file(file), file.stat().st_mtime)
    return hash_dict


def compare_files_hash_and_mtime(list_files, hash_dict):
    try:
        for file in list_files:
            # file has changed (content or metadata)
            assert hash_dict.get(file)[0] == hash_file(file)
            # file was accessed (or overwritten with original)
            assert hash_dict.get(file)[1] == file.stat().st_mtime
    except KeyError:
        raise Exception("hash dict not complete, key can not be checked")


def hash_file(path):
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


def get_file_list_tree(tree_root, depth=None):
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

    return files, base_length


def compare_file_tree(tree_a, tree_b, depth=None):

    files_a, base_length_a = get_file_list_tree(tree_a, depth=depth)
    files_b, base_length_b = get_file_list_tree(tree_b, depth=depth)

    for i in range(len(files_a)):
        com_parts_a = files_a[i].parts[base_length_a:]
        com_parts_b = files_b[i].parts[base_length_b:]
        assert com_parts_a == com_parts_b
    return files_a, files_b


def test_compare_tree(dir_lib_b_mp3, dir_lib_c_mp3):
    files_a, files_b = compare_file_tree(dir_lib_b_mp3, dir_lib_b_mp3)
    assert len(files_a) == 10
    assert len(files_b) == 10
    files_a, files_b = compare_file_tree(dir_lib_b_mp3, dir_lib_b_mp3, 2)
    assert len(files_a) == 1
    assert len(files_b) == 1
    with pytest.raises(AssertionError):
        compare_file_tree(dir_lib_c_mp3, dir_lib_b_mp3)


def cmd_mmusicc(*args):
    final_cmd = list()
    if isinstance(args, pathlib.Path):
        args = str(args)
    for arg in args:
        if isinstance(arg, str):
            if arg == "":
                continue
            final_cmd.extend(arg.split())
        elif isinstance(arg, bytes):
            final_cmd.append(arg.decode())
        elif isinstance(arg, pathlib.Path):
            final_cmd.append(str(arg))
        elif arg is None:
            continue
        else:
            for a in arg:
                final_cmd.extend(cmd_mmusicc(a))
    return final_cmd


def run_mmusicc(*args):
    with pytest.raises(SystemExit) as excinfo:
        MmusicC(cmd_mmusicc(*args))
    assert excinfo.value.code == 0


def test_cmd_mmusicc():
    cmd = cmd_mmusicc("-fuu bar", ["--Hello", "World"], ["-qood libet"])
    assert cmd == ['-fuu', 'bar', '--Hello', 'World', '-qood', 'libet']
