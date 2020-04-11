import pathlib

from mmusicc.util.misc import get_the_right_one, swap_base


def test_dummy_load_allocation_map(allocation_map):
    # test not needed her but otherwise fixture (module level) will not load it
    assert len(allocation_map.list_tags) > 0


def test_black_and_whitelist(dir_lib_x_flac):
    pass


def test_get_the_right_one():

    plist = ["a/b/c/fuu/beam/hello.mp3",
             "d/e/f/fuu/bar/world.mp3",
             "g/h/foo/bar/hello.mp3",
             pathlib.Path("l/fee/bar/world.mp3"),
             ]
    match = "m/n/foo/bar/hello.mp3"

    the_right_one = get_the_right_one(plist, match)

    assert str(the_right_one) == plist[2]


def test_swap_base():
    root_a = pathlib.Path("base/A")
    path_a = pathlib.Path("base/A/fuu/bar/")
    root_b = pathlib.Path("esab/B")
    path_b_expected = pathlib.Path("esab/B/fuu/bar/")
    assert swap_base(root_a, path_a, root_b) == path_b_expected
