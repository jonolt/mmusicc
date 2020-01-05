import yaml
import os
import mutagen


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


    def __init__(self, file):
        if not Metadata.class_initialized:
            Metadata.init_class()
        if os.path.exists(file):
            self._file_path = file
            self._file = mutagen.File(self._file_path)
            # TODO what happens if file contains no tag?
        else:
            raise FileNotFoundError("Error File does not exist")
        self.unprocessed_tags = None
        self.dict_data = dict()
        for tag in Metadata.list_tags:
            self.dict_data[tag] = None

        self.read_tag()

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
        tags = Metadata.__process_white_and_blacklist(whitelist, blacklist)
        for tag in self.list_tags:
            if tag in tags:
                self.dict_data[tag] = source_meta.dict_data[tag]
            else:
                if remove_other:
                    self.dict_data[tag] = None

    @staticmethod
    def __process_white_and_blacklist(whitelist, blacklist):
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


if __name__ == "__main__":

    whitelist = None
    whitelist = ["ALBUM"]

    mfs = Metadata("/home/johannes/Desktop/MusicManager/media/The_Mariana_Hollow/The_Abandoned_Parade_(2019)/01_Only_The_Fear.flac")
    m3 = Metadata("/home/johannes/Desktop/MusicManager/test/The_Mariana_Hollow/The_Abandoned_Parade_(2019)/01_Only_The_Fear.mp3")
    mf = Metadata("/home/johannes/Desktop/MusicManager/test/The_Mariana_Hollow/The_Abandoned_Parade_(2019)/01_Only_The_Fear.flac")

    m3.import_tag(mfs, whitelist=whitelist, remove_other=True)
    m3.write_tag()

    mf.import_tag(mfs, whitelist=whitelist, remove_other=True)
    mf.write_tag()

    print(mfs, m3, mf)
