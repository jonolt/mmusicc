## Metadata Music Control

mmusicc is a lightweight audio file and metadata control and synchronization program to transfer the changes in a master music library to a derived music library.  New files or albums are converted and created with ffmpeg, changed metadata only is copied to. The individual tags and their processing can be freely selected by each user via a configuration file. There should also be preconfigured configurations. ID3 tags are possibly processed before. There will be a simple Autofill feature which will be only applied to source files, and fill empty fields from pattern.

The folder structure and directory/file names must be identical, this should be given when this toll is used to one-way sync the parent directory.

mmusicc shall not replace a metadata editor but provide methods for automated syncing of large music libraries.

### Conventions

- Program internal, all tags and assertion values are saved lowercase (casefold), except ID3 tags which are uppercase.

