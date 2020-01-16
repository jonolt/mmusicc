import os
import shutil
import sys
import time
import unittest

from mmusicc.metadata import Metadata, AlbumMetadata, Div
import mmusicc.formats as formats

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


class TestMetadata(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        Metadata.path_config_yaml = "test_metadata_config.yaml"
        print("Creating new test folder at {}".format(path_test))
        shutil.copytree(path_media, path_test)
        formats.init()

    @classmethod
    def tearDownClass(cls) -> None:
        shutil.rmtree(path_test)
        print("Deleted test folder at {}".format(path_test))

    def test_0001_load_mp3(self):
        """check if all metadata is loaded correctly from file to dict"""
        path_source = os.path.join(path_test, "test_read.mp3")
        source = Metadata(path_source)
        for tag in list(dict_answer):
            self.assertEqual(dict_answer.get(tag), source.dict_data.get(tag))

    def test_0002_load_flac(self):
        """check if all metadata is loaded correctly from file to dict"""
        path_source = os.path.join(path_test, "test_read.flac")
        source = Metadata(path_source)
        for tag in list(dict_answer):
            self.assertEqual(dict_answer.get(tag), source.dict_data.get(tag))

    def test_0011_load_album_mp3(self):
        """check if all metadata is loaded correctly from file to dict"""
        path_source = os.path.join(path_test, "mp3")
        source = AlbumMetadata(path_source)
        self.album_tests(source)

    def test_0012_load_album_flac(self):
        """check if all metadata is loaded correctly from file to dict"""
        path_source = os.path.join(path_test, "flac")
        source = AlbumMetadata(path_source)
        self.album_tests(source)

    def album_tests(self, meta):
        self.assertEqual(dict_answer.get("artist"),
                         meta.dict_data.get("artist"))
        self.assertIsInstance(meta.dict_data.get("title"), Div)
        self.assertIsInstance(meta.dict_data.get("tracknumber"), Div)


if __name__ == "__main__":
    try:
        unittest.main()
    finally:
        TestMetadata.tearDownClass()
