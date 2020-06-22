#  Copyright (c) 2020 Johannes Nolte
#  SPDX-License-Identifier: GPL-3.0-or-later

import argparse
import datetime
import enum
import logging
import math
import os
import pathlib
import textwrap

from mmusicc._init import init_formats, init_logging, init_allocationmap
from mmusicc.formats import AudioFileError
from mmusicc.formats import loaders as audio_loader
from mmusicc.formats import types as audio_types
from mmusicc.metadata import Metadata, AlbumMetadata
from mmusicc.util.allocationmap import get_tags_from_strs
from mmusicc.util.ffmpeg import FFmpeg, FFRuntimeError
from mmusicc.util.misc import is_supported_audio, swap_base, process_white_and_blacklist
from mmusicc.version import __version__ as package_version

str_description_rqw = textwrap.dedent(
    """\
    Metadata and file syncing the following combination are possible:
      - file   --> file
      - file   --> parent folder (target name is generated from source)
      - folder --> folder        (use --album to not to move through tree)
      - folder --> db            (full path as primary key)
      - db     --> folder        (key matching starts at leave of path)

    Supported Formats: 
    {}
    in Containers:
    {}
    """
)


# noinspection PyMethodMayBeStatic
class MmusicC:

    # TODO allow a predefined config file with all parser options to be passed

    def __init__(self, args):
        """Create a mmusicc object with the given options.
        Args:
            args (:list: string):
        """

        # the arguments the pre parser parses are identical to the main parser. This
        # allows for a nice help printout, but certain args parsed early on.
        pre_parser = argparse.ArgumentParser(add_help=False)
        pre_parser.add_argument(
            "-v", "--verbose", action="count", default=0,
        )
        pre_parser.add_argument(
            "--log-file", action="store",
        )
        parsed, remaining = pre_parser.parse_known_args(args)
        self.pre_result_verbose = parsed.verbose
        self.pre_result_logfile = parsed.log_file

        if self.pre_result_verbose == 0:
            log_level = 25
        elif self.pre_result_verbose == 1:
            log_level = logging.INFO
        else:
            log_level = logging.DEBUG

        self._log_path = init_logging(log_level, file_path=self.pre_result_logfile)
        init_formats()

        str_description = str_description_rqw.format(
            textwrap.fill(str(sorted([t.format for t in audio_types]))),
            textwrap.fill(str(sorted(list(audio_loader)))),
        )

        # noinspection PyTypeChecker
        self.parser = argparse.ArgumentParser(
            prog="mmusicc",
            formatter_class=argparse.RawDescriptionHelpFormatter,
            description=str_description,
            # epilog="",
            add_help=False,
            allow_abbrev=True,
        )

        pg_required = self.parser.add_argument_group("Required Options")
        pg_general = self.parser.add_argument_group("General Options")
        pg_conversion = self.parser.add_argument_group("File Conversion")
        pg_meta = self.parser.add_argument_group("Metadata Syncing")

        group_source = pg_required.add_mutually_exclusive_group(required=True)
        group_source.add_argument(
            "-s", "--source", action="store", help="source file/album/lib-root.",
        )
        group_source.add_argument(
            "-sdb",
            "--source-db",
            action="store",
            help="source database (SQLite database file or (not tested) database URL.",
        )

        group_target = pg_required.add_mutually_exclusive_group(required=True)
        group_target.add_argument(
            "-t", "--target", action="store", help="target file/album/lib-root.",
        )
        group_target.add_argument(
            "-tdb", "--target-db", action="store", help="target database.",
        )

        pg_general.add_argument(
            "-h",
            "--help",
            action="help",
            default=argparse.SUPPRESS,
            help="Show this help message and exit.",
        )
        pg_general.add_argument("--version", action="version", version=package_version)
        pg_general.add_argument(
            "--album", action="store_true", help="only sync folder level",
        )
        group1 = pg_general.add_mutually_exclusive_group()
        group1.add_argument(
            "--only-meta",
            action="store_true",
            help="only sync meta, don't sync files. "
            "Auto set when syncing from/to database.",
        )
        group1.add_argument(
            "--only-files",
            action="store_true",
            help="only sync files, don't update metadata.",
        )
        pg_general.add_argument(
            "--dry-run",
            action="store_true",
            help="do everything as usual, but without writing (file and "
            "database). It is recommended to use with --only-meta or "
            "--only-files, otherwise errors are likely.",
        )
        pg_general.add_argument(
            "-v",
            "--verbose",
            action="count",
            default=0,
            help="print log messages. can be stacked up to 2 (info, debug).",
        )
        pg_general.add_argument(
            "-a", "--all", action="store_true", help="print log for unchanged files.",
        )
        pg_general.add_argument(
            "--log-file",
            action="store",
            help="Log file for detailed logging at DEBUG level. "
            "If file exist log is appended.",
        )

        pg_conversion.add_argument(
            "-f",
            "--format",
            action="store",
            required=False,
            help="output container format of ffmpeg conversion "
            "(ignored when target is file_path).",
        )
        pg_conversion.add_argument(
            "-o",
            "--ffmpeg-options",
            action="store",
            help="conversion options for ffmpeg conversion, if empty ffmpeg defaults "
            "are used. It is recommended to test them directly with ffmpeg before "
            "they are used with mmusicc.",
        )

        tmp_double_txt_2 = (
            "Can be passed as file (Plain text file, "
            "#containing "
            "tags separated with a new line) or as one or "
            "multiple arguments."
        )
        pg_meta.add_argument(
            "--white-list-tags",
            nargs="+",
            action="store",
            help="Tags to be whitelisted. " + tmp_double_txt_2,
        )
        pg_meta.add_argument(
            "--black-list-tags",
            nargs="+",
            action="store",
            help="Tags to be blacklisted. " + tmp_double_txt_2,
        )
        pg_meta.add_argument(
            "--lazy-import",
            action="store_true",
            help="do not overwrite an existing non-None tag with None when importing "
            "metadata. Therefore,  if a tag is not excluded in the source it is "
            "not deleted in the target and the tag in the target remains "
            "unchanged.",
        )
        pg_meta.add_argument(
            "--delete-existing-metadata",
            action="store_true",
            help="delete existing metadata from target. This includes all defined, "
            "and unprocessed tags.",
        )
        pg_meta.add_argument(
            "--path-config", action="store", help="file path to custom config file.",
        )

        logging.debug("mmusicc running with arguments: {}".format(args))

        self.result = self.parser.parse_args(args)

        Metadata.dry_run = self.result.dry_run

        if not self.result.path_config:
            path_folder_this_file = pathlib.Path(__file__).resolve().parent
            self.result.path_config = path_folder_this_file.joinpath(
                "data", "config.yaml"
            )

        try:
            init_allocationmap(self.result.path_config)
        except FileNotFoundError:
            self.parser.error("path to config file not found")

        self.run_files = not self.result.only_meta
        self.run_meta = not self.result.only_files

        self.db_url = None
        if self.result.source:
            self.source = pathlib.Path(self.result.source).expanduser().resolve()
        else:
            self.source = None
            self.db_url = self.result.source_db

        if self.result.target:
            self.target = pathlib.Path(self.result.target).expanduser().resolve()
        else:
            self.target = None
            self.db_url = self.result.target_db

        if self.db_url:
            if Metadata.is_linked_database:
                Metadata.unlink_database()
            Metadata.link_database(self.db_url)

        self.source_type = self.get_element_type(self.source)
        self.target_type = self.get_element_type(self.target)

        if not (self.source or self.target) and self.run_files:
            self.parser.error("Target or source is database! I can only run meta!")

        if not self.source and not self.target:
            self.parser.error("Can't sync from database to database!")

        if self.source and self.target:
            self.format_extension = None
            if self.target_type == MmusicC.ElementType.file:
                if "." in self.target.suffix:  # target is file
                    self.format_extension = self.target.suffix

            if not self.format_extension and self.result.format:
                # target is folder an format has to be given!
                self.format_extension = self.result.format
                if "." not in self.format_extension:
                    self.format_extension = "." + self.format_extension

            if not self.format_extension:
                self.parser.error(
                    "the following arguments are required: "
                    "-f/--format, except at file-->file and "
                    "album/lib-->database operations."
                )

        self.whitelist = None
        try:
            if self.result.white_list_tags:
                self.whitelist = load_tags_from_list_or_file(
                    self.result.white_list_tags
                )
        except KeyError as err:
            self.parser.error(
                "Whitelist: {}. If input is file it is not found.".format(err)
            )

        self.blacklist = None
        try:
            if self.result.black_list_tags:
                self.blacklist = load_tags_from_list_or_file(
                    self.result.black_list_tags
                )
        except KeyError as err:
            self.parser.error(
                "Blacklist: {}. If input is file it is not found.".format(err)
            )

        # just fot the log
        if self.whitelist or self.blacklist:
            whitelist = process_white_and_blacklist(self.whitelist, self.blacklist)
            logging.info("Tags to be Synced: {}".format(whitelist))

        # stats for report
        self.unchanged = 0
        self.created = 0
        self.metadata = 0
        self.both = 0
        self.error = 0
        time_start = datetime.datetime.now()

        string_opt_args = ""
        for att in [
            "album",
            "delete_existing_metadata",
            "dry_run",
            "lazy_import",
            "only_files",
            "only_meta",
            "log_file",
            "all",
        ]:
            if getattr(self.result, att, None):
                string_opt_args += f"{att}={getattr(self.result, att)}; "

        options = [
            f"             Running mmusicc",
            f"source type: {self.source_type}",
            f"source path: {self.source if self.source else self.db_url}",
            f"target type: {self.target_type}",
            f"target path: {self.target if self.target else self.db_url}",
            f"format     : {getattr(self, 'format_extension', '')}"
            f"{' | ' if self.result.ffmpeg_options else ''}"
            f"{self.result.ffmpeg_options if self.result.ffmpeg_options else ''}",
            f"options    : {string_opt_args[:-2]}",
            f"path config: {self.result.path_config}",
        ]

        for o in options:
            logging.log(25, o)

        logging.log(25, "---------------------------------------------------------")

        if self.db_url:
            if self.source_type == MmusicC.ElementType.file:
                self.handle_media2db(self.source)
            elif self.source_type == MmusicC.ElementType.folder:
                if self.result.album:
                    self.handle_media2db(self.source)
                else:
                    gen = os.walk(self.source, topdown=True)
                    for root, dirs, files in gen:
                        audio_files = [
                            file for file in files if is_supported_audio(file)
                        ]
                        if len(audio_files) > 0:
                            self.handle_media2db(root)
            elif self.target_type == MmusicC.ElementType.file:
                self.handle_db2media(self.target)
            elif self.target_type == MmusicC.ElementType.folder:
                if self.result.album:
                    self.handle_db2media(self.target)
                else:
                    gen = os.walk(self.target, topdown=True)
                    for root, dirs, files in gen:
                        audio_files = [
                            file for file in files if is_supported_audio(file)
                        ]
                        if len(audio_files) > 0:
                            self.handle_db2media(root)

        elif self.source_type == MmusicC.ElementType.file:
            self.handle_files2file(self.source, self.target)

        elif self.source_type == MmusicC.ElementType.folder:
            if self.result.album:
                self.handle_album2album(self.source, self.target)
            else:
                logging.debug(
                    "Walking through tree of directory '{}'".format(self.source)
                )
                gen = os.walk(self.source, topdown=True)
                for root, dirs, files in gen:
                    root = pathlib.Path(root)
                    album_target = swap_base(self.source, root, self.target)
                    logging.info("Current root: {}".format(root))

                    if any(is_supported_audio(f) for f in files):
                        if self.target_type == MmusicC.ElementType.folder:
                            self.handle_album2album(root, album_target)
                        else:
                            self.handle_media2db(root)

                    # i like when singles have their own folder like albums have
                    if len(files) > 0 and len(dirs) > 0:
                        logging.info(
                            "Found files not in album {} at folder '{}'".format(
                                files, root
                            )
                        )

        time_delta = datetime.datetime.now() - time_start

        if self.created + self.metadata + self.both > 0 or self.result.all:
            logging.log(25, "---------------------------------------------------------")

        report = [
            f"Total Time : {math.floor(time_delta.total_seconds() / 60)} min "
            f"{math.fmod(time_delta.total_seconds(), 60)} s",
            f"Unchanged  : {self.unchanged}",
            f"Metadata   : {self.metadata}",
            f"Created    : {self.created}",
            f"Both       : {self.both}",
            f"Errors     : {self.error}",
        ]

        if self.target is MmusicC.ElementType.database:
            logging.log(25, report[1])
        else:
            for r in report:
                logging.log(25, r)

    # __init___

    def handle_files2file(self, file_source, file_target):
        if not is_supported_audio(file_source):
            logging.warning(f"file '{file_source}' not a supported audio file.")
            return -1
        logging.debug(f"handle_files2file: {file_source}->{file_target}")
        # compute filename when only target folder is given
        if self.get_element_type(file_target) == MmusicC.ElementType.folder:
            file_target = file_target.joinpath(file_source.stem + self.format_extension)
        change = 0
        change += self._handle_files2file_file(file_source, file_target)
        if change < 0:
            return change
        change += self._handle_files2file_meta(file_source, file_target)
        self.log_changes(change, file_target, make_relative=False)
        return change

    def _handle_files2file_file(self, file_source, file_target):
        if self.run_files and file_source and file_target:
            if file_target.is_file():
                logging.debug(f"ffmpeg skipped target file exists: '{file_target}'")
            elif not self.result.dry_run:
                with FFmpeg(
                    file_source, file_target, options=self.result.ffmpeg_options,
                ) as ffmpeg:
                    try:
                        ffmpeg.run()
                        return 2
                    except FFRuntimeError as ex:
                        tmp_msg = [str(file_target.relative_to(self.target))]
                        last3 = ex.stderr.split("\n")[-4:-1]
                        tmp_msg.extend(last3)
                        tmp_msg_str = ("\n" + " " * 5).join(tmp_msg)
                        logging.log(25, f"ffmpeg error: {tmp_msg_str}")
                        return -2
        return 0

    def _handle_files2file_meta(self, file_source, file_target):
        if self.run_meta:
            try:
                meta_source = Metadata(file_source)
                meta_target = Metadata(file_target)
                meta_target.import_tags(
                    meta_source,
                    whitelist=self.whitelist,
                    blacklist=self.blacklist,
                    skip_none=self.result.lazy_import,
                    clear_blacklisted=self.result.delete_existing_metadata,
                )
                return meta_target.write_tags(
                    remove_existing=self.result.delete_existing_metadata
                )
            except AudioFileError as ex:
                logging.info(ex)
                return -1
            except FileNotFoundError as ex:
                logging.info(ex)
                return -4
        return 0

    def handle_album2album(self, album_source, album_target):
        """
        Note:
            For the moment, it makes no difference if metadata is synced file by file as
            Metadata or album wise as AlbumMetadata. This will change, when the
            interactive mode with album wise comparison is introduced.
            Therefore the metadata syncing is currently done in run_files, except when
            the only-meta option is given.
        """
        logging.debug(f"handle_album2album: {album_source}->{album_target}")
        if self.run_files and album_source and album_target:
            changes_file = dict()
            if not album_target.is_dir():
                album_target.mkdir(parents=True)
            for file in sorted(os.listdir(album_source)):
                if is_supported_audio(file):
                    file_source = album_source.joinpath(file)
                    file_target = album_target.joinpath(
                        file_source.stem + self.format_extension
                    )
                    changes_file[file_target] = self._handle_files2file_file(
                        file_source, file_target
                    )
                    if self.run_meta:
                        changes_file[file_target] += self._handle_files2file_meta(
                            file_source, file_target
                        )
                    self.log_changes(changes_file[file_target], file_target)
                else:
                    logging.info(f"File is not supported or not valid: {file}")

        if self.run_meta and not self.run_files:
            if not album_target.is_dir():
                logging.warning(
                    "no target folder for given source '{}', "
                    "skipping".format(album_source)
                )
                return
            meta_source = AlbumMetadata(album_source)
            meta_target = AlbumMetadata(album_target)
            meta_target.import_tags(
                meta_source,
                whitelist=self.whitelist,
                blacklist=self.blacklist,
                skip_none=self.result.lazy_import,
                clear_blacklisted=self.result.delete_existing_metadata,
            )
            changes_meta = meta_target.write_tags(
                remove_existing=self.result.delete_existing_metadata
            )
            for file, change in changes_meta.items():
                self.log_changes(change, file)

    def handle_media2db(self, album_source):
        album_target = pathlib.Path(album_source)
        if album_target.is_file():
            meta_source = Metadata(album_source)
        else:
            meta_source = AlbumMetadata(album_source)
        meta_source.export_tags_to_db()

    def handle_db2media(self, album_target):
        album_target = pathlib.Path(album_target)
        if album_target.is_file():
            meta_target = Metadata(album_target)
        else:
            meta_target = AlbumMetadata(album_target)
        meta_target.import_tags_from_db(
            whitelist=self.whitelist,
            blacklist=self.blacklist,
            skip_none=self.result.lazy_import,
            clear_blacklisted=self.result.delete_existing_metadata,
        )
        meta_target.write_tags(remove_existing=self.result.delete_existing_metadata)

    def log_changes(self, change, file, make_relative=True):
        if file.is_absolute() and make_relative:
            file = file.relative_to(self.target)
        if change < 0:
            self.error += 1
        elif change > 0:
            if change == 1:
                self.metadata += 1
            elif change == 2:
                self.created += 1
            elif change == 3:
                self.both += 1
        else:
            self.unchanged += 1
            if not self.result.all:
                logging.info(f"{change} > {file}")
                return

        logging.log(25, "{: d} > {}".format(change, file))

    def get_element_type(self, element):
        """Get the element type based on the pathlib.Path object.

        Instance method in clarifying that the function is instance dependent.

        """

        if not element:
            if Metadata.is_linked_database:
                return MmusicC.ElementType.database
            else:
                return MmusicC.ElementType.other

        if element.suffix in audio_loader.keys():  # target is file
            if element.exists():
                if not is_supported_audio(element):
                    self.parser.error(f"File '{element}' not supported!")
            return MmusicC.ElementType.file
        else:
            if "." in element.suffix:
                logging.info(
                    f"Path identified as folder, although it can also be an "
                    f"unsupported file with extension {element.suffix}"
                )
            return MmusicC.ElementType.folder

    class ElementType(enum.Enum):
        file = (1,)
        folder = (2,)
        database = (3,)
        other = 4


def load_tags_from_list_or_file(list_tags_or_file):
    """Load TAG-list from a list of STRING or a file.

    Where each tag (STRING) is separated by newline.

    Args:
        list_tags_or_file (list of str or str): list of tags or file_path

    Returns:
        list of str: TAGs

    """
    if len(list_tags_or_file) == 1:
        path = pathlib.Path(list_tags_or_file[0])
        if path.exists():
            with path.open(mode="r") as f:
                list_tags_or_file = [line.rstrip() for line in f]
    return get_tags_from_strs(list_tags_or_file)
