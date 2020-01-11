import unittest

import mmusicc.formats as formats


class MyTestCase(unittest.TestCase):

    def test_something(self):
        formats.init()
        for ext in [".mp3", ".ogg", ".flac"]:
            self.assertIn(ext, list(formats.loaders))
        str_type_list = str(formats.types)
        for t in ["MP3File", "FLACFile", "OggFile"]:
            self.assertIn(t, str_type_list)
        for m in ["audio/ogg; codecs=vorbis", "audio/vorbis", "audio/mp3"]:
            self.assertIn(m, formats.mimes)


if __name__ == '__main__':
    unittest.main()
