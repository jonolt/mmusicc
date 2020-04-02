internals
=========

Programming conventions, internal working mechanisms and metadata behaviour.

Conventions
-----------

- Program internal, all tags and assertion values are saved lowercase (casefold), except ID3 tags which are uppercase.


Variable Naming
^^^^^^^^^^^^^^^

+----------+------------+----------------------------------------------------+
|code_long | code_short | description                                        |
+==========+============+====================================================+
|tag       | t          | single tag key-value-pair e.g. 'artist': Elvis     |
+----------+------------+----------------------------------------------------+
|tag_key   | key, k     | single key of tag e.g. 'artist'                    |
+----------+------------+----------------------------------------------------+
|tag_val   | val, v     | single value of tag e.g. 'Elvis'                   |
+----------+------------+----------------------------------------------------+
|frame_id  |            | single tag id3-key e.g. 'TPE1'                     |
+----------+------------+----------------------------------------------------+
|tags      |            | any arbitrary list or dictionary of tag            |
+----------+------------+----------------------------------------------------+
|audio     | a          | AudioFile containing the metadata of a file as dict|
+----------+------------+----------------------------------------------------+
|datab     | d          | Database                                           |
+----------+------------+----------------------------------------------------+
|meta      | m          | Metadata containing audio and datab                |
+----------+------------+----------------------------------------------------+

Behaviour Metadata
------------------

1) multivalues are internally saved as list
2) multiple values in one string, which are divided by a char, will be extracted to multivalues and saved as in 1, when char is given. TODO global split char


xiph
^^^^^

1) multivalues of a key are writen as multiple tags, 


mp3
^^^

1) no format checking of values (e.g. TimeStampTextFrame)
2) paired text frames are extracted to a flat list
3) the flat list of paired text frames is writen as [u'', list[i]]


formats
-------

options file_save

+-------+-------+-------+-------+-------+-------+-------+
| source                | file original                 |
+-------+-------+-------+-------+-------+-------+-------+
| tag_a | tag_b | tag_c | tag_a | tag_b | tag_c | tag_x |
+=======+=======+=======+=======+=======+=======+=======+
| t1    | None  | t3    | fuu   | bar   | None  | xxx   |
+-------+-------+-------+-------+-------+-------+-------+

+----------------+-------------+-------+-------+-------+-------+
|                |             | file after                    |
+----------------+-------------+-------+-------+-------+-------+
|remove_existing | write_empty | tag_a | tag_b | tag_c | tag_x |
+================+=============+=======+=======+=======+=======+
|False           | False       | t1    |       | t3    | xxx   |
+----------------+-------------+-------+-------+-------+-------+
|False           | True        | t1    | None  | t3    | xxx   |
+----------------+-------------+-------+-------+-------+-------+
|True            | False       | t1    |       | t3    |       |
+----------------+-------------+-------+-------+-------+-------+
|True            | True        | t1    | None  | t3    |       |
+----------------+-------------+-------+-------+-------+-------+