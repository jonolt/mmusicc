import os
import shutil
import sys
import time
import unittest

from mmusicc.metadata import Metadata, AlbumMetadata, Div, Empty

path_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, path_root)

name_test_folder = "test_mmusicc_" + str(int(time.time()))
path_test = os.path.join(path_root, name_test_folder)
path_media = os.path.join(path_root, "media")


class TestMetadata(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        Metadata.path_config_yaml = "test/test_metadata_config.yaml"

    def test_0001_load_mp3(self):
        """check if all metadata is loaded correctly from file to dict"""
        path_source = os.path.join(path_test, "test_read.mp3")
        source = Metadata(path_source)
        for tag in source.list_tags:
            self.assertEqual(source.dict_data.get(tag),
                             source.dict_test_read.get(tag))

    def test_0002_load_flac(self):
        """check if all metadata is loaded correctly from file to dict"""
        path_source = os.path.join(path_test, "test_read.flac")
        source = Metadata(path_source)
        for tag in source.list_tags:
            if tag == "ARRANGER".casefold():
                self.assertEqual(source.dict_data.get(tag),
                                 'str_arranger_A|str_arranger_B')
            else:
                self.assertEqual(source.dict_data.get(tag),
                                 source.dict_test_read.get(tag))

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
        self.assertEqual(meta.dict_data.get("artist"),
                         meta.dict_test_read.get("artist"))
        self.assertIsInstance(meta.dict_data.get("title"), Div)
        self.assertIsInstance(meta.dict_data.get("tracknumber"), Div)


if __name__ == "__main__":
    try:
        print("Creating new test folder at {}".format(path_test))
        shutil.copytree(path_media, path_test)
        unittest.main(failfast=True)
    finally:
        shutil.rmtree(path_test)
        print("Deleted test folder at {}".format(path_test))
