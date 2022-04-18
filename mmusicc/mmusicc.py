#  Copyright (c) 2020 Johannes Nolte
#  SPDX-License-Identifier: GPL-3.0-or-later

import argparse
import datetime
import enum
import logging
import math
import os
import pathlib
import shutil
import textwrap

from mmusicc._init import init_formats, init_logging, init_allocationmap
from mmusicc.formats import loaders as audio_loader
from mmusicc.formats import types as audio_types
from mmusicc.formats import is_supported_audio
from mmusicc.metadata import Metadata, GroupMetadata, parse_path_to_metadata
from mmusicc.util.allocationmap import get_tags_from_strs
from mmusicc.util.ffmpeg import FFmpeg, FFRuntimeError
from mmusicc.util.misc import process_white_and_blacklist
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
            "-v",
            "--verbose",
            action="count",
            default=0,
        )
        pre_parser.add_argument(
            "--log-file",
            action="store",
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

        # Set up logging. From here on stuff is getting logged.
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
            "-s",
            "--source",
            action="store",
            help="source file/album/lib-root.",
        )
        group_source.add_argument(
            "-sdb",
            "--source-db",
            action="store",
            help="source database (SQLite database file or (not tested) database URL.",
        )

        group_target = pg_required.add_mutually_exclusive_group(required=True)
        group_target.add_argument(
            "-t",
            "--target",
            action="store",
            help="target file/album/lib-root.",
        )
        group_target.add_argument(
            "-tdb",
            "--target-db",
            action="store",
            help="target database.",
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
            "--album",
            action="store_true",
            help="only sync folder level",
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
        group1.add_argument(
            "--delete-files",
            action="store_true",
            help="delete audio files and folders that are not in source."
            "While Non Audio Files and Folder are ignored, all files "
            "regardless of type are deleted when their containing audio "
            "folder is deleted.",
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
            "-a",
            "--all",
            action="store_true",
            help="print log for unchanged files.",
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
            "--path-config",
            action="store",
            help="file path to custom config file.",
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
        # not really needed but should improve readability
        self.run_both = self.run_files & self.run_meta

        self.db_url = None
        self.source = None
        self.target = None

        if self.result.source:
            self.source = pathlib.Path(self.result.source).expanduser().resolve()
            # TODO asume album if source has no subfolders
        else:
            # self.source = None
            self.db_url = self.result.source_db

        if self.result.target:
            self.target = pathlib.Path(self.result.target).expanduser().resolve()
        else:
            # self.target = None
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
            # as db is linked as class attribute only one can exist!

        if self.source and self.target:
            self.format_extension = None

            # FIXME file extension beats format specifier, correct?
            if self.target_type == MmusicC.ElementType.file:
                # if "." in self.target.suffix:  # target is file
                self.format_extension = self.target.suffix

            if not self.format_extension and self.result.format:
                # target is folder a format has to be given!
                self.format_extension = self.result.format
                if "." not in self.format_extension:
                    self.format_extension = "." + self.format_extension

            if not self.format_extension:
                self.parser.error(
                    "the following arguments are required: "
                    "-f/--format, except at file-->file and "
                    "album/lib-->database operations."
                )

        if (
            self.source_type == MmusicC.ElementType.file
            and self.target_type == MmusicC.ElementType.folder
        ):
            logging.debug("target and target type will be changed below!")

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
        self.deleted = 0
        time_start = datetime.datetime.now()

        string_opt_args = ""
        for att in [
            "album",
            "delete_existing_metadata",
            "dry_run",
            "lazy_import",
            "only_meta",
            "only_files",
            "delete_files",
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

        # noinspection PyShadowingNames
        def walk_album(root_path):
            # initially it is assumed that every folder is an album
            # using os path tp keep using strings
            folders = sorted([x[0] for x in os.walk(root_path)])
            # if len(folders) == 0:
            #     return root_path,  {root_path: ""}
            # elif len(folders) == 1:
            if len(folders) == 0:
                raise Exception(
                    "no subfolders found if it is an album pleacey applecozly specifiy album option"
                )
            if len(folders) == 1:
                return root_path, {root_path: ""}

            common_path = os.path.commonpath(folders)
            folders = [os.path.relpath(p, common_path) for p in folders][1:]
            albums = dict()
            for folder_path in folders:
                try:
                    albums[folder_path] = os.path.join(common_path, folder_path)
                except ValueError:
                    pass

            return common_path, albums

        self.source_common_path = None
        self.source_tree = None
        self.target_common_path = None
        self.target_tree = None
        self.target_delete_tree = None

        self.error_occurred_flag = False

        # create a content tree
        if self.source_type == MmusicC.ElementType.folder:
            if self.result.album:
                self.source_common_path = self.source
                self.source_tree = {self.source: parse_path_to_metadata(self.source)}
            else:
                common_path, album = walk_album(self.source)
                self.source_common_path = pathlib.Path(common_path)
                self.source_tree = {
                    k: parse_path_to_metadata(v) for k, v in album.items()
                }
        elif self.source_type == MmusicC.ElementType.file:
            self.source_common_path = self.source.parent
            self.source_tree = {"": parse_path_to_metadata(self.source, is_file=True)}

        if self.target_type == MmusicC.ElementType.folder:
            if self.source_type == MmusicC.ElementType.file:  # file->folder
                self.target_common_path = self.target
                self.target_type = MmusicC.ElementType.file
                # from here on file->folder as handled as file->file
                self.target = self.target_common_path.joinpath(
                    self.source.name
                ).with_suffix(self.format_extension)
            elif self.result.album:
                # album get some special treatment
                self.target_common_path = self.target
                if not self.target_common_path.exists():
                    if self.target_common_path.parent.exists():
                        self.target_common_path.mkdir()
                    else:
                        raise FileNotFoundError(
                            "Nor the target folder or ist parent exists. The target "
                            "folder can only be automatically created if its parent "
                            "does exist!"
                        )
                self.target_tree = {
                    self.target: parse_path_to_metadata(self.target, link_mode="try")
                }
            else:
                common_path, album = walk_album(self.target)
                self.target_common_path = pathlib.Path(common_path)
                self.target_tree = {
                    k: parse_path_to_metadata(v, link_mode="try")
                    for k, v in album.items()
                }

        # using if instead of elif as target type might be changed in previous condition
        if self.target_type == MmusicC.ElementType.file:
            self.target_common_path = self.target.parent
            self.target_tree = {
                "": parse_path_to_metadata(
                    self.target,
                    is_file=True,
                    link_mode="try" if self.run_files else "raise",
                )
            }

        if self.db_url:
            # copy metadata to or from file depending on if its source or target
            # TODO this must create a output to (especially for db-->file/folder
            if self.source_tree:
                for metadata in self.source_tree.values():
                    if metadata is None:
                        continue
                    metadata.export_tags_to_db()
            if self.target_tree:  # is subclass metadata not string ?
                for metadata in self.target_tree.values():
                    if metadata is None:
                        continue
                    metadata.import_tags_from_db(
                        whitelist=self.whitelist,
                        blacklist=self.blacklist,
                        skip_none=self.result.lazy_import,
                        clear_blacklisted=self.result.delete_existing_metadata,
                    )
                    metadata.write_tags(
                        remove_existing=self.result.delete_existing_metadata
                    )
        else:  # only file/folder --> file/folder is left

            if (
                self.result.delete_files
                and self.target_type == MmusicC.ElementType.folder
            ):

                logging.log(
                    25, "---------------------------------------------------------"
                )
                logging.log(25, "Deleting Folders ...")

                diff = set(self.target_tree).difference(self.source_tree)
                # the sorting ensures we start with the deepest directory
                diff = sorted(diff, key=len, reverse=True)

                def remove_metadata_file(metadata_obj: Metadata):
                    try:
                        metadata_obj.unlink_audio_file()
                        # TODO add option moving file to trash can
                        metadata_obj.file_path.unlink()
                        self.deleted += 1
                        logging.log(25, f". {metadata_obj.file_path}")
                    except FileNotFoundError:
                        self.error += 1
                        logging.log(25, f"E {metadata_obj.file_path}")

                for path in diff:
                    o = self.target_tree[path]
                    if isinstance(o, GroupMetadata):
                        for metadata in o.list_metadata:
                            remove_metadata_file(metadata)
                    elif isinstance(o, Metadata):
                        remove_metadata_file(o)

                    # remove all other none audio files then delete folder
                    if isinstance(o, GroupMetadata) or o is None:
                        dir_path = self.target_common_path.joinpath(path)
                        for file_path in dir_path.iterdir():
                            if file_path.is_file():
                                file_path.unlink()
                                logging.log(
                                    25,
                                    f"  {file_path.relative_to(self.target_common_path)}",
                                )
                            else:
                                logging.warning(
                                    f"resource {file_path} is not a file, aborting deletion of folder {dir_path}"
                                )
                                break
                        else:  # break should never happen
                            dir_path.rmdir()
                            logging.log(
                                25, f"  {dir_path.relative_to(self.target_common_path)}"
                            )

                    self.target_tree.pop(path)

                logging.log(
                    25, "---------------------------------------------------------"
                )
                logging.log(25, "Deleting Files (in albums) ... ")

                # source and target tree folders should now be equal
                for path in self.source_tree:
                    if isinstance(self.source_tree[path], GroupMetadata):
                        files_source = {
                            m.file_path.stem: m
                            for m in self.source_tree[path].list_metadata
                        }
                        files_target = {
                            m.file_path.stem: m
                            for m in self.target_tree[path].list_metadata
                        }
                        diff = set(files_target) - set(files_source)
                        for file in diff:
                            meta_obj = self.target_tree[path].remove_metadata(
                                files_target[file]
                            )
                            remove_metadata_file(meta_obj)

                logging.log(25, "---------------------------------------------------------")
            logging.log(25, "Running Sync ...")

            for key_path in self.source_tree.keys():  # source can not, not exist

                if self.source_tree[key_path] is None:
                    # path is structural or empty (no audio) folder
                    continue

                res_a = {}
                if self.run_files:
                    res_a = self.group_metadata_run_file(key_path)

                res_b = {}
                if self.run_meta:
                    res_b = self.group_metadata_run_meta(key_path)

                if self.source_type == MmusicC.ElementType.folder:
                    file_names = [
                        f.stem for f in self.source_tree[key_path].file_path_list
                    ]
                else:
                    # FIXME this can be done nicer!
                    file_names = [set(res_a.keys()).union(set(res_b.keys())).pop()]
                result = {
                    key: res_a.get(key, 0) + res_b.get(key, 0) for key in file_names
                }

                neg = [i for i in result.values() if i > 3]
                pos = [j for j in result.values() if j >= 0]
                sum_unchanged = sum([z == 0 for z in pos])
                self.unchanged += sum_unchanged
                sum_metadata = sum([z == 1 for z in pos])
                self.metadata += sum_metadata
                sum_created = sum([z == 2 for z in pos])
                self.created += sum_created
                sum_both = sum([z == 3 for z in pos])
                self.both += sum_both
                self.error += len(neg)

                if not self.result.all and sum(result.values()) > 0:
                    str_list = list()
                    str_list.append(
                        f"{len(result)-sum_unchanged:02d}/{len(result):02d} > {key_path}"
                    )
                    for r, v in result.items():
                        str_list.append(f"    {v} >> {r}")
                    logging.log(25, "\n".join(str_list))

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
            f"Deleted    : {self.deleted if self.result.delete_files else 'Not Applicable'}",
            f"Errors     : {self.error}",
        ]

        if self.target is MmusicC.ElementType.database:
            logging.log(25, report[1])
        else:
            for r in report:
                logging.log(25, r)

    def group_metadata_run_file(self, key_path):

        if key_path not in self.target_tree or (
            isinstance(self.source_tree[key_path], GroupMetadata)
            and len(
                {
                    x.file_path for x in self.source_tree[key_path].list_metadata
                }.difference(
                    {x.file_path for x in self.target_tree[key_path].list_metadata}
                )
            )
            > 0
        ):
            # album does not exist or is not complete
            self.target_tree[key_path] = GroupMetadata(
                [
                    Metadata(
                        self.target_common_path.joinpath(
                            metadata.file_path.relative_to(self.source_common_path)
                        ).with_suffix(self.format_extension),
                        link_mode="try",
                    )
                    for metadata in self.source_tree[key_path].list_metadata
                ]
            )
        logging.error("fuu")
        prepared = dict()
        if isinstance(self.target_tree[key_path], GroupMetadata):
            # first create a list of source
            for metadata in self.source_tree[key_path].list_metadata:
                prepared[metadata.file_path.stem] = [
                    metadata,
                    None,
                ]
            # then match the target by stem
            for metadata in self.target_tree[key_path].list_metadata:
                if metadata.file_path.stem not in prepared:
                    raise Exception("Consistency Error, list metadata should be equal")
                prepared[metadata.file_path.stem][1] = metadata
            folder_path = self.target_tree[key_path].common_path

        else:  # Metadata
            prepared = {
                self.source_tree[key_path].file_path.stem: [
                    self.source_tree[key_path],
                    self.target_tree[key_path],
                ]
            }
            folder_path = self.target_tree[key_path].file_path.parent

        if not folder_path.exists():
            folder_path.mkdir(parents=True)

        result = dict()
        for file_name, (meta_s, meta_t) in prepared.items():
            if not meta_t.audio_file_linked:
                if meta_t.file_path.is_file():
                    logging.debug(
                        f"ffmpeg skipped target file exists (but is not linked): '{meta_t.file_path}'"
                    )
                    res = 0
                elif self.result.dry_run:
                    res = 2
                else:
                    res = self.convert_file(meta_s.file_path, meta_t.file_path)

                if res >= 0:
                    try:
                        meta_t.link_audio_file()
                    except FileNotFoundError:
                        logging.warning(
                            f"File {meta_t.file_path} could not be linked, it might be missing."
                        )
                        res = 1 << 4  # 16

            else:
                res = 0

            result[file_name] = res

        return result

    def convert_file(self, source, target):
        with FFmpeg(
            source,
            target,
            options=self.result.ffmpeg_options,
        ) as ffmpeg:
            try:
                ffmpeg.run()
                return 2
            except FFRuntimeError as ex:
                logging.debug(ex)
                logging.log(
                    25,
                    f"ffmpeg error for: {source.relative_to(self.source_common_path)}",
                )
                return 1 << 5  # 32

    def group_metadata_run_meta(self, key_path):
        if key_path not in self.target_tree:
            logging.debug("skipping")
            return {}

        self.target_tree[key_path].import_tags(
            self.source_tree[key_path],
            whitelist=self.whitelist,
            blacklist=self.blacklist,
            skip_none=self.result.lazy_import,
            clear_blacklisted=self.result.delete_existing_metadata,
        )
        res = self.target_tree[key_path].write_tags(
            remove_existing=self.result.delete_existing_metadata
        )
        if self.source_type == MmusicC.ElementType.file:
            # FIXME have another look at this! Is this even used?
            # in case of file --> file actions the names can differ. This ensures the dict keys exists.
            res = {self.source.relative_to(self.source_common_path): res}
        return {k.stem: v for k, v in res.items()}

    def on_error_rmtree(self, function, path, excinfo):
        logging.warning(
            f"Could bnot remove file '{path}'. "
            f"The follorwing error was raised: {excinfo}"
        )
        self.error_occurred_flag = True

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
            # TODO make sure!
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
