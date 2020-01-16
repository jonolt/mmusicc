import unittest
import shutil
import os
import time
import sys

import mmusicc.formats as formats

path_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, path_root)

name_test_folder = "test_mmusicc_" + str(int(time.time()))
path_test = os.path.join(path_root, name_test_folder)
path_media = os.path.join(path_root, "media")


class MyTestCase(unittest.TestCase):

    @classmethod
    def setUpClass(cls) -> None:
        print("Creating new test folder at {}".format(path_test))
        shutil.copytree(path_media, path_test)
        formats.init()

    @classmethod
    def tearDownClass(cls) -> None:
        shutil.rmtree(path_test)
        print("Deleted test folder at {}".format(path_test))

    def test_something(self):
        for ext in [".mp3", ".ogg", ".flac"]:
            self.assertIn(ext, list(formats.loaders))
        str_type_list = str(formats.types)
        for t in ["MP3File", "FLACFile", "OggFile"]:
            self.assertIn(t, str_type_list)
        for m in ["audio/ogg; codecs=vorbis", "audio/vorbis", "audio/mp3"]:
            self.assertIn(m, formats.mimes)


if __name__ == '__main__':
    unittest.main(failfast=True)
