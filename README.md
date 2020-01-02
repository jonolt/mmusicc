## Metadata Music Control

mmusic is a lightweight audio file and metadata control and synchronization program to transfer the changes in a master music library to a derived music library.  New files or albums are converted and created with ffmpeg, changed metadata only is copied to. To accommodate the different tag types only a limited set of the most common metadata is supported. These are stored in the ID3 schema which can also be exported to a SQLite database.

More functions:  
- automatic completion easy to determine missing meter data
- show consistency errors between metadata and folder content

The program should work from the command line only and if needed provide a TUI to confirm or suppress changes before writing. It should also be possible to operate the program only via the TUI.

mmusicc shall not replace a metadata editor but provide methods for automated editing of large music libraries.

### Possible Combination

- db -> file
- db -> album
- db -> folder
- file -> file
- file -> db
- album -> album
- album -> db
- folder -> folder
- folder -> db
