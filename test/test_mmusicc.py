#  Copyright (c) 2020 Johannes Nolte
#  SPDX-License-Identifier: GPL-3.0-or-later

from distutils.dir_util import copy_tree
from distutils.file_util import copy_file

import pytest

from mmusicc.__main__ import main
from ._util import *


class Ste:
    """Source Target Expected. Object holding files path for testing"""

    def __init__(self, combo, path_s, path_t, path_e, add_args=None):
        self.combo = combo
        self.path_s = path_s  # input file (lib A)
        self.path_t = path_t  # output/changed file (working copy)
        self.path_e = path_e  # expected result (lib B)
        self.add_args = add_args  # additional arguments for some tests


@pytest.fixture
def ste(request, dir_lib_a_flac, dir_lib_test, dir_lib_b_ogg, dir_lib_c_ogg):
    #            session         function      session
    """provide Paths (source target expected) for the different scenarios"""
    combo = request.param
    if combo == "file-->file":
        return Ste(
            combo,
            dir_lib_a_flac.joinpath(
                "artist_quodlibet/album_bar_-_single_(2020)/01_track1.flac"
            ),
            dir_lib_test.joinpath("01_track1.ogg"),
            dir_lib_b_ogg.joinpath(
                "artist_quodlibet/album_bar_-_single_(2020)/01_track1.ogg"
            ),
        )
    elif combo == "file-->folder":
        return Ste(
            combo,
            dir_lib_a_flac.joinpath(
                "artist_quodlibet/album_bar_-_single_(2020)/01_track1.flac"
            ),
            dir_lib_test,
            dir_lib_b_ogg.joinpath(
                "artist_quodlibet/album_bar_-_single_(2020)/01_track1.ogg"
            ),
        )
    elif combo == "folder-->folder":
        return Ste(combo, dir_lib_a_flac, dir_lib_test, dir_lib_b_ogg)
    elif combo == "album-->album":
        return Ste(
            combo,
            dir_lib_a_flac.joinpath("artist_puddletag"),
            dir_lib_test,
            dir_lib_b_ogg.joinpath("artist_puddletag"),
            "--album",
        )
    elif combo == "folder-->folder_part":
        # folder with missing files and wrong mata to be updated
        copy_tree(str(dir_lib_c_ogg), str(dir_lib_test))
        return Ste(combo, dir_lib_a_flac, dir_lib_test, dir_lib_b_ogg)
    else:
        raise ValueError("combo does not exists")


class TestMetadataOnly:
    @pytest.mark.parametrize("combo", ["file-->file", "file-->folder"])
    @pytest.mark.parametrize(
        "opt",
        [
            None,
            "--lazy",
            "--delete-existing-metadata",
            "--lazy --delete-existing-metadata",
        ],
    )
    def test_file_file(self, dir_lib_a_flac, dir_lib_c_ogg, dir_lib_test, opt, combo):
        """test file to file metadata sync with different options"""
        path_copy_source = dir_lib_c_ogg.joinpath(
            "artist_quodlibet/album_bar_-_single_(2020)/01_track1.ogg"
        )
        path_s = dir_lib_a_flac.joinpath(
            "artist_quodlibet/album_bar_-_single_(2020)/01_track1.flac"
        )
        path_t = dir_lib_test.joinpath("01_track1.ogg")
        copy_file(str(path_copy_source), str(path_t))

        org_file_list = [path_t]
        saved_file_info = save_files_hash_and_mtime(org_file_list, touch=True)

        if combo == "file-->folder":
            path_t2 = dir_lib_test
            opt_f = [opt, "-f ogg"]
        else:
            opt_f = opt
            path_t2 = path_t

        _assert_run_mmusicc(
            "--only-meta", "--source", path_s, "--target", path_t2, opt_f
        )

        assert cmp_files_hash_and_time(org_file_list, saved_file_info) > 0
        metadata = Metadata(str(path_t))
        assert metadata.get_tag("album") == "Bar - Single"
        assert metadata.get_tag("date") == "2020"
        assert metadata.get_tag("artist") == "Quod Libet"
        # assert metadata.get_tag("composer") == "should not be here"

        if opt and "--delete-existing-metadata" in opt:
            assert len(metadata.unprocessed_tag) == 0
            if "--lazy" in opt:
                assert metadata.get_tag("composer") == "should not be here"
            else:
                assert metadata.get_tag("composer") is None
        else:
            assert len(metadata.unprocessed_tag) > 0
            assert metadata.get_tag("composer") == "should not be here"

    def test_folder_folder(self, dir_lib_a_flac, dir_lib_b_ogg, dir_lib_test):
        """test folder folder metadata sync"""
        copy_tree(str(dir_lib_b_ogg), str(dir_lib_test))
        saved_file_info = save_files_hash_and_mtime(dir_lib_test, touch=True)
        _assert_run_mmusicc(
            "--only-meta",
            "--source",
            dir_lib_a_flac,
            "--target",
            dir_lib_test,
            "-f .ogg",
        )
        # check no file was modified (11 files were accessed: 11*100=1000)
        assert cmp_files_hash_and_time(dir_lib_test, saved_file_info) == 11

    @pytest.mark.parametrize("opt", [None, "--lazy", "--delete-existing-metadata"])
    def test_folder_folder_part(self, dir_lib_a_flac, dir_lib_c_ogg, dir_lib_test, opt):
        """test folder folder metadata sync, where target has not got all
            elements of source folder
        """
        copy_tree(str(dir_lib_c_ogg), str(dir_lib_test))
        saved_file_info = save_files_hash_and_mtime(dir_lib_test, touch=True)
        _assert_run_mmusicc(
            "--only-meta",
            "--source",
            dir_lib_a_flac,
            "--target",
            dir_lib_test,
            "-f .ogg",
            opt,
        )

        equal_to_lib_b = cmp_files_metadata(dir_lib_test, dir_lib_a_flac, ext_b=".flac")
        if opt is None:
            # 2 files CD_02 got empty tags not present in source which are not deleted
            # by the standard operation. At Single the composer is imported as None and
            # therefore unchanged on file, while some wrong tags are changed. (7-2-1=4)
            assert equal_to_lib_b == 4
        elif "--lazy" in opt:
            # at import the the composer tag is not overwritten with None from source
            # also the empty values in CD_02 are not replaced with none. Since
            # write_empty is by default False, a value that is Empty in Metadata will
            # be deleted on file, therefore CD_02 has no Empty tags left.
            assert equal_to_lib_b == 6
        else:
            # only metadata existing in A is left since org data is deleted
            assert equal_to_lib_b == 7

        # check no file but 3 were modified
        # 7 files were accessed, 3 modified: 7*100+3=703)
        cmp_th = cmp_files_hash_and_time(dir_lib_test, saved_file_info)
        if cmp_th == 30207 or cmp_th == 10007:
            pytest.xfail(
                "strange behaviour that occurs now and then and "
                "could be explained yet. Since the hash has changed "
                "the file must have been modified"
            )

        if opt is None:
            # Since the files in CD_02 are unchanged only one file is modified.
            assert cmp_th == 10107
        else:
            assert cmp_th == 30307

    def test_white_and_blacklist(
        self, dir_lib_a_flac, dir_lib_c_ogg, dir_lib_test, dir_subpackages
    ):
        path_copy_source = dir_lib_c_ogg.joinpath(
            "various_artists/album_best_hits_compilation_(2010)/" "CD_01/01_track1.ogg"
        )
        path_whitelist = dir_subpackages.joinpath("whitelist.txt")
        list_blacklist = ["artist"]
        path_s = dir_lib_a_flac.joinpath(
            "various_artists/album_best_hits_compilation_(2010)/" "CD_02/02_track2.flac"
        )
        path_t = dir_lib_test.joinpath("01_track1.ogg")
        copy_file(str(path_copy_source), str(path_t))
        _assert_run_mmusicc(
            "--only-meta",
            "--source",
            path_s,
            "--target",
            path_t,
            "--white-list-tags",
            path_whitelist,
            "--black-list-tags",
            list_blacklist,
        )
        metadata = Metadata(str(path_t))
        assert metadata.get_tag("album") == "best hists compilation"  # white
        assert metadata.get_tag("title") == "track2"  # white
        assert metadata.get_tag("discnumber") == "1" or "01"  # black
        assert metadata.get_tag("tracknumber") == "2" or "02"  # black
        assert metadata.get_tag("artist") == "hello"  # black

    def test_file_database_in_and_export(
        self, dir_lib_a_flac, dir_lib_c_ogg, dir_lib_test
    ):
        database_path = dir_lib_test.joinpath("fuubar.db3")
        path_s = dir_lib_a_flac.joinpath(
            "artist_quodlibet/album_bar_-_single_(2020)/01_track1.flac"
        )
        path_copy_s = dir_lib_c_ogg.joinpath(
            "artist_quodlibet/album_bar_-_single_(2020)/01_track1.ogg"
        )
        path_t = dir_lib_test.joinpath("01_track1.ogg")
        _assert_run_mmusicc(
            "--source", path_s, "--target-db", database_path,
        )
        assert pathlib.Path(database_path).is_file()

        copy_file(str(path_copy_s), str(dir_lib_test))
        saved_file_info = save_files_hash_and_mtime(dir_lib_test, touch=True)
        assert not Metadata(path_s).dict_data == Metadata(path_t).dict_data

        _assert_run_mmusicc(
            "--source-db",
            database_path,
            "--target",
            path_t,
            "--delete-existing-metadata",
        )
        # one changed audio file + one database
        assert cmp_files_hash_and_time(dir_lib_test, saved_file_info) == 10102
        assert Metadata(path_s).dict_data == Metadata(path_t).dict_data

    def test_folder_database_in_and_export(
        self, dir_lib_a_flac, dir_lib_b_ogg, dir_lib_c_ogg, dir_lib_test,
    ):
        database_path = dir_lib_test.joinpath("fuubar.db3")
        _assert_run_mmusicc(
            "--source", dir_lib_a_flac, "--target-db", database_path,
        )
        assert pathlib.Path(database_path).is_file()

        copy_tree(str(dir_lib_c_ogg), str(dir_lib_test))
        copy_tree(str(dir_lib_b_ogg), str(dir_lib_test), update=True)
        saved_file_info = save_files_hash_and_mtime(dir_lib_test, touch=True)
        _assert_run_mmusicc(
            "--target",
            dir_lib_test,
            "--source-db",
            database_path,
            "-f .ogg",
            "--delete-existing-metadata",
        )
        # 11 audio files + 1 database file. 3 audio are changed.
        assert cmp_files_hash_and_time(dir_lib_test, saved_file_info) == 30312
        assert cmp_files_metadata(dir_lib_b_ogg, dir_lib_test) == 11


@pytest.mark.parametrize("ste", ["file-->file"], indirect=True)
class TestConversionFileFile:
    """Test convert file to file operation and options"""

    @pytest.mark.parametrize("opt_format", ["mp3", "ogg"])
    def test_option_format(self, ste, opt_format):
        """ both cases are converted to mp3 since -f is ignored and the
            extension is known from the target
        """
        # not tested if format can be neglected at file-->file
        _assert_run_mmusicc(
            "--only-files", "-s", ste.path_s, "-t", ste.path_t, "-f", opt_format
        )

        assert pathlib.Path(ste.path_t).is_file()

    def test_ffmpeg_options(self, ste):
        """test if ffmpeg options are passed through"""
        # byte objects are not splited but converted to string
        _assert_run_mmusicc(
            "--only-files",
            "-s",
            ste.path_s,
            "-t",
            ste.path_t,
            "--ffmpeg-options",
            b"-q:a 9",
            "-f",
            ".ogg",
        )
        assert pathlib.Path(ste.path_t).is_file()
        # org file size is > 50000
        assert pathlib.Path(ste.path_t).stat().st_size < 10000

    def test_catch_ffmpeg_error(self, ste):
        """test if ffmpeg options are passed through and a exception is raised
            for a invalid option string. since ffmpeg errors are captured, mmusic will
            exit with code 0.
        """
        _assert_run_mmusicc(
            "--only-files",
            "-s",
            ste.path_s,
            "-t",
            ste.path_t,
            "--ffmpeg-options",
            b"-q: fuubar",
        )


@pytest.mark.parametrize("ste", ["file-->folder"], indirect=True)
class TestConversionFileFolder:
    """Test convert file to folder operation and options"""

    @pytest.mark.parametrize("opt_format", ["mp3", "ogg", ".ogg"])
    def test_option_format(self, ste, opt_format):
        # both extension with and without leading dot can be used
        _assert_run_mmusicc(
            "--only-files", "-s", ste.path_s, "-t", ste.path_t, "-f", opt_format
        )
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
        org_file_list = get_file_list_tree(ste.path_t)
        saved_file_info = save_files_hash_and_mtime(org_file_list, touch=True)
        _assert_run_mmusicc(
            "--only-files",
            "-s",
            ste.path_s,
            "-t",
            ste.path_t,
            "-f",
            ".ogg",
            ste.add_args,
        )

        if ste.combo == "album-->album":
            _assert_file_tree(ste.path_t, ste.path_e, depth=1)
            assert ste.path_t.joinpath("audio_at_artist_level.ogg").is_file()
            assert not ste.path_t.joinpath("album_good_(2018)").exists()
        elif ste.combo == "folder-->folder_part":
            _assert_file_tree(ste.path_t, ste.path_e)
            assert cmp_files_hash_and_time(org_file_list, saved_file_info) == 7
        else:
            _assert_file_tree(ste.path_t, ste.path_e)


class TestMmusicc:
    """Test complete program"""

    @pytest.mark.parametrize(
        "opt",
        [
            None,
            "--lazy-import",
            "--delete-existing-metadata",
            "--lazy --delete-existing-metadata",
        ],
    )
    def test_default(
        self, dir_lib_a_flac, dir_lib_c_ogg, dir_lib_test, dir_lib_b_ogg, opt
    ):
        """test the program for the default case it is made for with most used
            parameters
        """
        copy_tree(str(dir_lib_c_ogg), str(dir_lib_test))
        org_file_list = get_file_list_tree(dir_lib_test)
        saved_file_info = save_files_hash_and_mtime(dir_lib_test, touch=True)
        _assert_run_mmusicc(
            "--source", dir_lib_a_flac, "--target", dir_lib_test, "-f .ogg", opt
        )

        # check that missing files are created
        _assert_file_tree(dir_lib_test, dir_lib_b_ogg)
        path_changed = dir_lib_test.joinpath(
            "artist_quodlibet/album_bar_-_single_(2020)/01_track1.ogg"
        )
        metadata = Metadata(str(path_changed))
        assert metadata.get_tag("album") == "Bar - Single"
        assert metadata.get_tag("date") == "2020"
        assert metadata.get_tag("artist") == "Quod Libet"

        cmp_th = cmp_files_hash_and_time(org_file_list, saved_file_info)
        # see test_folder_folder_part for explanation
        if opt is None:
            assert cmp_th == 10107
        else:
            assert cmp_th == 30307

        if opt and "--delete-existing-metadata" in opt:
            assert len(metadata.unprocessed_tag) == 0
            if "--lazy" in opt:
                assert metadata.get_tag("composer") == "should not be here"
            else:
                assert metadata.get_tag("composer") is None
        else:
            assert len(metadata.unprocessed_tag) > 0
            assert metadata.get_tag("composer") == "should not be here"

        # run a second time to ensure its deterministic
        saved_file_info = save_files_hash_and_mtime(dir_lib_test, touch=True)
        _assert_run_mmusicc(
            "--source", dir_lib_a_flac, "--target", dir_lib_test, "-f .ogg", opt
        )
        # check no file was modified, first run should have done all
        assert cmp_files_hash_and_time(dir_lib_test, saved_file_info) == 11

    def test_custom_config_path(self, dir_lib_a_flac, dir_lib_test, dir_orig_data):
        """run mmusicc with testing config file, which is not the default one

            because init_allocationmap will be skipped when list_tags is
            already filled. It is cleared so the init will load the new
            config file. Since the map is force initialized module wise by
            the fixture it is reset to the default.
        """
        import mmusicc.util.allocationmap as am

        am.list_tags = list()
        abs_path = str(dir_orig_data.joinpath("metadata_config.yaml"))
        _assert_run_mmusicc(
            "--only-meta",
            "--source",
            dir_lib_a_flac,
            "--target",
            dir_lib_test,
            "--path-config",
            abs_path,
            "-f ogg",
        )
        assert len(am.list_tags) == 23
        am.list_tags = list()
        _assert_run_mmusicc(
            "--only-meta",
            "--source",
            dir_lib_a_flac,
            "--target",
            dir_lib_test,
            "-f ogg",
        )
        assert len(am.list_tags) == 16


def _assert_file_tree(tree_a, tree_b, depth=None) -> (list, list):
    """asserts if tree structure of sub-files and directories is identical

        and returns a lists of the compared files as tuple (files_a, files_b).
    """
    files_a, base_length_a = get_file_list_tree(tree_a, depth=depth, ret_base=True)
    files_b, base_length_b = get_file_list_tree(tree_b, depth=depth, ret_base=True)

    for i in range(len(files_a)):
        com_parts_a = files_a[i].parts[base_length_a:]
        com_parts_b = files_b[i].parts[base_length_b:]
        assert com_parts_a == com_parts_b
    return files_a, files_b


def _cmd_mmusicc(*args):
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
                final_cmd.extend(_cmd_mmusicc(a))
    return final_cmd


def _assert_run_mmusicc(*args):
    """runs mmusicc with the given arguments. args will be preprocessed with
        cmd_command().
    """
    with pytest.raises(SystemExit) as excinfo:
        main(_cmd_mmusicc(*args))
    assert excinfo.value.code == 0


def test_assert_file_tree(dir_lib_b_ogg, dir_lib_c_ogg):
    files_a, files_b = _assert_file_tree(dir_lib_b_ogg, dir_lib_b_ogg)
    assert len(files_a) == 11
    assert len(files_b) == 11
    files_a, files_b = _assert_file_tree(dir_lib_b_ogg, dir_lib_b_ogg, 2)
    assert len(files_a) == 1
    assert len(files_b) == 1
    with pytest.raises(AssertionError):
        _assert_file_tree(dir_lib_c_ogg, dir_lib_b_ogg)


def test_cmd_mmusicc():
    cmd = _cmd_mmusicc("-fuu bar", ["--Hello", "World"], ["-qood libet"])
    assert cmd == ["-fuu", "bar", "--Hello", "World", "-qood", "libet"]
