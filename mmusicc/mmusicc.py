import argparse
import logging
import os
import shutil
import sys
import textwrap

from mmusicc._init import init_formats, init_logging, init_allocationmap
from mmusicc.formats import loaders as audio_loader
from mmusicc.metadata import Metadata, AlbumMetadata
from mmusicc.util.misc import check_is_audio
from mmusicc.version import __version__ as package_version


class MmusicC:

    # TODO allow a predefined config file with all parser options to be passed

    def __init__(self, args):
        """Create a ViewControl object with the given options.
        Args:
            args (:list: string):
        """

        init_logging()
        init_formats()

        str_ext = "Supported Formats for Metadata: {}"\
            .format(list(audio_loader))

        parent_parser = argparse.ArgumentParser(
            add_help=False
        )
        parent_parser.add_argument('--path-config',
                                   action='store',
                                   help="file path to custom config file")
        parent_parser.add_argument('--ffmpeg-commands',
                                   action='store',
                                   # TODO this about a good system to pass
                                   #  detailed commands to ffmpeg and provide
                                   #  an easy interface at the same time
                                   )
        tmp_double_txt_2 = "Can be passed as file (Plain text file, " \
                           "#containing " \
                           "tags separated with a new line) or as one or " \
                           "multiple arguments"
        parent_parser.add_argument('--white-list-tags',
                                   nargs='+',
                                   action='store',
                                   help="Tags to be whitelisted. "
                                        + tmp_double_txt_2
                                   )
        parent_parser.add_argument('--black-list-tags',
                                   nargs='+',
                                   action='store',
                                   help="Tags to be blacklisted. "
                                        + tmp_double_txt_2
                                   )
        parent_parser.add_argument('--delete-existing-metadata',
                                   action='store_true',
                                   help="delete existing metadata on target "
                                        "files before writing.")
        group1 = parent_parser.add_mutually_exclusive_group()
        group1.add_argument('--only-meta',
                            action='store_true',
                            help="only sync meta, don't sync files")
        group1.add_argument('--only-files',
                            action='store_true',
                            help="only sync files, don't update metadata")
        parent_parser.add_argument('--update-files',
                                   action='store_true',
                                   help="compares creation date, if source "
                                        "is newer, target gets replaced")
        # TODO warning when only-metadata is set
        parent_parser.add_argument(
            '--dry-run',
            action='store_true',
            help="do everything as usual, but without writing (file and "
                 "database). It is recommended to use with --only-meta or "
                 "--only-files, otherwise errors are likely.")
        # TODO ensure this is really done

        parent_parser_2 = argparse.ArgumentParser(add_help=False)
        parent_parser_2.add_argument(
            '-f', '--format',
            action='store',
            required=True
        )

        parser = argparse.ArgumentParser(
            prog="MmusicC",
            formatter_class=argparse.RawDescriptionHelpFormatter,
            description=str_ext,
            epilog=textwrap.dedent(
                '''\
                metadata manager
                    *files are not matched filenames
                    *folder structures of source and target must be equal and matched 
                     by their filename and tree path starting from the given directory
                when using multiple inputs and outputs, files will be matched by path starting from the filename'
                '''),
        )
        parser.add_argument(
            '--version',
            action='version',
            version=package_version
        )
        subparsers = parser.add_subparsers(help='sub-command help')

        # create the parser for the "file" command
        parser_file = subparsers.add_parser(
            'file',
            parents=[parent_parser],
            description=str_ext,
            help='synchronizes a single file'
        )
        parser_file.add_argument(
            '-s', '--source',
            action='store',
            required=True,
            help="source file"
            )
        parser_file.add_argument(
            '-t', '--target',
            action='store',
            required=True,
            help="target file"
            )
        parser_file.set_defaults(func=self.process_file)

        # create the parser for the "album" command
        parser_album = subparsers.add_parser(
            'album',
            parents=[parent_parser, parent_parser_2],
            description=str_ext,
            help=('synchronizes a album folder. '
                  '(All audio files in directory level)'),
        )
        parser_album.add_argument(
            '-s', '--source',
            action='store',
            required=True,
            help="source album folder"
        )
        parser_album.add_argument(
            '-t', '--target',
            action='store',
            required=True,
            help="target album folder"
        )
        parser_album.set_defaults(func=self.process_album)

        # create the parser for the "folder" command
        parser_lib = subparsers.add_parser(
            'lib',
            parents=[parent_parser, parent_parser_2],
            description=str_ext,
            help=('synchronizes a music library. Walks through subfolders and '
                  'treats every folder without subfolders as album folder.')
        )
        parser_lib.add_argument(
            '-s', '--source',
            action='store',
            required=True,
            help="source root folder"
        )
        parser_lib.add_argument(
            '-t', '--target',
            action='store',
            required=True,
            help="target root folder"
        )

        parser_lib.set_defaults(func=self.process_folder)

        logging.debug("MmusicC running with arguments: {}".format(args))

        self.parser_result = parser.parse_args(args)

        if not self.parser_result.path_config:
            path_this_file = os.path.dirname(os.path.dirname(
                os.path.abspath(__file__)))
            self.parser_result.path_config = os.path.join(path_this_file,
                                                          "config.yaml")
            # TODO find better way to locate the config file,
            #  maybe change its position

        init_allocationmap(self.parser_result.path_config)

        self.run_files = not self.parser_result.only_meta
        self.run_meta = not self.parser_result.only_files

        try:
            self.format_extension = self.parser_result.format
            if '.' not in self.format_extension:
                self.format_extension = '.' + self.format_extension
        except AttributeError:
            pass

        if self.parser_result.white_list_tags:
            if len(self.parser_result.white_list_tags) == 1:
                if os.path.exists(self.parser_result.white_list_tags[0]):
                    pass
                    # TODO load file and read tags
        else:
            self.whitelist = self.parser_result.white_list_tags

        if self.parser_result.black_list_tags:
            if len(self.parser_result.black_list_tags) == 1:
                if os.path.exists(self.parser_result.black_list_tags[0]):
                    pass
                    # TODO load file and read tags
        else:
            self.blacklist = self.parser_result.black_list_tags

        # TODO compare with tag list to filter wrongs and print warning
        #      alternatively use allocation map to find the right one at both

        # TODO maybe already combine white and blacklist and print synced tags

        self.parser_result.func()

        sys.exit(0)

    def process_file(self):
        logging.info("processing file")

        file_source = os.path.abspath(self.parser_result.source)
        file_target = os.path.abspath(self.parser_result.target)
        self.handle_files(file_source, file_target)

    def process_album(self):
        logging.info("processing album")

        album_source = os.path.abspath(self.parser_result.source)
        album_target = os.path.abspath(self.parser_result.target)
        self.handle_album(album_source, album_target)

    def process_folder(self):
        logging.info("processing folder")

        root_source = os.path.abspath(self.parser_result.source)
        root_target = os.path.abspath(self.parser_result.target)

        gen = os.walk(root_source, topdown=True)
        for root, dirs, files in gen:
            if len(dirs) == 0:
                album_target = swap_base(root_source, root_target, root)
                self.handle_album(root, album_target)
            elif len(files) > 0:
                logging.info("Found files not in album {} at folder '{}'"
                             .format(files, root))

    def handle_files(self, file_source, file_target):
        if self.run_files and file_source and file_target:
            convert_file_with_ffmpeg(
                file_source,
                file_target,
                dry_run=self.parser_result.dry_run
            )
        if self.run_meta:
            meta_source = Metadata(file_source)
            meta_target = Metadata(file_target)
            meta_target.import_tags(
                meta_source,
                whitelist=self.whitelist,
                blacklist=self.blacklist,
                remove_other=self.parser_result.delete_existing_metadata
            )
            meta_target.write_tags(
                remove_other=self.parser_result.delete_existing_metadata
            )
        return

    def handle_album(self, album_source, album_target):
        if self.run_files and album_source and album_target:
            if not os.path.isdir(album_target):
                os.makedirs(album_target)
            for file in os.listdir(album_source):
                if check_is_audio(file):
                    file_source = os.path.join(album_source, file)
                    target_filename = os.path.splitext(file)[0] + '.flac'
                    # TODO add variable for target extension
                    file_target = os.path.join(album_target, target_filename)
                    convert_file_with_ffmpeg(
                        file_source,
                        file_target,
                        dry_run=self.parser_result.dry_run
                    )
        if self.run_meta:
            meta_source = AlbumMetadata(album_source)
            meta_target = AlbumMetadata(album_target)
            meta_target.import_tags(
                meta_source,
                whitelist=self.whitelist,
                blacklist=self.blacklist,
                remove_other=self.parser_result.delete_existing_metadata
            )
            meta_target.write_tags(
                remove_other=self.parser_result.delete_existing_metadata
            )


def swap_base(root_a, root_b, full_path):
    return os.path.join(root_b, full_path[len(root_a) + 1:])


def convert_file_with_ffmpeg(source, target, dry_run=False):
    # create folders if not already there
    if os.path.isfile(target):
        print("file exists returning")
        return
    if not dry_run:
        shutil.copyfile(source, target)
