import os
import shutil
import tempfile
import unittest

from mmusicc import MmusicC

path_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
path_media = os.path.join(path_root, "media")


class TestMmusicC(unittest.TestCase):

    def setUp(self) -> None:
        self.td = tempfile.TemporaryDirectory()
        self.paths_work = os.path.join(self.td.name, "media")
        shutil.copytree(path_media, self.paths_work)
        os.chdir(self.td.name)
        print("Temporary working directory: {}".format(os.getcwd()))

    def tearDown(self) -> None:
        self.td.cleanup()

    def _test_help(self):
        with self.assertRaises(SystemExit) as cm:
            MmusicC("--help".split())
        the_exception = cm.exception
        self.assertEqual(the_exception.code, 0)

    def _test_version(self):
        with self.assertRaises(SystemExit) as cm:
            MmusicC("--version".split())
        the_exception = cm.exception
        self.assertEqual(the_exception.code, 0)

    def test_load_files(self):
        self.assertTrue(True)
        MmusicC("-s media/test_read.flac -t media/test_read.mp3".split())

    def test_load_albums(self):
        self.assertTrue(True)
        MmusicC("-s media/flac -t media/mp3".split())

    def test_load_file_list(self):
        self.assertTrue(True)
        ps = TestMmusicC.convert2abspath([
            "media/flac/1-str_title_A.flac",
            "media/flac/2-str_title_B.flac",
            "media/flac/3-str_title_C.flac"])
        pt = TestMmusicC.convert2abspath([
            "media/mp3/1-str_title_A.mp3",
            "media/mp3/2-str_title_B.mp3",
            "media/mp3/3-str_title_C.mp3"])
        MmusicC("-s {} -t {}".format(ps, pt).split())

    def test_load_mix(self):
        self.assertTrue(True)
        MmusicC("-s media -t media/mp3".split())

    @staticmethod
    def convert2abspath(paths):
        if isinstance(paths, str):
            return TestMmusicC._convert2abspath(paths)
        else:
            abs_paths = list()
            for p in paths:
                abs_paths.append(TestMmusicC._convert2abspath(p))
            return " ".join(abs_paths)

    @staticmethod
    def _convert2abspath(path):
        return os.path.abspath(path)


if __name__ == '__main__':
    unittest.main()
