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


@pytest.fixture(scope="session")
def expected_metadata_read(dir_orig_data) -> dict:
    data = {}
    with dir_orig_data.joinpath("read_expected_metadata.py").open("r") as fp:
        exec(fp.read(), data)
    return data.get("dict_answer")


@pytest.fixture(scope="session")
def metadata_write_tags(expected_metadata_read, exclude=None) -> dict:
    _dict = expected_metadata_read.copy()
    if not exclude:
        exclude = []
    for key in list(_dict):
        if key in exclude:
            continue
        if not isinstance(_dict[key], str):
            continue
        try:
            cur_int = int(_dict[key])
            _dict[key] = str(cur_int + 1)
        except ValueError:
            if key == 'originaldate':
                continue
            _dict[key] = _dict[key] + "_2"
    return _dict


@pytest.fixture(scope="session")
def audio_loaders() -> dict:
    mmusicc.formats.init()
    # equals: init_formats()
    return mmusicc.formats.loaders


@pytest.fixture(scope="session")
def allocation_map(dir_orig_data):
    mmusicc.util.init_allocationmap(
        str(dir_orig_data.joinpath("metadata_config.yaml")))
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
def dir_lib_a_flac(tmp_path_factory, dir_orig_data):
    temp_dir = tmp_path_factory.mktemp("A_flac")
    s_path = dir_orig_data.joinpath("music_lib", "A_flac")
    res = copy_tree(str(s_path), str(temp_dir))
    return temp_dir


@pytest.fixture(scope="class")
def dir_lib_b_mp3(tmp_path_factory, dir_orig_data):
    temp_dir = tmp_path_factory.mktemp("B_mp3")
    s_path = (dir_orig_data.joinpath("music_lib", "B_mp3"))
    res = copy_tree(str(s_path), str(temp_dir))
    return temp_dir
