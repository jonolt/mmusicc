import os

from mmusicc.metadata import Metadata, GroupMetadata, AlbumMetadata


# noinspection PyPep8Naming
def PathLoader(path):
    """loads content path is pointing at. can be:

        - a single file
        - a single folder (scans only folder level)
        - a list of files/folders (finds all audio files in path). always pass
            this as list (otherwise it will interpret it as album).

    """
    if isinstance(path, str):
        path = os.path.expanduser(path)
        if os.path.isfile(path):
            return Metadata(path)
        elif os.path.isdir(path):
            return AlbumMetadata(path)
        else:
            raise FileNotFoundError
    else:
        listOfFiles = set()
        for p in path:
            p = os.path.expanduser(p)
            if os.path.exists(p):
                if os.path.isfile(p):
                    listOfFiles.add(p)
                    continue
                # Get the list of all files in directory tree at given path
                for (dirpath, _, filenames) in os.walk(p):
                    listOfFiles.update(
                        [os.path.join(dirpath, file) for file in filenames])
            else:
                print("path '{}' does not exist, continuing".format(path))
        for path in listOfFiles:
            if not Metadata.check_is_audio(path):
                listOfFiles.remove(path)
        if len(listOfFiles) > 0:
            GroupMetadata(list(listOfFiles))
        else:
            print("no audio files found in path '{}'".format(path))
