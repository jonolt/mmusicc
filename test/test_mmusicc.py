import hashlib
import pathlib
from distutils.dir_util import copy_tree
from distutils.file_util import copy_file

import pytest

from mmusicc import MmusicC, Metadata
from mmusicc.util.ffmpeg import FFRuntimeError


class Ste:

    def __init__(self, combo, path_s, path_t, path_e, add_args=None):
        self.combo = combo
        self.path_s = path_s
        self.path_t = path_t
        self.path_e = path_e
        self.add_args = add_args


@pytest.fixture
def ste(request, dir_lib_a_flac, dir_lib_test, dir_lib_b_ogg, dir_lib_c_ogg):
    #            session         function      session
    """provide Paths (source target expected) for the different scenarios"""
    combo = request.param
    if combo == "file-->file":
        return Ste(
            combo,
            dir_lib_a_flac.joinpath(
                "artist_quodlibet/album_bar_-_single_(2020)/01_track1.flac"),
            dir_lib_test.joinpath("01_track1.ogg"),
            dir_lib_b_ogg.joinpath(
                "artist_quodlibet/album_bar_-_single_(2020)/01_track1.ogg"),
        )
    elif combo == "file-->folder":
        return Ste(
            combo,
            dir_lib_a_flac.joinpath(
                "artist_quodlibet/album_bar_-_single_(2020)/01_track1.flac"),
            dir_lib_test,
            dir_lib_b_ogg.joinpath(
                "artist_quodlibet/album_bar_-_single_(2020)/01_track1.ogg"),
        )
    elif combo == "folder-->folder":
        return Ste(
            combo,
            dir_lib_a_flac,
            dir_lib_test,
            dir_lib_b_ogg
        )
    elif combo == "album-->album":
        return Ste(
            combo,
            dir_lib_a_flac.joinpath("artist_puddletag"),
            dir_lib_test,
            dir_lib_b_ogg.joinpath("artist_puddletag"),
            "--album"
        )
    elif combo == "folder-->folder_part":
        # folder with missing files and wrong mata to be updated
        copy_tree(str(dir_lib_c_ogg), str(dir_lib_test))
        return Ste(
            combo,
            dir_lib_a_flac,
            dir_lib_test,
            dir_lib_b_ogg
        )
    else:
        raise ValueError("combo does not exists")


class TestMetadataOnly:

    @pytest.mark.parametrize("combo", ["file-->file", "file-->folder"])
    @pytest.mark.parametrize("opt", [None, "--lazy"])
    def test_file_file(self, dir_lib_a_flac, dir_lib_c_ogg,
                       dir_lib_test, opt, combo):
        """test file to file metadata sync with different options"""
        path_copy_source = dir_lib_c_ogg.joinpath(
            "artist_quodlibet/album_bar_-_single_(2020)/01_track1.ogg")
        path_s = dir_lib_a_flac.joinpath(
            "artist_quodlibet/album_bar_-_single_(2020)/01_track1.flac")
        path_t = dir_lib_test.joinpath("01_track1.ogg")
        copy_file(str(path_copy_source), str(path_t))

        org_file_list = [path_t]
        saved_file_info = save_files_hash_and_mtime(org_file_list, touch=True)

        if combo == "file-->folder":
            path_t2 = dir_lib_test
            opt = [opt, "-f ogg"]
        else:
            path_t2 = path_t

        assert_run_mmusicc("--only-meta",
                           "--source", path_s,
                           "--target", path_t2,
                           opt)

        assert cmp_files_hash_and_time(org_file_list, saved_file_info) > 0
        metadata = Metadata(str(path_t))
        assert metadata.get_tag("album") == "Bar - Single"
        assert metadata.get_tag("date") == "2020"
        assert metadata.get_tag("artist") == "Quod Libet"
        assert metadata.get_tag("composer") == "should not be here"

    def test_folder_folder(self, dir_lib_a_flac, dir_lib_b_ogg, dir_lib_test):
        """test folder folder metadata sync"""
        copy_tree(str(dir_lib_b_ogg), str(dir_lib_test))
        org_file_list, _ = get_file_list_tree(dir_lib_test)
        saved_file_info = save_files_hash_and_mtime(org_file_list, touch=True)
        assert_run_mmusicc("--only-meta",
                           "--source", dir_lib_a_flac,
                           "--target", dir_lib_test,
                           "-f .ogg",
                           )
        # check no file was modified (10 files were accessed: 10*100=1000)
        assert cmp_files_hash_and_time(org_file_list, saved_file_info) == 10

    def test_folder_folder_part(self, dir_lib_a_flac, dir_lib_c_ogg,
                                dir_lib_test):
        """test folder folder metadata sync, where target has not got all
            elements of source folder
        """
        copy_tree(str(dir_lib_c_ogg), str(dir_lib_test))
        org_file_list, _ = get_file_list_tree(dir_lib_test)
        saved_file_info = save_files_hash_and_mtime(org_file_list, touch=True)
        assert_run_mmusicc("--only-meta",
                           "--source", dir_lib_a_flac,
                           "--target", dir_lib_test,
                           "-f .ogg"
                           )
        # check no file but 3 were modified
        # 7 files were accessed, 3 modified: 7*100+3=703)
        assert cmp_files_hash_and_time(org_file_list, saved_file_info) == 30307

    def test_white_and_blacklist(self, dir_lib_a_flac, dir_lib_c_ogg,
                                 dir_lib_test, dir_subpackages):
        path_copy_source = dir_lib_c_ogg.joinpath(
            "various_artists/album_best_hits_compilation_(2010)/"
            "CD_01/01_track1.ogg")
        path_whitelist = dir_subpackages.joinpath("whitelist.txt")
        list_blacklist = ["artist"]
        path_s = dir_lib_a_flac.joinpath(
            "various_artists/album_best_hits_compilation_(2010)/"
            "CD_02/02_track2.flac")
        path_t = dir_lib_test.joinpath("01_track1.ogg")
        copy_file(str(path_copy_source), str(path_t))
        assert_run_mmusicc("--only-meta",
                           "--source", path_s,
                           "--target", path_t,
                           "--white-list-tags", path_whitelist,
                           "--black-list-tags", list_blacklist,
                           )
        metadata = Metadata(str(path_t))
        assert metadata.get_tag("album") == "best hists compilation"  # white
        assert metadata.get_tag("title") == "track2"                  # white
        assert metadata.get_tag("discnumber") == "1" or "01"          # black
        assert metadata.get_tag("tracknumber") == "2" or "02"         # black
        assert metadata.get_tag("artist") == "hello"                  # black

    @pytest.mark.skip
    def test_remove_existing(self):
        pass


@pytest.mark.parametrize("ste", ["file-->file"], indirect=True)
class TestConversionFileFile:
    """Test convert file to file operation and options"""

    @pytest.mark.parametrize("opt_format", ["mp3", "ogg"])
    def test_option_format(self, ste, opt_format):
        """ both cases are converted to mp3 since -f is ignored and the
            extension is known from the target
        """
        # not tested if format can be neglected at file-->file
        assert_run_mmusicc("--only-files",
                           "-s", ste.path_s,
                           "-t", ste.path_t,
                           "-f", opt_format)

        assert pathlib.Path(ste.path_t).is_file()

    def test_ffmpeg_options(self, ste):
        """test if ffmpeg options are passed through"""
        # byte objects are not splited but converted to string
        assert_run_mmusicc("--only-files",
                           "-s", ste.path_s,
                           "-t", ste.path_t,
                           "--ffmpeg-options", b"-q:a 9",
                           "-f", ".ogg")
        assert pathlib.Path(ste.path_t).is_file()
        # org file size is > 50000
        assert pathlib.Path(ste.path_t).stat().st_size < 10000

    def test_catch_ffmpeg_error(self, ste):
        """test if ffmpeg options are passed through and a exception is raised
            for a invalid option string
        """
        with pytest.raises(FFRuntimeError):
            # byte objects are not splited but converted to string
            assert_run_mmusicc("--only-files",
                               "-s", ste.path_s,
                               "-t", ste.path_t,
                               "--ffmpeg-options", b"-q: fuubar")


@pytest.mark.parametrize("ste", ["file-->folder"], indirect=True)
class TestConversionFileFolder:
    """Test convert file to folder operation and options"""

    @pytest.mark.parametrize("opt_format", ["mp3", "ogg", ".ogg"])
    def test_option_format(self, ste, opt_format):
        # both extension with and without leading dot can be used
        assert_run_mmusicc("--only-files",
                           "-s", ste.path_s,
                           "-t", ste.path_t,
                           "-f", opt_format)
        if not opt_format == ".ogg":
            opt_format = "." + opt_format
        target_file = ste.path_s.stem + opt_format
        assert pathlib.Path(ste.path_t).joinpath(target_file).is_file()


logic_params = ["folder-->folder", "album-->album", "folder-->folder_part"]


@pytest.mark.parametrize("ste", logic_params, indirect=True)
class TestConversionFolderFolder:
    """Test convert folder to folder operation and options"""

    def test_tree_logic(self, ste):
        """test if the tree in target folder is created correctly"""
        org_file_list, _ = get_file_list_tree(ste.path_t)
        saved_file_info = save_files_hash_and_mtime(org_file_list, touch=True)
        assert_run_mmusicc("--only-files",
                           "-s", ste.path_s,
                           "-t", ste.path_t,
                           "-f", ".ogg",
                           ste.add_args)

        if ste.combo == "album-->album":
            assert_file_tree(ste.path_t, ste.path_e, depth=1)
            assert ste.path_t.joinpath("audio_at_artist_level.ogg").is_file()
            assert not ste.path_t.joinpath("album_good_(2018)").exists()
        elif ste.combo == "folder-->folder_part":
            assert_file_tree(ste.path_t, ste.path_e)
            assert cmp_files_hash_and_time(
                org_file_list, saved_file_info) == 7
        else:
            assert_file_tree(ste.path_t, ste.path_e)


class TestMmusicc:
    """Test complete program"""

    # TODO add test for option --remove-existing-metadata
    @pytest.mark.parametrize("opt", [None, "--lazy"])
    def test_default(self, dir_lib_a_flac, dir_lib_c_ogg, dir_lib_test,
                     dir_lib_b_ogg, opt):
        """test the program for the default case it is made for with most used
            parameters
        """
        copy_tree(str(dir_lib_c_ogg), str(dir_lib_test))
        org_file_list, _ = get_file_list_tree(dir_lib_test)
        saved_file_info = save_files_hash_and_mtime(org_file_list, touch=True)
        assert_run_mmusicc("--source", dir_lib_a_flac,
                           "--target", dir_lib_test,
                           "-f .ogg",
                           opt
                           )

        # check no file but one was modified
        # 7 files were accessed, 3 modified: 7*100+3=703)
        assert cmp_files_hash_and_time(org_file_list, saved_file_info) == 30307
        # check that missing files are created
        assert_file_tree(dir_lib_test, dir_lib_b_ogg)
        path_changed = dir_lib_test.joinpath(
            "artist_quodlibet/album_bar_-_single_(2020)/01_track1.ogg")
        metadata = Metadata(str(path_changed))
        assert metadata.get_tag("album") == "Bar - Single"
        assert metadata.get_tag("date") == "2020"
        assert metadata.get_tag("artist") == "Quod Libet"
        assert metadata.get_tag("composer") == "should not be here"
        # if opt and "--lazy" in opt:
        #     assert metadata.get_tag("composer") == "should not be here"
        # else:
        #     assert Empty.is_empty(metadata.get_tag("composer"))

    def test_custom_config_path(self, dir_lib_a_flac, dir_lib_test,
                                dir_orig_data):
        """run mmusicc with testing config file, which is not the default one

            because init_allocationmap will be skipped when list_tags is
            already filled. It is cleared so the init will load the new
            config file. Since the map is force initialized module wise by
            the fixture it is reset to the default.
        """
        import mmusicc.util.allocationmap as am
        am.list_tags = list()
        abs_path = str(dir_orig_data.joinpath("metadata_config.yaml"))
        assert_run_mmusicc(
            "--only-meta",
            "--source", dir_lib_a_flac,
            "--target", dir_lib_test,
            "--path-config", abs_path,
            "-f ogg"
        )
        assert len(am.list_tags) == 23
        am.list_tags = list()
        assert_run_mmusicc(
            "--only-meta",
            "--source", dir_lib_a_flac,
            "--target", dir_lib_test,
            "-f ogg"
        )
        assert len(am.list_tags) == 15


def save_files_hash_and_mtime(list_files, touch=False) -> dict:
    """save hashes to be used in compare_files_hash and mtime
        touches files before getting time when touch=True
    """
    hash_dict = dict()
    for file in list_files:
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
    try:
        exit_code = 0
        for file in list_files:
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


def get_file_list_tree(tree_root, depth=None) -> (list, int):
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

    return files, base_length


def assert_file_tree(tree_a, tree_b, depth=None) -> (list, list):
    """asserts if tree structure of sub-files and directories is identical

        and returns a lists of the compared files as tuple (files_a, files_b).
    """
    files_a, base_length_a = get_file_list_tree(tree_a, depth=depth)
    files_b, base_length_b = get_file_list_tree(tree_b, depth=depth)

    for i in range(len(files_a)):
        com_parts_a = files_a[i].parts[base_length_a:]
        com_parts_b = files_b[i].parts[base_length_b:]
        assert com_parts_a == com_parts_b
    return files_a, files_b


def test_assert_file_tree(dir_lib_b_ogg, dir_lib_c_ogg):
    files_a, files_b = assert_file_tree(dir_lib_b_ogg, dir_lib_b_ogg)
    assert len(files_a) == 10
    assert len(files_b) == 10
    files_a, files_b = assert_file_tree(dir_lib_b_ogg, dir_lib_b_ogg, 2)
    assert len(files_a) == 1
    assert len(files_b) == 1
    with pytest.raises(AssertionError):
        assert_file_tree(dir_lib_c_ogg, dir_lib_b_ogg)


def cmd_mmusicc(*args):
    """create and return a proper command list from a mixed input list

        strings will be splited at whitespaces, to pass a string like object
        without splitting (eg. for ffmpeg args) pass it as bytes.
    """
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


def assert_run_mmusicc(*args):
    """runs mmusicc with the given arguments. args will be preprocessed with
        cmd_command().
    """
    with pytest.raises(SystemExit) as excinfo:
        MmusicC(cmd_mmusicc(*args))
    assert excinfo.value.code == 0


def test_cmd_mmusicc():
    cmd = cmd_mmusicc("-fuu bar", ["--Hello", "World"], ["-qood libet"])
    assert cmd == ['-fuu', 'bar', '--Hello', 'World', '-qood', 'libet']
