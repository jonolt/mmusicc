"""
In test_formats.py was tested that all supported formats are loaded correctly
into the AudioFile dict. It is therefore enough to test metadata only with
one format which will be flac.
"""

import pytest

from mmusicc.metadata import Metadata, GroupMetadata, AlbumMetadata, Div

dict_files = {
    Metadata: "1-str_title_A.flac",
    GroupMetadata: ["1-str_title_A.flac",
                    "2-str_title_B.flac",
                    "3-str_title_C.flac"],
    AlbumMetadata: None
}


@pytest.fixture
def import_data(request, dir_lib_a_flac):
    if request.param == AlbumMetadata or request.param == GroupMetadata:
        metadata_path = create_file_path(GroupMetadata, dir_lib_a_flac)
        meta = GroupMetadata(metadata_path)
        for i in range(3):
            meta.list_metadata[i].dict_data.reset()
            meta.list_metadata[i].set_tag('album', "fuubar")
            meta.list_metadata[i].set_tag('artist', "quodlibet")
    else:
        metadata_path = create_file_path(Metadata, dir_lib_a_flac)
        meta = Metadata(metadata_path)
        meta.dict_data.reset()
        meta.set_tag('album', "fuubar")
        meta.set_tag('artist', "quodlibet")
    return request.param, meta


def test_database_link(dir_lib_a_flac, path_database):
    metadata_path = create_file_path(Metadata, dir_lib_a_flac)
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


@pytest.mark.parametrize("class_meta", dict_files.keys())
def test_read(class_meta, dir_lib_a_flac):
    metadata_path = create_file_path(class_meta, dir_lib_a_flac)
    meta = class_meta(metadata_path)
    assert isinstance(meta, class_meta)
    assert meta.dict_data.get("album")
    if class_meta is Metadata:
        assert meta.file_path_set
    else:  # Group and Album are basically the same
        assert isinstance(meta.dict_data.get("title"), Div)


@pytest.mark.parametrize("class_meta", dict_files.keys())
@pytest.mark.parametrize("remove_existing", [True, False])
def test_write_tags(class_meta, dir_lib_a_flac, remove_existing):
    metadata_path = create_file_path(class_meta, dir_lib_a_flac)
    meta = class_meta(metadata_path)
    meta.set_tag("album", "fuubar")
    meta.set_tag("artist", None)
    meta.write_tags(remove_existing=remove_existing)
    meta_2 = class_meta(metadata_path)
    assert meta_2.dict_data.get("album") == "fuubar"
    assert meta_2.dict_data.get("artist") is None
    # TODO actually test/assert remove_existing


@pytest.mark.parametrize("skip_none", [True, False])
@pytest.mark.parametrize("import_data", dict_files.keys(), indirect=True)
def test_import_tags(import_data, dir_lib_a_flac, skip_none):
    class_meta, import_source = import_data
    metadata_path = create_file_path(class_meta, dir_lib_a_flac)
    meta = class_meta(metadata_path)
    meta.import_tags(import_source,
                     whitelist=["album", "title"],
                     skip_none=skip_none)
    # Assert proper import
    assert meta.dict_data.get("album") == "fuubar"
    # Assert whitelist (blacklist does not need to be tested here, since the
    # actual whitelist of the called func is computed from black and whitelist.
    assert meta.dict_data.get("artist") == "str_artist"
    # Assert skip option (parametrized)
    if skip_none:
        if class_meta is Metadata:
            assert meta.dict_data.get("title") == "str_title_A"
        else:
            assert isinstance(meta.dict_data.get("title"), Div)
    else:
        assert meta.dict_data.get("title") is None


@pytest.mark.parametrize("skip_none", [True, False])
@pytest.mark.parametrize("class_meta", dict_files.keys())
def test_import_db_tag(class_meta, dir_lib_a_flac, path_database, skip_none):
    # artist: assert whitelist
    # album : assert correct import
    # title : assert skip none
    if Metadata.is_linked_database:
        Metadata.unlink_database()
    Metadata.link_database(str(path_database))
    metadata_path = create_file_path(class_meta, dir_lib_a_flac)
    meta = class_meta(metadata_path)
    # meta.dict_data.reset()
    meta.import_tags_from_db(whitelist=["album", "title"], skip_none=skip_none)
    assert meta.dict_data.get("artist") == "str_artist"  # not "quodlibet"
    if skip_none:
        if class_meta is Metadata:
            assert meta.dict_data.get("title") == "str_title_A"
        else:  # Group and Album are basically the same
            assert isinstance(meta.dict_data.get("title"), Div)
    else:
        assert meta.dict_data.get("title") is None


@pytest.mark.parametrize("class_meta", dict_files.keys())
def test_export_db_tag(class_meta, dir_lib_a_flac, temp_database):
    # artist: assert whitelist
    # album : assert correct import
    # title : assert skip none
    if Metadata.is_linked_database:
        Metadata.unlink_database()
    Metadata.link_database(str(temp_database))
    metadata_path = create_file_path(class_meta, dir_lib_a_flac)
    meta = class_meta(metadata_path)
    meta.export_tags_to_db()
    meta.import_tags_from_db()
    assert meta.dict_data.get("artist") == "str_artist"
    if class_meta is Metadata:
        assert meta.dict_data.get("title") == "str_title_A"
    else:  # Group and Album are basically the same
        assert isinstance(meta.dict_data.get("title"), Div)


def test_load_empty_meta(dir_lib_a_flac):
    meta = Metadata()
    assert not meta.file_path_set
    meta.link_audio_file(str(dir_lib_a_flac.joinpath("2-str_title_B.flac")))
    assert isinstance(meta, Metadata)
    assert meta.file_path_set
    assert not meta.dict_data.get("album")
    meta.read_tags()
    assert meta.dict_data.get("album")


def create_file_path(class_meta, dir_lib_a_flac):
    files = dict_files.get(class_meta)
    if not files:
        return str(dir_lib_a_flac)
    elif isinstance(files, str):
        return str(dir_lib_a_flac.joinpath(files))
    else:
        return [str(dir_lib_a_flac.joinpath(f)) for f in files]


def test_dry_run():
    pass


def test_div_object():
    pass


def test_metadatadict_reset():
    pass


def test_primary_key_algorithm():
    pass


# def test_create_test_db(temp_database, dir_lib_a_flac):
#     if Metadata.is_linked_database:
#         Metadata.unlink_database()
#     Metadata.link_database(str(temp_database))
#     metadata_path = create_file_path(GroupMetadata, dir_lib_a_flac)
#     meta = GroupMetadata(metadata_path)
#     for i in range(3):
#         meta.list_metadata[i].dict_data.reset()
#         meta.list_metadata[i].set_tag('album', "fuubar")
#         meta.list_metadata[i].set_tag('artist', "quodlibet")
#     meta.export_tags_to_db()

# import pytest
# from mmusicc import Metadata
#
#
# @pytest.fixture
# def metadata_file(dir_lib_a_flac):
#     return dir_lib_a_flac.joinpath("1-str_title_A.flac")
#
#
# class TestXMetadata:
#
#     def test_load(self, metadata_file):
#         meta = Metadata(metadata_file)
#         assert isinstance(meta, Metadata)
#         assert meta.file_path_set
#         assert len(meta.dict_data) > 0
#
#     def test_load_2(self, metadata_file):
#         meta = Metadata()
#         meta.link_audio_file(metadata_file)
#         assert isinstance(meta, Metadata)
#         assert meta.file_path_set
#         assert len(meta.dict_data) > 0
