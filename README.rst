Metadata Music Control
======================

|PyPI status|
|PyPI license|
|PyPI version mmusicc|
|PyPI pyversions|
|Documentation Status|
|code style: black|

.. |PyPI license| image:: https://img.shields.io/pypi/l/mmusicc.svg
   :target: https://pypi.python.org/pypi/mmusicc/

.. |PyPI version mmusicc| image:: https://img.shields.io/pypi/v/mmusicc.svg
   :target: https://pypi.python.org/pypi/mmusicc/

.. |code style: black| image:: https://img.shields.io/badge/code%20style-black-000000.svg
    :target: https://github.com/psf/black

.. |PyPI pyversions| image:: https://img.shields.io/pypi/pyversions/mmusicc.svg
   :target: https://pypi.python.org/pypi/mmusicc/

.. |PyPI status| image:: https://img.shields.io/pypi/status/mmusicc.svg
   :target: https://pypi.python.org/pypi/mmusicc/

.. |Documentation Status| image:: https://readthedocs.org/projects/mmusicc/badge/?version=latest
   :target: http://mmusicc.readthedocs.io/?badge=latest


mmusicc is a lightweight audio file and metadata control and synchronization program to transfer the changes made in a master music library to a derived music library. New files or albums are converted using ffmpeg. When the file already exits, the metadata is compared und updated if it has changed. The individual tags and their processing can be freely selected by the user via a configuration file. To Synchronize multiple folders at once, the folder structure, directory- and file-names must be identical at source and target, this should be given when this tool is used to one-way sync the master directory.

mmusicc shall not replace a metadata editor and only provides methods for automated syncing of large music libraries.

mmusicc's source code is inspired by the two music tag programs `quodlibet <https://github.com/quodlibet/quodlibet>`_ and `puddletag <https://github.com/keithgg/puddletag/>`_ and uses some code fragments of those.


Installation & Usage
--------------------

mmusicc is still under development and should not be used to overwrite master data. Using it for 'slave' data is perfectly fine. Multiple test confirm that the master files are not modified and only accessed. It is also tested that the program is deterministic.

.. code-block:: bash

    pip install mmusicc

The script is automatically installed on system. Use ``--help`` for usage info or see its output at `usage on mmusicc.readthedocs.org <https://mmusicc.readthedocs.io/en/latest/usage.html>`_. See also the following examples:


.. code-block:: bash

    # syncing a full library to mp3
    mmusicc -s Music -t MusicMp3 -f .mp3 --ffmpeg-options "-codec:a libmp3lame -qscale:a 2 -codec:v copy"

    # syncing a full library to ogg
    mmusicc --source Music --target MusicOgg --format .ogg --ffmpeg-options "-c:a libvorbis -q 6 -vn"

    # converting one file to another format. The two commands are equivalent
    mmusicc -s folder_source/song.flac -t . -f ogg
    mmusicc -s folder_source/song.flac -t song.ogg

    # syncing A to B, where all existing metadat is deleted,
    # leaving only the white listed tags on file
    mmusicc -s A -t B -f .ogg -white-list-tags track title artist delete-existing-metadata

Supported Formats/Codecs
^^^^^^^^^^^^^^^^^^^^^^^^

Supported Codecs anf Formats are displayed with ``--help`` (see `usage <https://mmusicc.readthedocs.io/en/latest/usage.html>`_).

**Additional formats/codecs will be implemented on request**.

For now the only formats/codecs supported are, what I need for myself.


Remarks
-------

Catching every special case of certain metadata formats and transferring it to a normalized dict is nearly impossible (especially with id3). Also different tagging program's have certain specialities how certain uncommon tags are saved or if say are even displayed. Therefore some features are not yet or only partially supported:

- Only one Album Cover file is supported at the moment. More will raise Errors (will be fixed soon).
- There is limited support for mp3 tags. Support for id3.PairedTextFrames was dropped, since it is not used much and I haven't found a good way to handle them. They might come back in the future. They are used for 'TIPL: Involved People List', 'TMCL: Musicians Credits List'. Some taggers use these field for e.g arranger.
