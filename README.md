## Metadata Music Control

mmusicc is a lightweight audio file and metadata control and synchronization program to transfer the changes made in a master music library to a derived music library. ~~New files or albums are converted using ffmpeg.~~ When the file already exits, the metadata is compared und updated if it has changed. The individual tags and their processing can be freely selected by each user via a configuration file. A simple Autofill future can be used to fix small consistency errors, which rules are also editable in the config file. To Synchronize multiple folders at once, the folder structure, directory- and file-names must be identical at source and target, this should be given when this tool is used to one-way sync the master directory. Data can also be exported to or imported from a database e.g. for a metadata backup.

mmusicc shall not replace a metadata editor and only provides methods for automated syncing of large music libraries.

mmusicc's source code is inspired by the two music tag programs [quodlibet](https://github.com/quodlibet/quodlibet) and [puddletag](https://github.com/keithgg/puddletag) and uses some code fragments of those.

mmusicc is still under development and is not yet suitable for productive use, yet.

---
## Programming Info
Some notes for programming.
### Conventions

- Program internal, all tags and assertion values are saved lowercase (casefold), except ID3 tags which are uppercase.

#### Variable Naming

code_long | code_short | description
---       | ---        | ---
tag       | t          | single tag key-value-pair e.g. 'artist': Elvis
tag_key   | key, k     | single key of tag e.g. 'artist'
tag_val   | val, v     | single value of tag e.g. 'Elvis'
frame_id  |            | single tag id3-key e.g. 'TPE1'
tags      |            | any arbitrary list or dictionary of tag
audio     | a          | AudioFile containing the metadata of a file as dict
datab     | d          | Database
meta      | m          | Metadata containing audio and datab

### Behaviour Metadata

1) multivalues are internally saved as list
2) multiple values in one string, which are divided by a char, will be extracted to multivalues and saved as in 1, when char is given. TODO global split char

#### xiph

1) multivalues of a key are writen as multiple texts, 

#### mp3

1) no format checking of values (e.g. TimeStampTextFrame)
2) paired text frames are extracted to a flat list
3) the flat list of paired text frames is writen as [u'', list[i]]