Testing (pytest)
----------------

Test is not optimized for speed. Each functions that writes to files, copies all or some data from the 3 source folders A_flac, B_mp3, C_mp3 to its onw test (pytest.fixture).

In test_formats.py was tested that all supported formats are loaded correctly into the AudioFile dict. It is therefore enough to test metadata only with one format which will be flac. Mmusicc test are using mp3 as target since it is a very common format.

All Tests use the default association map delivered with the program. Only test_formats uses a special mapping, which tries to test every possible tag, especially for ID3.

General
^^^^^^^

- database.db is the exported file of ``test_export_db_tag[AlbumMetadata]`` whith the title column in ``tags`` and ``pickle_tags`` set to NULL (e.g. `sqlitebrowser <http://sqlitebrowser.org>`_)


music_lib
^^^^^^^^^

- A_flac and B__flac have identical structure and metadata
- B_flac media stream is created with ffmpeg and without any arguments and custom metadata
- C_flac uses files from B_flac with additional changes in metadata, artist_puddletag is missing
- Test file metadata is manipulated with kid3 for the default files and ex falso for files with empty tags

C_ogg metadata changes
""""""""""""""""""""""

1)  - missing date
    - wrong album title ("wrong metadata, also date is missing")
    - composer tag ("should not be here")
    - license tag ("cc")
2)  - CD_01 got the default format
    - CD_02 has the same tag keys that CD_01 that plus tag keys with empty values




test data structure
"""""""""""""""""""

.. code-block:: none

    data/music_lib
    ├── A_flac
    │   ├── artist_puddletag
    │   │   ├── album_good_(2018)
    │   │   │   ├── 01_track1.flac
    │   │   │   └── 02_track2.flac
    │   │   └── audio_at_artist_level.flac
    │   ├── artist_quodlibet
    │   │   ├── album_bar_-_single_(2020)
    │   │   │   └── 01_track1.flac
    │   │   └── album_fuu_(2019)
    │   │       ├── 01_track1.flac
    │   │       └── 02_track2.flac
    │   └── various_artists
    │       └── album_best_hits_compilation_(2010)
    │           ├── CD_01
    │           │   ├── 01_track1.flac
    │           │   └── 02_track2.flac
    │           └── CD_02
    │               ├── 01_track1.flac
    │               └── 02_track2.flac
    ├── B_ogg
    │   ├── artist_puddletag
    │   │   ├── album_good_(2018)
    │   │   │   ├── 01_track1.ogg
    │   │   │   └── 02_track2.ogg
    │   │   └── audio_at_artist_level.ogg
    │   ├── artist_quodlibet
    │   │   ├── album_bar_-_single_(2020)
    │   │   │   └── 01_track1.ogg
    │   │   └── album_fuu_(2019)
    │   │       ├── 01_track1.ogg
    │   │       └── 02_track2.ogg
    │   └── various_artists
    │       └── album_best_hits_compilation_(2010)
    │           ├── CD_01
    │           │   ├── 01_track1.ogg
    │           │   └── 02_track2.ogg
    │           └── CD_02
    │               ├── 01_track1.ogg
    │               └── 02_track2.ogg
    ├── C_ogg
    │   ├── artist_quodlibet
    │   │   ├── album_bar_-_single_(2020)
    │   │   │   └── 01_track1.ogg                       --> 1)
    │   │   └── album_fuu_(2019)
    │   │       ├── 01_track1.ogg
    │   │       └── 02_track2.ogg
    │   └── various_artists
    │       └── album_best_hits_compilation_(2010)
    │           ├── CD_01                               --> 2)
    │           │   ├── 01_track1.ogg
    │           │   └── 02_track2.ogg
    │           └── CD_02                               --> 2)
    │               ├── 01_track1.ogg
    │               └── 02_track2.ogg
    └── README.rst
