import re
import warnings

import mutagen
import pytest

import mmusicc.formats
import mmusicc.util.allocationmap


@pytest.fixture(scope="module")
def expected_metadata_read(dir_orig_data) -> dict:
    data = {'album': 'str_album',
            'albumartist': 'str_albumartist',
            'albumartistsort': 'str_albumartistsort',
            'artist': 'str_artist',
            'bpm': '128',
            'comment': 'str_comment',
            'composer': 'str_composer',
            'date': '2020',
            'discid': 'str_discid',
            'discnumber': '2',
            'genre': 'str_genre',
            'isrc': 'QZES81947811',
            'lyrics': 'str_lyrics',
            'title': 'str_title',
            'tracknumber': '3',
            }
    return data


@pytest.fixture(scope="module")
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


@pytest.fixture(scope="module")
def audio_loaders() -> dict:
    mmusicc.formats.init()
    # trigger skipping of initialisation
    mmusicc.formats.init()
    # equals: init_formats()
    return mmusicc.formats.loaders


def test_audio_loaders_found(audio_loaders):
    assert len(audio_loaders) > 0


def test_dummy_load_allocation_map(allocation_map):
    # test not needed her but otherwise fixture (module level) will not load it
    assert len(allocation_map.list_tags) > 0


@pytest.fixture(scope="function")
def media_file(request, audio_files):
    file = audio_files.get(request.param)
    if not file:
        pytest.xfail("No file with given extension '{}' exists."
                     .format(request.param))
    return file


# TODO find a way to load extension dynamically
# TODO run tests per-class configuration
@pytest.mark.parametrize("media_file",
                         [".mp3", ".flac"],
                         indirect=["media_file"])
class TestFormats:

    def test_read(self, media_file, expected_metadata_read):
        read_and_compare_file(media_file, expected_metadata_read)

    @pytest.mark.parametrize("remove_existing", [True, False])
    def test_write(self, media_file, metadata_write_tags, remove_existing):
        write_meta_to_file(media_file, metadata_write_tags, remove_existing)
        # from test_read we already know that we reading works
        read_and_compare_file(media_file, metadata_write_tags)
        # TODO actually test/assert remove_existing

    def test_read_no_header(self, media_file):
        file_type = mutagen.File(media_file)
        file_type.delete()
        file_type.save()
        read_and_compare_file(media_file, {})

    def test_write_no_header(self, media_file, expected_metadata_read):
        write_meta_to_file(media_file, expected_metadata_read, True)
        read_and_compare_file(media_file, expected_metadata_read)

    def test_multiple_tag_values(self, media_file):
        val_dict = {"artist": ["fuu", "bar"]}
        write_meta_to_file(media_file, val_dict, True)
        m_file = read_and_compare_file(media_file, val_dict)
        assert len(m_file.dict_meta) == 1


def write_meta_to_file(path, dict_meta, remove_existing):
    m_file = mmusicc.formats.MusicFile(str(path))
    m_file.dict_meta = dict_meta
    m_file.file_save(remove_existing=remove_existing)


def read_and_compare_file(path, dict_answer, exclude=None):
    m_file = mmusicc.formats.MusicFile(str(path))
    m_file.file_read()
    if not exclude:
        exclude = []
    for tag in list(dict_answer):
        if tag in exclude:
            continue
        assert dict_answer.get(tag) == m_file.dict_meta.get(tag)
    return m_file


@pytest.fixture(scope="class")
def audio_files(audio_loaders, dir_subpackages) -> dict:
    loaders = set(audio_loaders.values())
    extensions = set(audio_loaders.keys())
    files = [p.name for p in dir_subpackages.glob("*.*")]
    regex = re.compile(r"formats_[\w\d]*.[\w\d]{3,4}")
    files = list(filter(regex.search, files))
    audio_files = dict()
    for f in files:
        path = dir_subpackages.joinpath(f)
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
