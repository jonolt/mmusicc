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
2) multiple values in one string, which are divided by a char, will be extracted to multivalues and saved as in 1)
3) comment is used as default and not description
4) album artwork is/are a dict item as any other tags on metadata level. Differentiation between Picture Types and how to represent them in the allocation map might needs to be implemented. A possible implementation would be to use the id3 picture types eg.:

.. code-block::

    'ALBUMART:COVER_FRONT':
        - 0
        - APIC
        - - COVER_FRONT
        - - MEDIA

    'ALBUMART:COVER_BACK':
        - 0
        - APIC
        - - COVER_BACK


xiph
^^^^^

1) multivalues of a key are writen as multiple tags


mp3
^^^

1) no format checking of values (e.g. TimeStampTextFrame)
2) all values are written as utf8, encoding options have to be defined


module formats
--------------

effect of options in file_save
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

In dict meta are to kinds of "empty":

- None : tag does not exist (and was not in source file metadata)
- Empty: tag does exist with an empty value (and was saved in source file with empty value). Values are handled as if they had a value.

Save behaviour:

- None is skipped, existing data on file is unchanged
- Empty write_empty==False: if tag exists in target it is deleted
- Empty write_empty==True : tag with value Empty is saved in file (and created)
- Value is always writen to file (and created)

The equivalent of write_empty (also remove empty) behaviour differs between programs:

- write_empty==False: audacious, EasyTAG, Kid3, VLC Media Player, Clementine
- write_empty==True : Ex Falso (QuodLibet), MusicBrainz Picard, Puddletag

To clear values not in the metadata list (=unprocessed tag) or to clear empty values without loading the dict with those, use remove_existing.


.. include:: ../test/data/README.rst
