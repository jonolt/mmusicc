import re
import warnings
from distutils.file_util import copy_file

import mutagen
import pytest

import mmusicc.formats
import mmusicc.util.allocationmap
from mmusicc.metadata import Empty


@pytest.fixture(scope="module")
def expected_metadata(dir_orig_data) -> dict:
    """expected results for a subset of the loaded elements"""
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
def metadata_write_tags(expected_metadata) -> dict:
    """adds _2 to strings and increases numbers by one and sets artist None"""
    _dict = expected_metadata.copy()
    for key in list(_dict):
        if isinstance(_dict[key], list):
            continue
        try:
            cur_int = int(_dict[key])
            _dict[key] = str(cur_int + 1)
        except ValueError:
            if key == 'originaldate':
                continue
            _dict[key] = _dict[key] + "_2"
    _dict["artist"] = None
    return _dict


def test_dummy_for_init(allocation_map, audio_loaders):
    # test not needed her but otherwise fixture (module level) will not be
    # loaded and the init functions are not called
    assert len(allocation_map.list_tags) > 0
    assert len(audio_loaders) > 0


@pytest.fixture(scope="function")
def media_file(request, audio_files, dir_lib_test):
    """find test file with the given extension and copy it to a test folder"""
    file = audio_files.get(request.param)
    if not file:
        pytest.xfail("No file with given extension '{}' exists."
                     .format(request.param))
    copy_file(str(file), str(dir_lib_test))
    return dir_lib_test.joinpath(file.name)


# TODO find a way to load extension dynamically
# TODO run tests per-class configuration
@pytest.mark.parametrize("media_file",
                         [".mp3", ".flac"],
                         indirect=["media_file"])
class TestFormats:

    def test_read(self, media_file, expected_metadata):
        """read from file and compare with expected"""
        m_file = read_and_compare_file(media_file, expected_metadata)
        keys = list(m_file.unprocessed_tag)
        assert len(keys) == 1
        assert m_file.unprocessed_tag.get(keys[0]) == "not in tag list"

    @pytest.mark.parametrize("remove_existing", [True, False])
    @pytest.mark.parametrize("write_empty", [True, False])
    def test_write(self,
                   media_file,
                   metadata_write_tags,
                   remove_existing,
                   write_empty):
        """write to file and compare with expected, test optional arguments"""
        write_meta_to_file(media_file,
                           metadata_write_tags,
                           remove_existing,
                           write_empty)
        # from test_read we already know that we reading works
        m_file = read_and_compare_file(media_file,
                                       metadata_write_tags,
                                       exclude=["artist"])

        if remove_existing:
            assert len(list(m_file.unprocessed_tag)) == 0
        else:
            assert len(list(m_file.unprocessed_tag)) == 1

        if media_file.suffix == ".mp3":
            warnings.warn(UserWarning("mp3 not tested for write empty"))
            return

        if write_empty:
            assert Empty.is_empty(m_file.dict_meta["artist"])
        else:
            assert "artist" not in m_file.dict_meta

    def test_read_and_write_no_header(self, media_file, expected_metadata):
        """try reading file with no header, header is deleted by mutagen"""
        file_type = mutagen.File(media_file)
        file_type.delete()
        file_type.save()
        read_and_compare_file(media_file, {})
        write_meta_to_file(media_file, expected_metadata, True)
        read_and_compare_file(media_file, expected_metadata)

    def test_write_multiple_tag_values(self, media_file):
        """try writing multiple tag values (lists in tag dict),
        reading was tested in test_read()
        """
        val_dict = {"artist": ["fuu", "bar"]}
        write_meta_to_file(media_file, val_dict, True)
        m_file = read_and_compare_file(media_file, val_dict)
        assert len(m_file.dict_meta) == 1


def write_meta_to_file(path, dict_meta, remove_existing, write_empty=True):
    m_file = mmusicc.formats.MusicFile(str(path))
    m_file.dict_meta = dict_meta.copy()
    m_file.file_save(remove_existing=remove_existing, write_empty=write_empty)


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
