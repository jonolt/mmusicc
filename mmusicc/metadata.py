import yaml
import os
import mutagen
import mimetypes
import re

class MetadataDict(dict):

    def __init__(self, init_value=None):
        super().__init__()
        self._init_value = init_value
        if not Metadata.class_initialized:
            Metadata.init_class()
        for key in Metadata.list_tags:
            self[key] = init_value

    def reset(self):
        for key in list(self):
            self[key] = self._init_value


class Metadata:

    dry_run = False
    class_initialized = False
    path_config_yaml = "config.yaml"
    write_empty = True

    dict_config = None
    list_tags_sorted = None
    list_tags = None
    dict_tags_id3 = None
    dict_tags_str = None
    dict_auto_fill_org = None
    dict_auto_fill_rules = None

    @classmethod
    def init_class(cls):
        dicts = cls.get_dictionaries(cls.path_config_yaml)
        cls.dict_config = dicts.get("dict_config")
        # list_tags_sorted can contain none, while list_tags should not
        cls.list_tags_sorted = dicts.get("list_tags_sorted")
        cls.list_tags = dicts.get("list_tags")
        cls.dict_tags_id3 = dicts.get("dict_tags_id3")
        cls.dict_tags_str = dicts.get("dict_tags_str")
        cls.dict_auto_fill_rules = dicts.get("dict_auto_fill_rules")
        cls.class_initialized = True

    @classmethod
    def get_dictionaries(cls, path=None):
        # TODO autfill riles
        list_displ_tags = [None] * 20
        list_tags = list()
        dict_tags_id3 = dict()
        dict_tags_str = dict()
        dict_auto_fill_rules = dict()

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
            if len(value) == 4:
                dict_auto_fill_rules[key] = value[3]

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
            "list_tags_sorted": list_displ_tags,
            "list_tags": list_tags,
            "dict_tags_id3": dict_tags_id3,
            "dict_tags_str": dict_tags_str,
            "dict_auto_fill_rules": dict_auto_fill_rules,
        }

    def __init__(self, file, read_tag=True, autofill=False):
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

        self.dict_auto_fill_org = None

    @property
    def file_name(self):
        return os.path.splitext(os.path.basename(self._file_path))[0]

    def auto_fill_tag(self):
        if not self.dict_auto_fill_org:
            self.dict_auto_fill_org = MetadataDict(init_value=False)
        for tag in list(Metadata.dict_auto_fill_rules):
            rule = self.dict_auto_fill_rules.get(tag)
            val_test = self.dict_data.get(rule[0])
            val_regex = rule[1]
            try:
                val_parse = self.dict_data.get(rule[2])
            except KeyError:
                val_parse = rule[2]
            if val_regex is None:
                if isinstance(val_test, Empty):
                    self.dict_auto_fill_org[tag] = self.dict_data[tag]
                    self.dict_data[tag] = val_parse
            elif isinstance(val_regex, str):
                m = re.search(val_regex, val_test)
                if m:
                    self.dict_auto_fill_org[tag] = self.dict_data[tag]
                    self.dict_data[tag] = eval(val_parse)



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
                val = Empty()

            if isinstance(val, mutagen.id3.ID3TimeStamp):
                val = val.text
            elif Empty.is_empty(val):
                val = Empty()

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

            if Empty.is_empty(val):
                val = Empty()

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

        if not Metadata.dry_run:
            print("write")
            #self._file.save(v1=2, v2_version=4)

    def __write_tag_flac(self, remove_other=True):

        if self._file.tags and remove_other:
            self._file.delete()

        if self._file.tags is None:
            self._file.add_tags()

        for tag in self.list_tags:

            val = self.dict_data.get(tag)

            if Empty.is_empty(val):
                if Metadata.write_empty:
                    val = Empty.value
                else:
                    continue

            self._file.tags[tag] = val

        if not Metadata.dry_run:
            print("write")
            #self._file.save()

    def import_tag(self, source_meta, whitelist=None, blacklist=None,
                   remove_other=False):
        """import metadata from source meta object"""
        tags = Metadata.process_white_and_blacklist(whitelist, blacklist)
        for tag in self.list_tags:
            if tag in tags:
                self.dict_data[tag] = source_meta.dict_data[tag]
            else:
                if remove_other:
                    self.dict_data[tag] = None

    @staticmethod
    def process_white_and_blacklist(whitelist, blacklist):
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
        if mimetype[0] and "audio" in mimetype[0]:
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

        self.dict_auto_fill_org = None

    def auto_fill_tag(self):
        if not self.dict_auto_fill_org:
            self.dict_auto_fill_org = MetadataDict(init_value=False)
        for metadata in self.list_metadata:
            metadata.auto_fill_tag()
        self.__compare_tags()

    def read_tag(self):
        for metadata in self.list_metadata:
            metadata.read_tag()
        self.__compare_tags()

    def __compare_tags(self):
        for key in AlbumMetadata.list_tags:
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

        # tags = Metadata.process_white_and_blacklist(whitelist, blacklist)

        for metadata_self in self.list_metadata:
            for metadata_source in source_meta.list_metadata:
                if metadata_self.file_name == metadata_source.file_name:
                    metadata_self.import_tag(
                        metadata_source,
                        whitelist=whitelist,
                        blacklist=blacklist,
                        remove_other=remove_other)


class Empty(object):

    value = ""

    def __repr__(self):
        return "<none>"

    def __eq__(self, other):
        if isinstance(other, Empty):
            return True
        else:
            return False

    @staticmethod
    def is_empty(text):
        if text is None or isinstance(text, Empty) or text.strip() == "":
            return True
        else:
            return False

    #@property
    #def value(self):
    #    return Empty.value



class Div(object):

    def __init__(self, key=None, list_metadata=None):
        self._dict_values = dict()
        self._diff = None
        self._key_tag = None  # maybe not needed
        if key and list_metadata:
            self.add_metadata(key, list_metadata)

    def __repr__(self):
        return "<div>"

    def __eq__(self, other):
        if not isinstance(other, Div):
            return False
        equal = None
        for meta_a in list(self._dict_values):
            for meta_b in list(other._dict_values):
                if meta_a.file_name == meta_b.file_name:
                    if not self._dict_values.get(meta_a) == other._dict_values.get(meta_b):
                        equal = False
        if equal is None:
            equal = False
        return equal

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
