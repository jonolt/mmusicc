usage
=====

Don't use it on your music library before version 0.3!

.. highlight:: none

.. code-block::

    usage: MmusicC (-s SOURCE | -sdb SOURCE_DB) (-t TARGET | -tdb TARGET_DB) [-h]
                   [--version] [--album] [--only-meta | --only-files] [--dry-run]
                   [-v] [-f FORMAT] [--ffmpeg-options FFMPEG_OPTIONS]
                   [--white-list-tags WHITE_LIST_TAGS [WHITE_LIST_TAGS ...]]
                   [--black-list-tags BLACK_LIST_TAGS [BLACK_LIST_TAGS ...]]
                   [--delete-existing-metadata] [--path-config PATH_CONFIG]

    metadata and file syncing the following combination are possible:
      - file   --> file
      - file   --> parent folder (target name is generated from source)
      - folder --> folder (use --album to not to move through tree)
      - folder --> db (full path as primary key)
      - db     --> folder (key matching starts at leave of path)

    Supported Formats for Metadata:
    ['.ogg', '.oga', '.flac', '.mp3', '.mp2', '.mp1', '.mpg', '.mpeg']

    Required Options:
      -s SOURCE, --source SOURCE
                            source file/album/lib-root
      -sdb SOURCE_DB, --source-db SOURCE_DB
                            source database
      -t TARGET, --target TARGET
                            target file/album/lib-root
      -tdb TARGET_DB, --target-db TARGET_DB
                            target database

    General Options:
      -h, --help            Show this help message and exit.
      --version             show program's version number and exit
      --album               only sync folder level
      --only-meta           only sync meta, don't sync files. Auto set when
                            syncing from/to database
      --only-files          only sync files, don't update metadata
      --dry-run             do everything as usual, but without writing (file and
                            database). It is recommended to use with --only-meta
                            or --only-files, otherwise errors are likely.
      -v, --verbose         print log messages. can be stacked up to 2 (info,
                            debug)

    File Conversion:
      -f FORMAT, --format FORMAT
                            output container format of ffmpeg conversion
      --ffmpeg-options FFMPEG_OPTIONS
                            conversion options for ffmpeg conversion. If empty
                            ffmpeg defaults are used.

    Metadata Syncing:
      --white-list-tags WHITE_LIST_TAGS [WHITE_LIST_TAGS ...]
                            Tags to be whitelisted. Can be passed as file (Plain
                            text file, #containing tags separated with a new line)
                            or as one or multiple arguments
      --black-list-tags BLACK_LIST_TAGS [BLACK_LIST_TAGS ...]
                            Tags to be blacklisted. Can be passed as file (Plain
                            text file, #containing tags separated with a new line)
                            or as one or multiple arguments
      --delete-existing-metadata
                            delete existing metadata on target files before
                            writing.
      --path-config PATH_CONFIG
                            file path to custom config file