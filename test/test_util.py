

def test_dummy_load_allocation_map(allocation_map):
    # test not needed her but otherwise fixture (module level) will not load it
    assert len(allocation_map.list_tags) > 0


def test_black_and_whitelist(dir_lib_x_flac):
    pass
