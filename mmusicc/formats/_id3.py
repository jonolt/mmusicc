from ._audio import AudioFile


class ID3File(AudioFile):

    Kind = None

    def __init__(self):
        super().__init__()
