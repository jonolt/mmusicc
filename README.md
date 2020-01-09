## Metadata Music Control

mmusicc is a lightweight audio file and metadata control and synchronization program to transfer the changes in a master music library to a derived music library.  New files or albums are converted and created with ffmpeg, changed metadata only is copied to. The individual tags and their processing can be freely selected by each user via a configuration file. There should also be preconfigured configurations. ID3 tags are possibly processed before.

The folder structure and directory/file names must be identical, this should be given when this toll is used to one-way sync the parent directory.

Autofill will be only applied to source files.



The program should work from the command line only and if needed provide a TUI to confirm or suppress changes before writing. It should also be possible to operate the program only via the TUI.

mmusicc shall not replace a metadata editor but provide methods for automated editing of large music libraries.

### MILESTONES

1) read write metadata with onw functions (than commit to main)
2) implement puddletag/exfalso functions

### TODOS
- write test for Album/GroupMetadata
- automatic completion easy to determine missing meter data
- show consistency errors between metadata and folder content
- use puddle tag libraries for reading and writing
- implement database support
  - save/read all metadata to database
- automatic library sync
  - sync and convert files
  - sync metadata
- Text User Interface support for all functions
- Function to guess id3 frame tag from vorbis comment (see other taggers)

### Conventions

- Program internal, all tags and assertion values are saved lowercase, except ID3 tags which are uppercase.
- Multiple values for a key are delimited by newlines TODO arranger

### Sources

#### Libraries
- mutagen

#### General Taggers
Used for coding ideas, since they are writen in python and use mutagen:
- puddletag http://puddletag.sourceforge.net
- Ex Falso https://quodlibet.readthedocs.org/
- MusicBrainz Picard https://picard.musicbrainz.org/

Other Taggers used as reference:
- kid3 C++ http://kid3.sourceforge.net
- EasyTAG C https://wiki.gnome.org/Apps/EasyTAG


