## Metadata Music Control

mmusicc is a lightweight audio file and metadata control and synchronization program to transfer the changes made in a master music library to a derived music library. New files or albums are converted using ffmpeg. When the file already exits, the metadata is compared und updated if it has changed. The individual tags and their processing can be freely selected by each user via a configuration file. A simple Autofill future can be used to fix small consistency errors, which rules are also editable in the config file. To Synchronize multiple folders at once, the folder structure, directory- and file-names must be identical at source and target, this should be given when this tool is used to one-way sync the master directory. Data can also be exported to or imported from a database e.g. for a metadata backup.

mmusicc shall not replace a metadata editor and only provides methods for automated syncing of large music libraries.

mmusicc's source code is inspired by the two music tag programs [quodlibet](https://github.com/quodlibet/quodlibet) and [puddletag](https://github.com/keithgg/puddletag) and uses some code fragments of those.

mmusicc is still under development and is not yet suitable for productive use, yet.

### Version Milestones

version | milestone
--- | ---
0.1.0 | Metadata working 
0.2.0 | MmusicC working (and first package distribution (test.pypi only))
0.3.0 | comprehensive testing and verification (release on pypi)
0.5.0 | interactive mode with text user interface (tui) to display changes
0.7.0 | mmusic can be run in graphical mode from tui (state machine)