from mmusicc.database import MetaDB


test_dict = {
    "album": "mmusicc",  # str
    "artist": 42,  # int
    "title": 3.14,  # float
    "genre": ["fuu", "bar"],  # list
    "albumartist": ("fuu", "bar"),  # tuple
    "date": object(),  # object
    "albumartistsort": None,  # None
}


def test_dummy_load_allocation_map(allocation_map):
    # test not needed her but otherwise fixture (module level) will not load it
    assert len(allocation_map.list_tags) > 0


def test_read_and_write_database(temp_database):
    db = MetaDB(str(temp_database))
    db.insert_meta(test_dict, "some_path")
    db = MetaDB(str(temp_database))
    read_dict = db.read_meta("some_path")
    assert isinstance(read_dict.get("date"), object)
    read_dict.pop("date")
    for key in read_dict.keys():
        assert read_dict.get(key) == test_dict.get(key)
    assert read_dict.get("tracknumber") is None
