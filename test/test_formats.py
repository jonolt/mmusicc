import pathlib
import re
import warnings

import pytest

import mmusicc.formats


def test_audio_loaders_found(audio_loaders):
    assert len(audio_loaders) > 0


def test_allocation_map_loaded(allocation_map):
    assert len(allocation_map.list_tags) > 0


@pytest.fixture(scope="function")
def media_file(request, audio_files):
    file = audio_files.get(request.param)
    if not file:
        pytest.xfail("No file with given extension '{}' exists."
                     .format(request.param))
    return file


# TODO find a way to load extension dynamically
@pytest.mark.parametrize("media_file",
                         [".mp3", ".flac"],
                         indirect=["media_file"])
class TestFormats:

    def test_read(self, media_file, expected_metadata_read):
        read_and_compare_file(media_file, expected_metadata_read)

    def test_write(self, media_file, metadata_write_tags):
        write_meta_to_file(media_file, metadata_write_tags)

    # from test_read we already know that we reading works
    def test_read_written(self, media_file, metadata_write_tags):
        read_and_compare_file(media_file, metadata_write_tags)


def write_meta_to_file(path, dict_meta):
    m_file = mmusicc.formats.MusicFile(str(path))
    m_file.dict_meta = dict_meta
    m_file.file_save(remove_existing=True)


def read_and_compare_file(path, dict_answer, exclude=None):
    m_file = mmusicc.formats.MusicFile(str(path))
    m_file.file_read()
    if not exclude:
        exclude = []
    for tag in list(dict_answer):
        if tag in exclude:
            continue
        assert dict_answer.get(tag) == m_file.dict_meta.get(tag)


@pytest.fixture(scope="class")
def audio_files(audio_loaders, test_media) -> dict:
    loaders = set(audio_loaders.values())
    extensions = set(audio_loaders.keys())
    audio_file_dir = test_media.joinpath("source")
    files = [p.name for p in audio_file_dir.glob("*.*")]
    regex = re.compile(r"formats_[\w\d]*.[\w\d]{3,4}")
    files = list(filter(regex.search, files))
    audio_files = dict()
    for f in files:
        path = pathlib.Path(audio_file_dir, f)
        audio_files[path.suffix] = path
        extensions.remove(path.suffix)
        try:
            loaders.remove(audio_loaders.get(path.suffix))
        except KeyError:
            pass
    # if loaders is empty all loaders have/will been tested
    # extensions is just for info what supported extension types are not tested
    if len(loaders) > 0:
        warnings.warn(UserWarning("module(s) '{}' is not been tested"
                                  .format(str(loaders))))
    return audio_files
