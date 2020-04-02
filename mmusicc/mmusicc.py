import argparse
import enum
import logging
import os
import sys
import textwrap

import mmusicc.util.allocationmap as am
from mmusicc._init import init_formats, init_logging, init_allocationmap
from mmusicc.formats import loaders as audio_loader
from mmusicc.metadata import Metadata, AlbumMetadata
from mmusicc.util.ffmpeg import FFmpeg, FFRuntimeError, \
    FFExecutableNotFoundError
from mmusicc.util.misc import check_is_audio, swap_base, \
    process_white_and_blacklist
from mmusicc.version import __version__ as package_version


class MmusicC:

    # TODO allow a predefined config file with all parser options to be passed

    def __init__(self, args):
        """Create a ViewControl object with the given options.
        Args:
            args (:list: string):
        """

        pre_parser = argparse.ArgumentParser(add_help=False)
        pre_parser.add_argument(
            '-v', '--verbose',
            action='count',
            default=0
        )
        parsed, remaining = pre_parser.parse_known_args(args)
        self.pre_result_verbose = parsed.verbose

        if self.pre_result_verbose == 0:
            log_level = 25
        elif self.pre_result_verbose == 1:
            log_level = logging.INFO
        else:
            log_level = logging.DEBUG

        init_logging(log_level)
        init_formats()

        str_description = textwrap.dedent(
            '''\
            metadata and file syncing the following combination are possible:
              - file   --> file
              - file   --> parent folder (target name is generated from source)
              - folder --> folder (use --album to not to move through tree)
              - folder --> db (full path as primary key)
              - db     --> folder (key matching starts at leave of path)
            
            Supported Formats for Metadata: 
            {}
            '''
            ).format(textwrap.fill(str(list(audio_loader))))

        parser = argparse.ArgumentParser(
            prog="MmusicC",
            formatter_class=argparse.RawDescriptionHelpFormatter,
            description=str_description,
            # epilog="",
            add_help=False
        )

        pg_required = parser.add_argument_group("Required Options")
        pg_general = parser.add_argument_group("General Options")
        pg_conversion = parser.add_argument_group("File Conversion")
        pg_meta = parser.add_argument_group("Metadata Syncing")

        group_source = pg_required.add_mutually_exclusive_group(required=True)
        group_source.add_argument(
            '-s', '--source',
            action='store',
            help="source file/album/lib-root"
        )
        group_source.add_argument(
            '-sdb', '--source-db',
            action='store',
            help="source database"
        )

        group_target = pg_required.add_mutually_exclusive_group(required=True)
        group_target.add_argument(
            '-t', '--target',
            action='store',
            help="target file/album/lib-root"
        )
        group_target.add_argument(
            '-tdb', '--target-db',
            action='store',
            help="target database"
        )

        pg_general.add_argument(
            '-h', '--help',
            action='help',
            default=argparse.SUPPRESS,
            help='Show this help message and exit.'
        )
        pg_general.add_argument(
            '--version',
            action='version',
            version=package_version
        )
        pg_general.add_argument(
            '--album',
            action='store_true',
            help="only sync folder level")
        group1 = pg_general.add_mutually_exclusive_group()
        group1.add_argument(
            '--only-meta',
            action='store_true',
            help="only sync meta, don't sync files. "
                 "Auto set when syncing from/to database")
        group1.add_argument(
            '--only-files',
            action='store_true',
            help="only sync files, don't update metadata")
        pg_general.add_argument(
            '--dry-run',
            action='store_true',
            help="do everything as usual, but without writing (file and "
                 "database). It is recommended to use with --only-meta or "
                 "--only-files, otherwise errors are likely.")
        pg_general.add_argument(
            '-v', '--verbose',
            action='count',
            default=0,
            help='print log messages. can be stacked up to 2 (info, debug)'
            # processed before argparser
        )
        # pg_general.add_argument(
        #     '-q', '--quiet',
        #     action='count',
        #     default='0',
        #     help='print log messages'
        # )

        pg_conversion.add_argument(
            '-f', '--format',
            action='store',
            required=False,
            help='output container format of ffmpeg conversion '
                 '(ignored when target is file_path)'
        )
        pg_conversion.add_argument(
            '--ffmpeg-options',
            action='store',
            help="conversion options for ffmpeg conversion. "
                 "If empty ffmpeg defaults are used."
        )

        tmp_double_txt_2 = "Can be passed as file (Plain text file, " \
                           "#containing " \
                           "tags separated with a new line) or as one or " \
                           "multiple arguments"
        pg_meta.add_argument(
            '--white-list-tags',
            nargs='+',
            action='store',
            help="Tags to be whitelisted. "
                 + tmp_double_txt_2
        )
        pg_meta.add_argument(
            '--black-list-tags',
            nargs='+',
            action='store',
            help="Tags to be blacklisted. "
                 + tmp_double_txt_2
        )
        pg_meta.add_argument(
            '--lazy',
            action='store_true',
            help="don't overwrite existing value in target with None from "
                 "source")
        pg_meta.add_argument(
            '--delete-existing-metadata',
            action='store_true',
            help="delete existing metadata on target "
                 "files before writing.")
        pg_meta.add_argument(
            '--path-config',
            action='store',
            help="file path to custom config file")

        logging.debug("MmusicC running with arguments: {}".format(args))

        self.result = parser.parse_args(args)

        if not self.result.path_config:
            path_folder_this_file = os.path.dirname(os.path.abspath(__file__))
            self.result.path_config = \
                os.path.join(path_folder_this_file, "data", "config.yaml")

        try:
            init_allocationmap(self.result.path_config)
        except FileNotFoundError:
            parser.error("path to config file not found")

        self.run_files = not self.result.only_meta
        self.run_meta = not self.result.only_files

        db_url = None
        if self.result.source:
            self.source = os.path.abspath(
                os.path.expanduser(self.result.source))
        else:
            self.source = None
            db_url = self.result.source_db

        if self.result.target:
            self.target = os.path.abspath(
                os.path.expanduser(self.result.target))
        else:
            self.target = None
            db_url = self.result.target_db

        if db_url:
            if Metadata.is_linked_database:
                Metadata.unlink_database()
            Metadata.link_database(db_url)

        self.source_type = get_element_type(self.source)
        self.target_type = get_element_type(self.target)
        logging.info("Source is '{}'. Target is '{}'.".
                     format(self.source_type, self.target_type))

        if not (self.source or self.target) and self.run_files:
            parser.error("Target or source is database! I can only run meta!")

        if not self.source and not self.target:
            parser.error("Can't sync from database to database!")

        if self.source and self.target:
            self.format_extension = None
            if os.path.isfile(self.result.source):
                ext = os.path.splitext(self.result.target)
                if '.' in ext[1]:  # target is file
                    self.format_extension = ext[1]

            if not self.format_extension and self.result.format:
                # target is folder an format has to be given!
                self.format_extension = self.result.format
                if '.' not in self.format_extension:
                    self.format_extension = '.' + self.format_extension

            if not self.format_extension:
                parser.error("the following arguments are required: "
                             "-f/--format, except at file-->file and "
                             "album/lib-->database operations.")

        self.whitelist = None
        try:
            if self.result.white_list_tags:
                if len(self.result.white_list_tags) == 1 \
                        and os.path.exists(self.result.white_list_tags[0]):
                    self.blacklist = load_tags_from_file(
                        self.result.white_list_tags[0])
                else:
                    self.whitelist = \
                        get_tag_from_str(self.result.white_list_tags)
        except KeyError as err:
            parser.error("Whitelist: {}. If input is file it is mot found."
                         .format(err))

        self.blacklist = None
        try:
            if self.result.black_list_tags:
                if len(self.result.black_list_tags) == 1 \
                        and os.path.exists(self.result.black_list_tags[0]):
                    self.blacklist = load_tags_from_file(
                        self.result.black_list_tags[0])
                else:
                    self.blacklist = \
                        get_tag_from_str(self.result.black_list_tags)
        except KeyError as err:
            parser.error("Blacklist: {}. If input is file it is mot found."
                         .format(err))

        # just fot the log
        if self.whitelist or self.blacklist:
            whitelist = \
                process_white_and_blacklist(self.whitelist, self.blacklist)
            logging.info("Tags to be Synced: {}".format(whitelist))

        if self.source_type == ElementType.file:
            # if source if file, target must be file to
            if self.target_type == ElementType.folder:
                basename = os.path.basename(self.source)
                filename = os.path.splitext(basename)[0]
                self.target = os.path.join(
                    self.target, filename + self.format_extension)
            self.handle_files2file(self.source, self.target)

        elif self.source_type == ElementType.folder:
            # if source is folder target must be folder or database
            if self.result.album:
                self.handle_album2album(self.source, self.target)
            else:
                logging.debug("Walking through tree of directory '{}'"
                              .format(self.source))
                gen = os.walk(self.source, topdown=True)
                for root, dirs, files in gen:
                    album_target = swap_base(self.source, self.target, root)
                    logging.debug('Current root: {}'.format(root))
                    if len(dirs) == 0:
                        if self.target_type == ElementType.folder:
                            self.handle_album2album(root, album_target)
                        else:
                            self.handle_album2db(root)
                    elif len(files) > 0:
                        self.handle_album2album(root, album_target)
                        logging.info(
                            "Found files not in album {} at folder '{}'"
                            .format(files, root))
        else:  # source is database
            gen = os.walk(self.target, topdown=True)
            for root, dirs, files in gen:
                if len(dirs) == 0:
                    self.handle_db2album(root)
                elif len(files) > 0:
                    logging.info("Found files not in album {} at folder '{}'"
                                 .format(files, root))

        sys.exit(0)

    def handle_files2file(self, file_source, file_target):
        if get_element_type(file_target) == ElementType.folder:
            basename = os.path.basename(file_source)
            filename = os.path.splitext(basename)[0]
            file_target = os.path.join(
                file_target, filename + self.format_extension)
        if self.run_files and file_source and file_target:
            convert_file_with_ffmpeg(
                file_source,
                file_target,
                dry_run=self.result.dry_run,
                options=self.result.ffmpeg_options
            )
        if self.run_meta:
            meta_source = Metadata(file_source)
            meta_target = Metadata(file_target)
            meta_target.import_tags(
                meta_source,
                whitelist=self.whitelist,
                blacklist=self.blacklist,
                skip_none=self.result.lazy,
            )
            meta_target.write_tags(
                remove_existing=self.result.delete_existing_metadata
            )
        return

    def handle_album2album(self, album_source, album_target):
        if self.run_files and album_source and album_target:
            if not os.path.isdir(album_target):
                os.makedirs(album_target)
            for file in os.listdir(album_source):
                if check_is_audio(file):
                    file_source = os.path.join(album_source, file)
                    self.handle_files2file(file_source, album_target)
        if self.run_meta:
            meta_source = AlbumMetadata(album_source)
            meta_target = AlbumMetadata(album_target)
            meta_target.import_tags(
                meta_source,
                whitelist=self.whitelist,
                blacklist=self.blacklist,
                skip_none=self.result.lazy,
            )
            meta_target.write_tags(
                remove_existing=self.result.delete_existing_metadata
            )

    def handle_album2db(self, album_source):
        meta_source = AlbumMetadata(album_source)
        meta_source.export_tags_to_db()

    def handle_db2album(self, album_target):
        meta_target = AlbumMetadata(album_target)
        meta_target.import_tags_from_db(
            whitelist=self.whitelist,
            blacklist=self.blacklist,
            skip_none=self.result.lazy
        )
        meta_target.write_tags(
            remove_existing=self.result.delete_existing_metadata
        )


def load_tags_from_file(path):
    if not os.path.exists(path):
        raise FileNotFoundError("File '{}' with tags not found.".format(path))
    with open(path, 'r') as f:
        lines = [line.rstrip() for line in f]
    return get_tag_from_str(lines)


def get_tag_from_str(tags):
    ret_tag = list()
    for string in tags:
        try:
            ret_tag.append(am.dict_str2tag[string])
        except KeyError:
            raise KeyError("String '{}' could not be associated with any tag."
                           .format(string))
    return ret_tag


def convert_file_with_ffmpeg(source, target, options=None, dry_run=False):
    # create folders if not already there
    if os.path.isfile(target):
        logging.info("target file exists, ffmpeg skipped, returning")
        return
    if not dry_run:
        try:
            FFmpeg(source, target, options=options).run()
        except FFExecutableNotFoundError:
            logging.error("ffmpeg path not found. either ffmpeg is not "
                          "installed are not at the standard path.")
            raise
        except FFRuntimeError as ex:
            logging.error("command \n{}\n produced the following error:\n {}"
                          .format(ex.cmd, ex.stderr))
            raise


def get_element_type(element):
    if not element:
        return ElementType.database
    ext = os.path.splitext(element)
    if '.' in ext[1]:  # target is file
        return ElementType.file
    else:
        return ElementType.folder


class ElementType(enum.Enum):
    file = 1,
    folder = 2,
    database = 3,
