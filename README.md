## Metadata Music Control

mmusicc is a lightweight audio file and metadata control and synchronization program to transfer the changes in a master music library to a derived music library.  New files or albums are converted and created with ffmpeg, changed metadata only is copied to. The individual tags and their processing can be freely selected by each user via a configuration file. There should also be preconfigured configurations. ID3 tags are possibly processed before. There will be a simple Autofill feature which will be only applied to source files, and fill empty fields from pattern.

The folder structure and directory/file names must be identical, this should be given when this toll is used to one-way sync the parent directory.

mmusicc shall not replace a metadata editor but provide methods for automated syncing of large music libraries.

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

2) multivalues are internally saved as list
2) multiple values in one string, which are divided by a char, will be extracted to multivalues and saved as in 1, when char is given. TODO global split char

#### xiph

1) multivalues of a key are writen as multiple texts, 

#### mp3

2) no format checking of values (e.g. TimeStampTextFrame)
1) paired text frames are extracted to a flat list
2) the flat list of paired text frames is writen as [u'', list[i]]