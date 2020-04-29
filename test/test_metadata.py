import pytest

from mmusicc.metadata import GroupMetadata, AlbumMetadata, Div, Empty
from ._util import *

_dict_files = {
    Metadata: "1-str_title_A.flac",
    GroupMetadata: ["1-str_title_A.flac", "2-str_title_B.flac", "3-str_title_C.flac"],
    AlbumMetadata: None,  # _create_file_path return an folder path
}


def test_dummy_for_init(allocation_map, audio_loaders):
    """test not needed here but otherwise fixture (module level) will not be
        loaded and the init functions are not called
    """
    assert len(allocation_map.list_tags) == 16
    assert len(audio_loaders) > 0


@pytest.fixture
def modified_metadata(request, dir_lib_x_flac):
    """provides a Metadata object loaded from the flac source with modified
        values for test.
    """
    if request.param == AlbumMetadata or request.param == GroupMetadata:
        metadata_path = _create_file_path(GroupMetadata, dir_lib_x_flac)
        meta = GroupMetadata(metadata_path)
        meta.reset_meta()
        meta.set_tag("album", "fuubar")
        meta.set_tag("artist", "quodlibet")
    else:
        metadata_path = _create_file_path(Metadata, dir_lib_x_flac)
        meta = Metadata(metadata_path)
        meta.dict_data.reset()
        meta.set_tag("album", "fuubar")
        meta.set_tag("artist", "quodlibet")
    return request.param, meta


def test_database_link(dir_lib_x_flac, path_database):
    """test linking and unlinking the database and corresponding properties."""
    metadata_path = _create_file_path(Metadata, dir_lib_x_flac)
    meta = Metadata(metadata_path)
    with pytest.raises(Exception):
        meta.export_tags_to_db()
    with pytest.raises(Exception):
        Metadata.unlink_database()
    Metadata.link_database(str(path_database))
    assert Metadata.is_linked_database
    with pytest.raises(Exception):
        Metadata.link_database(str(path_database))
    Metadata.unlink_database()
    assert not Metadata.is_linked_database
    Metadata.link_database(str(path_database))


@pytest.mark.parametrize("class_meta", _dict_files.keys())
def test_read_tags(class_meta, dir_lib_x_flac):
    metadata_path = _create_file_path(class_meta, dir_lib_x_flac)
    meta = class_meta(metadata_path)
    assert isinstance(meta, class_meta)
    assert meta._dict_data.get("album")
    if class_meta is Metadata:
        assert meta.file_path
    else:  # Group and Album are basically the same
        assert isinstance(meta._dict_data.get("title"), Div)


@pytest.mark.parametrize("class_meta", _dict_files.keys())
@pytest.mark.parametrize("rem_ex, write_empty", [(False, False), (True, True)])
def test_write_tags(class_meta, dir_lib_x_flac, rem_ex, write_empty):
    metadata_path = _create_file_path(class_meta, dir_lib_x_flac)
    meta = class_meta(metadata_path)
    meta.set_tag("album", "fuubar")
    meta.set_tag("albumartist", Empty())
    meta.set_tag("artist", None)
    meta.write_tags(remove_existing=rem_ex, write_empty=write_empty)
    meta_2 = class_meta(metadata_path)
    assert meta_2._dict_data.get("album") == "fuubar"

    if rem_ex:
        assert meta_2._dict_data.get("artist") is None
    else:
        assert meta_2._dict_data.get("artist") == "str_artist"

    if write_empty:
        assert Empty.is_empty(meta_2._dict_data.get("albumartist"))
    else:
        assert meta_2._dict_data.get("albumartist") is None


@pytest.mark.parametrize("skip_none", [True, False])
@pytest.mark.parametrize("modified_metadata", _dict_files.keys(), indirect=True)
def test_import_tags(modified_metadata, dir_lib_x_flac, skip_none):
    class_meta, import_source = modified_metadata
    metadata_path = _create_file_path(class_meta, dir_lib_x_flac)
    meta = class_meta(metadata_path)
    meta.import_tags(import_source, whitelist=["album", "title"], skip_none=skip_none)
    # Assert proper import
    assert meta.get_tag("album") == "fuubar"
    # Assert whitelist (blacklist does not need to be tested here, since the
    # actual whitelist of the called func is computed from black and whitelist.
    assert meta.get_tag("artist") == "str_artist"
    # Assert skip option (parametrized)
    if skip_none:
        if class_meta is Metadata:
            assert meta.get_tag("title") == "str_title_A"
        else:
            assert isinstance(meta.get_tag("title"), Div)
    else:
        assert meta.get_tag("title") is None


@pytest.mark.parametrize("skip_none", [True, False])
@pytest.mark.parametrize("class_meta", _dict_files.keys())
def test_import_db_tag(class_meta, dir_lib_x_flac, path_database, skip_none):
    # artist: assert whitelist
    # album : assert correct import
    # title : assert skip none
    if Metadata.is_linked_database:
        Metadata.unlink_database()
    Metadata.link_database(str(path_database))
    metadata_path = _create_file_path(class_meta, dir_lib_x_flac)
    meta = class_meta(metadata_path)
    meta.set_tag("album", "fuu")
    meta.set_tag("artist", "bar")
    meta.import_tags_from_db(whitelist=["album", "title"], skip_none=skip_none)
    assert meta.get_tag("artist") == "bar"
    if skip_none:
        if class_meta is Metadata:
            assert meta.get_tag("title") == "str_title_A"
        else:  # Group and Album are basically the same
            assert isinstance(meta.get_tag("title"), Div)
    else:
        assert meta.get_tag("title") is None


@pytest.mark.parametrize("class_meta", _dict_files.keys())
def test_export_db_tag(class_meta, dir_lib_x_flac, temp_database):
    # artist: assert whitelist
    # album : assert correct import
    if Metadata.is_linked_database:
        Metadata.unlink_database()
    Metadata.link_database(str(temp_database))
    metadata_path = _create_file_path(class_meta, dir_lib_x_flac)
    meta = class_meta(metadata_path)
    meta.export_tags_to_db()
    meta._dict_data.reset()
    meta.import_tags_from_db()
    assert meta.get_tag("artist") == "str_artist"
    if class_meta is Metadata:
        assert meta.get_tag("title") == "str_title_A"
    else:  # Group and Album are basically the same
        assert isinstance(meta.get_tag("title"), Div)


def test_load_empty_meta(dir_lib_x_flac):
    meta = Metadata()
    assert not meta.audio_file_linked
    meta.link_audio_file(str(dir_lib_x_flac.joinpath("2-str_title_B.flac")))
    assert isinstance(meta, Metadata)
    assert meta.audio_file_linked
    assert not meta.get_tag("album")
    meta.read_tags()
    assert meta.get_tag("album")


def test_dry_run(dir_lib_x_flac, temp_database):
    Metadata.dry_run = True
    if Metadata.is_linked_database:
        Metadata.unlink_database()
    Metadata.link_database(str(temp_database))
    metadata_path = _create_file_path(Metadata, dir_lib_x_flac)
    th = save_files_hash_and_mtime(metadata_path)
    meta = Metadata(metadata_path)
    meta.set_tag("album", "fuubar")
    meta.write_tags()
    meta.export_tags_to_db()
    meta.read_tags()
    assert meta.get_tag("album") != "fuubar"
    with pytest.raises(KeyError):
        meta.import_tags_from_db()
    # reset class variable to default
    assert cmp_files_hash_and_time(metadata_path, th) == 1
    Metadata.dry_run = False


@pytest.mark.skip(reason="not implemented - not so important")
def test_div_object():
    pass


def _create_file_path(class_meta, dir_lib_a_flac):
    files = _dict_files.get(class_meta)
    if not files:
        return str(dir_lib_a_flac)
    elif isinstance(files, str):
        return str(dir_lib_a_flac.joinpath(files))
    else:
        return [str(dir_lib_a_flac.joinpath(f)) for f in files]
