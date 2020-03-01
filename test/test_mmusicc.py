import os
import shutil
import tempfile
import unittest

from mmusicc import MmusicC

path_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
path_media_A = os.path.join(path_root, "media/TestMusicLib_flac")
path_media_B = os.path.join(path_root, "media/TestMusicLib_mp3")


class TestMmusicC(unittest.TestCase):

    def setUp(self) -> None:
        self.td = tempfile.TemporaryDirectory()
        shutil.copytree(path_media_A, os.path.join(self.td.name, "TestMusicLib_flac"))
        shutil.copytree(path_media_B, os.path.join(self.td.name, "TestMusicLib_mp3"))
        os.chdir(self.td.name)
        os.mkdir("newone")
        print("Temporary working directory: {}".format(os.getcwd()))

    def tearDown(self) -> None:
        self.td.cleanup()

    def test_help(self):
        with self.assertRaises(SystemExit) as cm:
            MmusicC("--help".split())
        the_exception = cm.exception
        self.assertEqual(the_exception.code, 0)

    def _test_version(self):
        with self.assertRaises(SystemExit) as cm:
            MmusicC("--version".split())
        the_exception = cm.exception
        self.assertEqual(the_exception.code, 0)

    def test_sync_files(self):
        with self.assertRaises(SystemExit) as cm:
            MmusicC("-s TestMusicLib_flac/artist_puddletag/album_good_(2018)/01_track1.flac -t 01_track1.mp3".split())
        self.assertEqual(cm.exception.code, 0)
        self.assertTrue(os.path.exists("01_track1.mp3"))
        with self.assertRaises(SystemExit) as cm:
            MmusicC("-s TestMusicLib_flac/artist_puddletag/album_good_(2018)/02_track2.flac -t . -f .mp3".split())
        self.assertEqual(cm.exception.code, 0)
        self.assertTrue(os.path.exists("02_track2.mp3"))

    def test_sync_albums(self):
        with self.assertRaises(SystemExit) as cm:
            MmusicC("--album -s TestMusicLib_flac/artist_puddletag/album_good_(2018) -t newone/artist_puddletag/album_good_(2018) -f mp3".split())
        self.assertEqual(cm.exception.code, 0)
        self.assertTrue(os.path.exists("newone/artist_puddletag/album_good_(2018)"))

    def test_sync_lib(self):
        with self.assertRaises(SystemExit) as cm:
            MmusicC("-s TestMusicLib_flac -t TestMusicLib_mp3 -f mp3".split())
        self.assertEqual(cm.exception.code, 0)
        self.assertTrue(os.path.exists("TestMusicLib_mp3/artist_puddletag/album_good_(2018)/01_track1.mp3"))
        self.assertTrue(os.path.exists("TestMusicLib_mp3/various_artists/album_best_hits_compilation_(2010)/CD_02/01_track1.mp3"))

    def test_sync_lib_dry_run(self):
        with self.assertRaises(SystemExit) as cm:
            MmusicC("-s TestMusicLib_flac -t TestMusicLib_mp3 --only-files --dry-run -f mp3".split())
        self.assertEqual(cm.exception.code, 0)
        self.assertFalse(os.path.exists("TestMusicLib_mp3/artist_puddletag/album_good_(2018)/01_track1.mp3"))
        self.assertFalse(os.path.exists("TestMusicLib_mp3/various_artists/album_best_hits_compilation_(2010)/CD_02/01_track1.mp3"))

    def test_sync_to_db(self):
        with self.assertRaises(SystemExit) as cm:
            MmusicC("-s TestMusicLib_flac -tdb fuubar.db".split())
        self.assertEqual(cm.exception.code, 0)
        self.assertTrue(os.path.exists("fuubar.db"))

    def test_sync_from_db(self):
        with self.assertRaises(SystemExit) as cm:
            MmusicC("-sdb TestMusicLib_flac/testMusicLib.db -t TestMusicLib_flac".split())
        self.assertEqual(cm.exception.code, 0)

    def test_white_and_black_list(self):
        with self.assertRaises(SystemExit) as cm:
            MmusicC(("-s TestMusicLib_flac/test_metadata/test_it_(2020)/1-str_title_A.flac "
                     "-t TestMusicLib_mp3/test_metadata/test_it_(2020)/1-str_title_A.mp3 "
                     "--only-meta "
                     "--black-list-tags album title artist track").split()
                    )
        self.assertEqual(cm.exception.code, 0)
        with self.assertRaises(SystemExit) as cm:
            MmusicC(["-s", "TestMusicLib_flac/test_metadata/test_it_(2020)/1-str_title_A.flac",
                     "-t", "TestMusicLib_mp3/test_metadata/test_it_(2020)/1-str_title_A.mp3",
                     "--only-meta",
                     "--white-list-tags", "TestMusicLib_flac/whitelist.txt"]
                    )
        self.assertEqual(cm.exception.code, 0)
        with self.assertRaises(SystemExit) as cm:
            MmusicC(("-s TestMusicLib_flac/test_metadata/test_it_(2020)/1-str_title_A.flac "
                     "-t TestMusicLib_mp3/test_metadata/test_it_(2020)/1-str_title_A.mp3 "
                     "--only-meta "
                     "--black-list-tags album title artist track fuubar").split()
                    )
        self.assertEqual(cm.exception.code, 2)


if __name__ == '__main__':
    unittest.main()
