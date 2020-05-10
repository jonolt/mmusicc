#  Copyright (c) 2020 Johannes Nolte
#  SPDX-License-Identifier: GPL-3.0-or-later

from distutils.dir_util import copy_tree
from distutils.file_util import copy_file

import pytest

import mmusicc
import mmusicc.formats
import mmusicc.util
import mmusicc.util.allocationmap
from ._util import *


@pytest.fixture(scope="session")
def dir_orig_data() -> pathlib.Path:
    return pathlib.Path(__file__).parent.joinpath("data")


@pytest.fixture(scope="module")
def allocation_map(request, dir_orig_data):
    if request.fspath.basename == "test_formats.py":
        path_config = "metadata_config.yaml"
    else:
        path_config = dir_orig_data.parent.parent.joinpath("mmusicc/data/config.yaml")
    abs_path = str(dir_orig_data.joinpath(path_config))
    mmusicc.util.init_allocationmap(abs_path, force=True)
    # equals: init_allocationmap(path_config)
    return mmusicc.util.allocationmap


@pytest.fixture(scope="session")
def audio_loaders() -> dict:
    mmusicc.formats.init()
    # trigger skipping of initialisation
    mmusicc.formats.init()
    # equals: init_formats()
    return mmusicc.formats.loaders


@pytest.fixture(scope="session")
def dir_tmp_root(tmp_path_factory):
    return tmp_path_factory.getbasetemp()


@pytest.fixture(scope="session")
def dir_subpackages(tmp_path_factory, dir_orig_data) -> pathlib.Path:
    files = [p.name for p in dir_orig_data.glob("*.*")]
    temp_dir = tmp_path_factory.mktemp("subpackages", numbered=False)
    for file in files:
        file_source = dir_orig_data.joinpath(file)
        copy_file(str(file_source), str(temp_dir))
    return temp_dir


@pytest.fixture(scope="session")
def path_database(dir_subpackages):
    return dir_subpackages.joinpath("database.db")


@pytest.fixture(scope="function")
def temp_database(tmp_path_factory):
    return tmp_path_factory.mktemp("fuu").joinpath("database.db")


@pytest.fixture(scope="function")
def dir_lib_x_flac(tmp_path_factory, dir_orig_data):
    temp_dir = tmp_path_factory.mktemp("lib_x_")
    s_path = dir_orig_data.joinpath("music_lib_x_flac")
    copy_tree(str(s_path), str(temp_dir))
    return temp_dir


@pytest.fixture(scope="session")
def dir_lib_a_flac(tmp_path_factory, dir_orig_data):
    # original flac data do not overwrite
    temp_dir = tmp_path_factory.mktemp("A_flac", numbered=True)
    s_path = dir_orig_data.joinpath("music_lib", "A_flac")
    copy_tree(str(s_path), str(temp_dir))
    save_info = save_files_hash_and_mtime(temp_dir, touch=True)
    yield temp_dir
    # make sure that the original file was not changed
    assert cmp_files_hash_and_time(temp_dir, save_info) == 12


@pytest.fixture(scope="session")
def dir_lib_b_ogg(tmp_path_factory, dir_orig_data):
    # original mp3 data do not overwrite (to be compared with result)
    temp_dir = tmp_path_factory.mktemp("B_ogg", numbered=False)
    s_path = dir_orig_data.joinpath("music_lib", "B_ogg")
    copy_tree(str(s_path), str(temp_dir))
    return temp_dir


@pytest.fixture(scope="session")
def dir_lib_c_ogg(tmp_path_factory, dir_orig_data):
    # lib with missing and wrong metadata
    temp_dir = tmp_path_factory.mktemp("C_ogg", numbered=False)
    s_path = dir_orig_data.joinpath("music_lib", "C_ogg")
    copy_tree(str(s_path), str(temp_dir))
    return temp_dir


@pytest.fixture(scope="function")
def dir_lib_test(tmp_path_factory):
    return tmp_path_factory.mktemp("libt_")
