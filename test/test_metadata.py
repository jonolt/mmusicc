import os
import shutil
import sys
import time
import unittest

import mmusicc
from mmusicc.metadata import Metadata, AlbumMetadata, Div

path_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, path_root)

name_test_folder = "test_mmusicc_" + str(int(time.time()))
path_test = os.path.join(path_root, name_test_folder)
path_media = os.path.join(path_root, "media")

dict_answer = {'album': 'str_album',
               'albumartist': 'str_albumartist',
               'albumartistsort': 'str_albumartistsort',
               'albumsort': 'str_albumsort',
               'arranger': ['str_arranger_A', 'str_arranger_B'],
               'artist': 'str_artist',
               'artistsort': 'str_artistsort',
               'bpm': '128',
               'comment': 'str_comment',
               'composer': 'str_composer',
               'date': '2020',
               'description': 'str_description',
               'discid': 'str_discid',
               'discnumber': '2',
               'genre': 'str_genre',
               'isrc': 'QZES81947811',
               'lyrics': 'str_lyrics',
               'originalalbum': 'str_originalalbum',
               'originalartist': 'str_originalartist',
               'originaldate': '2000-01-01',
               'part': 'str_part',
               'title': 'str_title',
               'tracknumber': '3'}


def append_2(_dict, exclude=None):
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


dict_answer_2 = append_2(dict_answer.copy())


class TestMetadata(unittest.TestCase):

    assert_counter = 0
    assert_counter_single = 0
    assert_counter_single_list = list()

    @classmethod
    def setUpClass(cls):
        Metadata.path_config_yaml = "test_metadata_config.yaml"
        print("Creating new test folder at {}".format(path_test))
        shutil.copytree(path_media, path_test)
        cls.assert_counter = 0
        mmusicc.init()

    @classmethod
    def tearDownClass(cls) -> None:
        shutil.rmtree(path_test)
        print("Successful asserts: {} -> {}".format(
            cls.assert_counter, str(cls.assert_counter_single_list)))
        print("Deleted test folder at {}".format(path_test))

    def setUp(self) -> None:
        TestMetadata.assert_counter_single = 0

    def tearDown(self) -> None:
        TestMetadata.assert_counter_single_list.append(
            TestMetadata.assert_counter_single)
        TestMetadata.assert_counter += TestMetadata.assert_counter_single

    def test_0001_load_file_mp3(self):
        """check if all metadata is loaded correctly from file to dict"""
        path_source = os.path.join(path_test, "test_read.mp3")
        self.read_and_compare_file(path_source, dict_answer)

    def test_0002_load_file_flac(self):
        """check if all metadata is loaded correctly from file to dict"""
        path_source = os.path.join(path_test, "test_read.flac")
        self.read_and_compare_file(path_source, dict_answer)

    def test_0011_load_album_mp3(self):
        """check if all metadata is loaded correctly from file to dict"""
        path_source = os.path.join(path_test, "mp3")
        self.album_tests(path_source)

    def test_0012_load_album_flac(self):
        """check if all metadata is loaded correctly from file to dict"""
        path_source = os.path.join(path_test, "flac")
        self.album_tests(path_source)

    def test_0101_save_file_mp3(self):
        path_source = os.path.join(path_test, "test_read.mp3")
        source = Metadata(path_source)
        append_2(source.dict_data)
        source.write_tags(remove_other=True)
        self.read_and_compare_file(path_source, dict_answer_2)

    def test_0102_save_file_flac(self):
        path_source = os.path.join(path_test, "test_read.flac")
        source = Metadata(path_source)
        append_2(source.dict_data)
        source.write_tags(remove_other=True)
        self.read_and_compare_file(path_source, dict_answer_2)

    def read_and_compare_file(self, path, cmp_dict, exclude=None):
        source = Metadata(path)
        self.read_and_compare(source, cmp_dict, exclude=exclude)

    def read_and_compare(self, meta, cmp_dict, exclude=None):
        if not exclude:
            exclude = []
        for tag in list(dict_answer):
            if tag in exclude:
                continue
            self.assertEqual(cmp_dict.get(tag), meta.dict_data.get(tag))
            TestMetadata.assert_counter_single += 1

    def album_tests(self, path):
        divs = ["title", "tracknumber"]
        meta = AlbumMetadata(path)
        self.read_and_compare(meta, dict_answer, exclude=divs)
        for tag in divs:
            self.assertIsInstance(meta.dict_data.get(tag), Div)
            TestMetadata.assert_counter_single += 1


if __name__ == "__main__":
    unittest.main()
