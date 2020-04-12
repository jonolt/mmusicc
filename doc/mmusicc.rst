package
=======

Subpackages
-----------

.. toctree::

   mmusicc.database
   mmusicc.formats
   mmusicc.util

mmusicc.metadata module
-----------------------
Base Module for all metadata interactions with files and the database.

.. hint:: how to doc metaclass properties and functions in class?

.. automodule:: mmusicc.metadata
    :show-inheritance:

    .. autoclass:: MetadataMeta
        :members:
        :show-inheritance:

    .. autoclass:: Metadata
        :members:
        :show-inheritance:

    .. autoclass:: GroupMetadata
        :members:
        :show-inheritance:

    .. autoclass:: AlbumMetadata
        :show-inheritance:


mmusicc.mmusicc module
----------------------
Module handling user interaction, providing the command line interface, using the functions provided by ffmpeg and metadata. See :ref:`usage` for more information.
