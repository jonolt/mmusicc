import yaml
import os
import mutagen
import mimetypes

class Metadata:

    class_initialized = False
    path_config_yaml = "config.yaml"
    write_empty = True

    @classmethod
    def init_class(cls):
        dicts = cls.get_dictionaries(cls.path_config_yaml)
        cls.dict_config = dicts.get("dict_config")
        cls.list_displ_tags = dicts.get("list_displ_tags")
        cls.list_tags = dicts.get("list_tags")
        cls.dict_tags_id3 = dicts.get("dict_tags_id3")
        cls.dict_tags_str = dicts.get("dict_tags_str")
        cls.class_initialized = True

    @classmethod
    def get_dictionaries(cls, path=None):

        list_displ_tags = [None] * 20
        list_tags = list()
        dict_tags_id3 = dict()
        dict_tags_str = dict()

        if not path:
            path = cls.path_config_yaml

        if not os.path.exists(path):
            raise FileNotFoundError("config file not found")
        with open(path, 'r') as f:
            dict_config = yaml.safe_load(f)
        for key, value in dict_config.items():
            pos = value[0]
            id3_tag = value[1]
            assertions = value[2]

            list_tags.append(key)
            list_displ_tags[pos-1] = key
            dict_tags_id3[key] = id3_tag
            strings = []
            if key not in assertions:
                strings.append(key)
            for val in assertions:
                strings.append(val)
            dict_tags_str[key] = strings
            i = len(list_displ_tags) - 1

        while list_displ_tags[i] is None:
            list_displ_tags.pop(i)
            i -= 1

        return {
            "dict_config": dict_config,
            "list_displ_tags": list_displ_tags,
            "list_tags": list_tags,
            "dict_tags_id3": dict_tags_id3,
            "dict_tags_str": dict_tags_str,
        }


    def __init__(self, file, read_tag=True):
        """
        file can be None, this is tu support album Metadata

        :param file: fuu
        """
        if not Metadata.class_initialized:
            Metadata.init_class()
        if not file:
            pass
        elif os.path.exists(file):
            self._file_path = file
            self._file = mutagen.File(self._file_path)
            # TODO what happens if file contains no tag?
        else:
            raise FileNotFoundError("Error File does not exist")

        self.dict_data = dict()
        for tag in Metadata.list_tags:
            self.dict_data[tag] = None

        self.unprocessed_tags = None
        if file and read_tag:
            self.read_tag()

    @property
    def file_name(self):
        return os.path.splitext(os.path.basename(self._file_path))[0]

    def read_tag(self):
        if isinstance(self._file, mutagen.mp3.MP3):
            self.__read_tag_mp3()
        if isinstance(self._file, mutagen.flac.FLAC):
            self.__read_tag_flac()

    def __read_tag_mp3(self):

        self.dummy_dict = dict(self._file.items().copy())

        for key in self.dummy_dict.keys():
            if "APIC:" in key:
                self.dummy_dict.pop(key)
                break

        for key in list(self.dict_data):
            id3_frame = Metadata.dict_tags_id3.get(key)
            try:
                val = self.dummy_dict.pop(id3_frame).text[0]
            except KeyError:  # raised when tag is not filled
                val = None

            if isinstance(val, mutagen.id3.ID3TimeStamp):
                val = val.text

            self.dict_data[key] = val

        if self.dummy_dict:
            self.unprocessed_tags = str(self.dummy_dict)

    def __read_tag_flac(self, join=True):

        if not self._file.tags:
            return
        self.dummy_dict = dict(self._file.tags.copy())

        for key in list(self.dict_data):
            ret_val = []
            ret_key = []
            for k in Metadata.dict_tags_str.get(key):
                try:
                    val = self.dummy_dict.pop(k)
                    if val:
                        ret_val.append(val)
                        ret_key.append(k)
                except KeyError:
                    continue
            if len(ret_val) == 0:
                val = None
            else:
                # take the list and check if entries a double
                if len(ret_val) > 1:
                    i = 0
                    j = 0
                    while i < len(ret_val):
                        while j < len(ret_val):
                            if i == j:
                                j += 1
                                continue
                            if ret_val[i] == ret_val[j]:
                                #self.log_to_db(
                                print(
                                    "dropped duplicate pair {}:{}, cheeping {}:{}"
                                    .format(ret_val[i], ret_key[i], ret_val[j],
                                            ret_key[j]))
                                ret_val.remove(ret_val[i])
                            j += 1
                        i += 1
                    if join:
                        val = ';'.join(ret_val)
                    else:
                        val = ret_val
                val = ret_val[0]

            self.dict_data[key] = val

        if self.dummy_dict:
            self.unprocessed_tags = str(self.dummy_dict)

    def write_tag(self, remove_other=True):
        """write tag to files if remove_other, clear all existing tags
        first, else overwrite them
        """
        if isinstance(self._file, mutagen.mp3.MP3):
            self.__write_tag_mp3(remove_other=remove_other)
        if isinstance(self._file, mutagen.flac.FLAC):
            self.__write_tag_flac(remove_other=remove_other)

    def __write_tag_mp3(self, remove_other=True):

        if self._file.tags and remove_other:
            self._file.tags = mutagen.id3.ID3()

        for tag in self.list_tags:
            val = self.dict_data.get(tag)
            if not val and not Metadata.write_empty:
                continue
            if val:
                id3_tag = Metadata.dict_tags_id3.get(tag)
                try:
                    self._file.tags[id3_tag] = val
                except TypeError:
                    try:
                        mutagen_id3 = eval("mutagen.id3.%s" % id3_tag)
                        tmp = mutagen_id3(text=val)
                    except AttributeError:
                        # TODO write TXXX tag
                        print("skipping {}={}".format(tag, val))
                        continue

                    self._file.tags.add(tmp)

        self._file.save(v1=2, v2_version=4)

    def __write_tag_flac(self, remove_other=True):

        if self._file.tags and remove_other:
            self._file.delete()

        if self._file.tags is None:
            self._file.add_tags()

        for tag in self.list_tags:

            val = self.dict_data.get(tag)

            if val is None:
                if Metadata.write_empty:
                    val = ""
                else:
                    continue

            self._file.tags[tag] = val

        self._file.save()

    def import_tag(self, source_meta, whitelist=None, blacklist=None, remove_other=False):
        """import metadata from source meta object"""
        tags = Metadata._process_white_and_blacklist(whitelist, blacklist)
        for tag in self.list_tags:
            if tag in tags:
                self.dict_data[tag] = source_meta.dict_data[tag]
            else:
                if remove_other:
                    self.dict_data[tag] = None

    @staticmethod
    def _process_white_and_blacklist(whitelist, blacklist):
        if not whitelist:
            whitelist = Metadata.list_tags
        if blacklist:
            for t in blacklist:
                try:
                    whitelist.pop(whitelist.index(t))
                except ValueError:
                    print("warning {} not in whitelist".format(t))
                    continue
        return whitelist

    @staticmethod
    def check_is_audio(file):
        mimetype = mimetypes.guess_type(file)
        if mimetype[0] and "audio"in mimetype[0]:
            return True
        else:
            return False


class AlbumMetadata(Metadata):

    def __init__(self, path_album):
        super().__init__(None)
        self.list_metadata = list()
        for file in os.listdir(path_album):
            Metadata.check_is_audio(file)
            if Metadata.check_is_audio(file):
                file_path = os.path.join(path_album, file)
                self.list_metadata.append(Metadata(file_path))
        self.read_tag()

    def read_tag(self):
        for metadata in self.list_metadata:
            metadata.read_tag()
        for key in list(metadata.dict_data):
            first = True
            for metadata in self.list_metadata:
                data = metadata.dict_data.get(key)
                if first:
                    self.dict_data[key] = data
                    first = False
                else:
                    if self.dict_data[key] == data:
                        pass
                    else:
                        self.dict_data[key] = Div(key, self.list_metadata)
                        break

    def write_tag(self, remove_other=True):
        for metadata in self.list_metadata:
            metadata.write_tag(remove_other=remove_other)

    def import_tag(self, source_meta, whitelist=None, blacklist=None,
                   remove_other=False):

        tags = Metadata._process_white_and_blacklist(whitelist, blacklist)

        for metadata_self in self.list_metadata:
            for metadata_source in source_meta.list_metadata:
                if metadata_self.file_name == metadata_source.file_name:
                    metadata_self.import_tag(
                        metadata_source,
                        whitelist=whitelist,
                        blacklist=blacklist,
                        remove_other=remove_other)


class Div:

    def __init__(self, key=None, list_metadata=None):
        self._dict_values = dict()
        self._key_tag = None  # maybe not needed
        if key and list_metadata:
            self.add_metadata(key, list_metadata)

    def __repr__(self):
        return "<div>"

    def add_metadata(self, key_tag, list_metadata):
        self._key_tag = key_tag
        for metadata in list_metadata:
            self.add_value(metadata, metadata.dict_data.get(self._key_tag))

    def add_value(self, obj, val):
        self._dict_values[obj] = val

#    def add_dict(self, dict):
#        """dict<obj:val>"""
#        pass


def fuu():
    whitelist = None
    whitelist = ["ALBUM"]

    mfs = Metadata(
        "/home/johannes/Desktop/MusicManager/media/The_Mariana_Hollow/The_Abandoned_Parade_(2019)/01_Only_The_Fear.flac")
    m3 = Metadata(
        "/home/johannes/Desktop/MusicManager/test/The_Mariana_Hollow/The_Abandoned_Parade_(2019)/01_Only_The_Fear.mp3")
    mf = Metadata(
        "/home/johannes/Desktop/MusicManager/test/The_Mariana_Hollow/The_Abandoned_Parade_(2019)/01_Only_The_Fear.flac")

    m3.import_tag(mfs, whitelist=whitelist, remove_other=True)
    # m3.write_tag()

    mf.import_tag(mfs, whitelist=whitelist, remove_other=True)
    # mf.write_tag()

    print(mfs, m3, mf)

def bar():
    mas = AlbumMetadata(
        "/home/johannes/Desktop/MusicManager/media/The_Mariana_Hollow/The_Abandoned_Parade_(2019)/")
    mat = AlbumMetadata(
        "/home/johannes/Desktop/MusicManager/test/The_Mariana_Hollow/The_Abandoned_Parade_(2019)/")
    mat.import_tag(mas)

    print(mat)

if __name__ == "__main__":
    fuu()
    bar()