Metadata Music Control
======================

|GPL-3.0-or-later|

.. |GPL-3.0-or-later| image:: https://img.shields.io/badge/License-GPLv3+-blue.svg
    :target: https://github.com/jonolt/mmusicc/blob/master/LICENSE

mmusicc is a lightweight audio file and metadata control and synchronization program to transfer the changes made in a master music library to a derived music library. New files or albums are converted using ffmpeg. When the file already exits, the metadata is compared und updated if it has changed. The individual tags and their processing can be freely selected by each user via a configuration file. A simple Autofill future can be used to fix small consistency errors, which rules are also editable in the config file. To Synchronize multiple folders at once, the folder structure, directory- and file-names must be identical at source and target, this should be given when this tool is used to one-way sync the master directory. Data can also be exported to or imported from a database e.g. for a metadata backup.

mmusicc shall not replace a metadata editor and only provides methods for automated syncing of large music libraries.

mmusicc's source code is inspired by the two music tag programs `quodlibet <https://github.com/quodlibet/quodlibet>`_ and `puddletag <https://github.com/keithgg/puddletag/>`_ and uses some code fragments of those.


Installation & Usage
--------------------

mmusicc is still under development and should not be used to overwrite master data. Using it for 'slave' data is perfectly fine. Multiple test confirm that the master files are not modified and only accessed. It is also tested that the program is deterministic.

.. code-block::

    pip install mmusicc

The script is automatically installed on system. Use ``--help`` for usage info or see its output at `usage on mmusicc.readthedocs.org <https://mmusicc.readthedocs.io/en/latest/usage.html>`_. See also the following examples:

.. code-block::

    # syncing a full library to mp3
    mmusicc -s Music -t MusicMp3 -f .mp3 --ffmpeg-options "-codec:a libmp3lame -qscale:a 2 -codec:v copy"


Remarks
-------

Catching every special case of certain metadata formats and transferring it to a normalized dict is nearly impossible (especially with id3).

Also different tagging program's have certain specialities how certain uncommon tags are saved or if say are even displayed.

.. note:: Only one Album Cover file is supported at the moment.

.. note:: Support for id3.PairedTextFrames was dropped, since it is not used much and I haven't found a good way to handle them. They might come back in the future. They are used for 'TIPL: Involved People List', 'TMCL: Musicians Credits List'. Some taggers use these field for e.g arranger.


Version Milestones
------------------

+--------+--------------------------------------------------------------------+
|version | milestone                                                          |
+--------+--------------------------------------------------------------------+
|0.1.0   | metadata working                                                   |
+--------+--------------------------------------------------------------------+
|0.2.0   | mmusicc working (and first package distribution (test.pypi only))  |
+--------+--------------------------------------------------------------------+
|0.3.0   | comprehensive testing and verification (release on pypi)           |
+--------+--------------------------------------------------------------------+
|0.5.0   | interactive mode with text user interface (tui) to display changes |
+--------+--------------------------------------------------------------------+
|0.7.0   | mmusicc can be run in graphical mode from tui (state machine)      |
+--------+--------------------------------------------------------------------+
