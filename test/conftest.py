import pathlib
from distutils.dir_util import copy_tree
from distutils.file_util import copy_file

import pytest

import mmusicc
import mmusicc.formats
import mmusicc.util
import mmusicc.util.allocationmap


@pytest.fixture(scope="session")
def dir_orig_data() -> pathlib.Path:
    return pathlib.Path(__file__).parent.joinpath("data")


@pytest.fixture(scope="module")
def allocation_map(request, dir_orig_data):
    if request.node.name == "test_formats.py":
        path_config = "metadata_config.yaml"
    else:
        path_config = dir_orig_data.parent.parent.\
            joinpath("mmusicc/data/config.yaml")
    mmusicc.util.init_allocationmap(
        str(dir_orig_data.joinpath(path_config)),
        force=True)
    # equals: init_allocationmap(path_config)
    return mmusicc.util.allocationmap


@pytest.fixture(scope="session")
def dir_tmp_root(tmp_path_factory):
    return tmp_path_factory.getbasetemp()


@pytest.fixture(scope="session")
def dir_subpackages(tmp_path_factory, dir_orig_data) -> pathlib.Path:
    files = [p.name for p in dir_orig_data.glob("*.*")]
    temp_dir = tmp_path_factory.mktemp("subpackages", numbered=False)
    for file in files:
        file_source = dir_orig_data.joinpath(file)
        copy_file(file_source, temp_dir)
    return temp_dir


@pytest.fixture(scope="session")
def path_database(dir_subpackages):
    return dir_subpackages.joinpath("database.db")


@pytest.fixture(scope="function")
def temp_database(tmp_path_factory):
    return tmp_path_factory.mktemp("fuu").joinpath("database.db")


@pytest.fixture(scope="function")
def dir_lib_x_flac(tmp_path_factory, dir_orig_data):
    temp_dir = tmp_path_factory.mktemp("lib_x")
    s_path = dir_orig_data.joinpath("music_lib_x_flac")
    copy_tree(str(s_path), str(temp_dir))
    return temp_dir


@pytest.fixture(scope="function")
def dir_lib_a_flac(tmp_path_factory, dir_orig_data):
    temp_dir = tmp_path_factory.mktemp("A_flac")
    s_path = dir_orig_data.joinpath("music_lib", "A_flac")
    copy_tree(str(s_path), str(temp_dir))
    return temp_dir


@pytest.fixture(scope="class")
def dir_lib_b_mp3(tmp_path_factory, dir_orig_data):
    temp_dir = tmp_path_factory.mktemp("B_mp3")
    s_path = (dir_orig_data.joinpath("music_lib", "B_mp3"))
    copy_tree(str(s_path), str(temp_dir))
    return temp_dir
