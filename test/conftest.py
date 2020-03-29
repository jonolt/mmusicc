import pathlib
import shutil

import pytest

import mmusicc
import mmusicc.formats
import mmusicc.util
import mmusicc.util.allocationmap


@pytest.fixture(scope="session")
def data_dir() -> pathlib.Path:
    return pathlib.Path(__file__).parent.joinpath("data")


@pytest.fixture(scope="session")
def expected_metadata_read(data_dir) -> dict:
    data = {}
    with data_dir.joinpath("read_expected_metadata.py").open("r") as fp:
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
def allocation_map(data_dir):
    mmusicc.util.init_allocationmap(
        str(data_dir.joinpath("metadata_config.yaml")))
    # equals: init_allocationmap(path_config)
    return mmusicc.util.allocationmap


@pytest.fixture(scope="class")
def test_media(tmp_path_factory, data_dir) -> pathlib.Path:
    temp_dir = tmp_path_factory.getbasetemp()
    shutil.copytree(data_dir, temp_dir.joinpath("source"))
    return temp_dir
