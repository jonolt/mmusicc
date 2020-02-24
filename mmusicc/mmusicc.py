import argparse
import os

from mmusicc._init import init
from mmusicc.util.misc import PathLoader
from mmusicc.version import __version__ as package_version


class MmusicC:

    def __init__(self, args):
        """Create a ViewControl object with the given options.
        Args:
            args (:list: string):
        """
        # print(args)
        parser = argparse.ArgumentParser(
            prog="MmusicC",
            description='metadata manager',
            epilog='when using multiple inputs and outputs, files will be matched by path starting from the filename')
        parser.add_argument('-s', '--source',
                            nargs='+',
                            action='store',
                            dest='source',
                            help="source file or folder or n args")
        parser.add_argument('-t', '--target',
                            nargs='+',
                            action='store',
                            dest='target',
                            help="target file or folder or n args")
        parser.add_argument('-w', '--walk',
                            action='store_true',
                            dest='walk',
                            help="walk through all subfolders and search for audio files"
                            )
        parser.add_argument('-b', '--target-base',
                            action='store',
                            dest='target_base',
                            help="target base folder, file matches will be searched in here")
        parser.add_argument('--database-export',
                            action='store',
                            dest='database_export',
                            default=None,
                            help="database url to exported to, SQLite if file path, set true to use connection file")
        parser.add_argument('--database-import',
                            action='store',
                            dest='database_import',
                            default=None,
                            help="database url to import data from, SQLite if file path, set rue to use connection file")
        parser.add_argument('--white-list-tag',
                            action='store',
                            dest='tag_white_list',
                            help="tag white list can be provided as list or file")
        parser.add_argument('--black-list-tag',
                            action='store',
                            dest='tag_black_list',
                            help="tag black list can be provided as list or file")
        parser.add_argument('--only-meta',
                            action='store_true',
                            dest='only_meta',
                            help="only sync meta, don't (re-)create files")
        parser.add_argument('--only-files',
                            action='store_true',
                            dest='only_files',
                            help="only sync files, don't update metadata")
        parser.add_argument('--delete-existing-metadata',
                            action='store_true',
                            dest='delete_existing_metadata',
                            help="delete existing metadata on target files")
        parser.add_argument('--delete-files',
                            action='store_true',
                            dest='delete_files',
                            help="delete files not in source directory")
        parser.add_argument('--dry-run',
                            action='store_true',
                            dest='dry_run',
                            help="do everything as usual, but writing")
        parser.add_argument('--database-config',
                            action='store',
                            dest='database_config',
                            help="optional file to store database connection use with --database-export/import true")
        parser.add_argument('--path-config',
                            action='store',
                            dest='path_config',
                            help="alternative config file")
        parser.add_argument('--version',
                            action='version',
                            version=package_version)
        self.parser_result = parser.parse_args(args)

        if not self.parser_result.path_config:
            path_this_file = os.path.dirname(os.path.dirname(
                os.path.abspath(__file__)))
            self.parser_result.path_config = os.path.join(path_this_file, "config.yaml")

        init(self.parser_result.path_config)

        if self.parser_result.dry_run:
            raise Exception("Dry Run not implemented yet. Raising Exception for safety reasons")

        if self.parser_result.tag_white_list:
            print("The whitelist is not implemented, yet. Coming Soon!")

        if self.parser_result.tag_black_list:
            print("The blacklist is not implemented, yet. Coming Soon!")

        if self.parser_result.delete_existing_metadata:
            print("The deletion of existing_metadata is not implemented, yet. Coming Soon!")

        if self.parser_result.delete_files:
            print("The deletion of files is not implemented, yet. Coming Soon!")

        if self.parser_result.database_export:
            print("The database export not implemented, yet. Coming Soon!")

        if self.parser_result.database_import:
            print("The database import not implemented, yet. Coming Soon!")

        if not self.parser_result.only_meta:
            print("File syncing is not implemented, yet. Coming Soon!")

        if not self.parser_result.only_files:
            if not self.parser_result.walk:
                if self.parser_result.source \
                        and len(self.parser_result.source) == 1:
                    self.parser_result.source = self.parser_result.source[0]
                if self.parser_result.target \
                        and len(self.parser_result.target) == 1:
                    self.parser_result.target = self.parser_result.target[0]

        if self.parser_result.source:
            self.source = PathLoader(self.parser_result.source)
        if self.parser_result.target:
            self.target = PathLoader(self.parser_result.target)

            print("loaded files, no other actions implemented yet")
