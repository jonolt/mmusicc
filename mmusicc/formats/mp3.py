from mutagen.mp3 import MP3
from ._id3 import ID3File


extensions = [".mp3", ".mp2", ".mp1", ".mpg", ".mpeg"]
# loader   see bottom
# types    see bottom


class MP3File(ID3File):

    format = "MPEG-1/2"
    mimes = ["audio/mp3", "audio/x-mp3", "audio/mpeg", "audio/mpg",
             "audio/x-mpeg"]
    Kind = MP3

    def __init__(self):
        super().__init__()


loader = MP3File
types = [MP3File]
