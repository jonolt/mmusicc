import logging

from sqlalchemy import MetaData, Table, Column, String, PickleType
from sqlalchemy import create_engine

from mmusicc.util.allocationmap import list_tags


class MetaDB:
    """Object representing a database connection in Metadata,

    holds connection parameters and inserts and reads data.
    When writing to the Database, always all data is written, while you can
    load only select which tags to load.

    *https://docs.sqlalchemy.org/en/13/core/engines.html

    Args:
        database_url (str): database url following RFC-1738*. If the sting,
        does not contain '://', a filepath and a sqlite database are assumed.
    """

    def __init__(self, database_url):
        if "://" not in database_url:
            database_url = 'sqlite:///' + database_url
        self._database_url = database_url
        self._engine = create_engine(self._database_url)
        if not list_tags:
            logging.warning("no tags found! Is project initialized")
        self._create_table(list_tags)

    def _create_table(self, list_keys):
        """Create a Tables in Database if it does not already exists,

        where the each column represents a tag (=key in list_keys).

        Args:
            list keys (list<str>): list of tags in Metadata
        """
        self.list_keys = list_keys
        sql_metadata = MetaData()
        self.tags = Table('tags', sql_metadata,
                          Column('_primary_key', String(200),
                                 primary_key=True))
        self.pickle_tags = Table('pickle_tags',
                                 sql_metadata,
                                 Column('_primary_key', String(200),
                                        primary_key=True))
        for key in list_keys:
            self.tags.append_column(Column(key, String(100)))
            self.pickle_tags.append_column(Column(key, PickleType()))

        self.tags.create(self._engine, checkfirst=True)
        self.pickle_tags.create(self._engine, checkfirst=True)

    def insert_meta(self, dict_data, primary_key):
        """Inserts a row into the database, with the values from the dict.

        Args:
            dict_data (dict<str:obj>): metadata dictionary to be writen
            primary_key         (str): unique identifier of the item which data
                is to be written (eg. Filepath).
        """
        dict_meta = dict_data.copy()
        dict_meta["_primary_key"] = primary_key
        dict_meta_pickle = dict()
        dict_meta_pickle["_primary_key"] = primary_key
        for key in list(dict_meta):
            if isinstance(dict_meta[key], str):
                pass
            else:
                dict_meta[key] = str(dict_meta[key])
                dict_meta_pickle[key] = dict_meta[key]

        with self._engine.connect() as conn:
            conn.execute(self.tags.insert().values(dict_meta))
            conn.execute(self.pickle_tags.insert().values(dict_meta))

    def read_meta(self, primary_key, tags=None):
        """returns values of a row with given primary key as metadata dict.

        Args:
            primary_key         (str): unique identifier of the item which data
                is to read (eg. Filepath).
            tags          (list<str>): list of strings to be read, reads all if
                None. Defaults to None.

        Returns:
            dict_data (dict<str:obj>): metadata dictionary
        """
        with self._engine.connect() as conn:
            foo_col = Column("_primary_key")
            result = conn.execute(self.tags.
                                  select().
                                  where(foo_col == primary_key)).first()
            if result:
                dict_data_tmp = dict(result)
                dict_data_tmp.pop("_primary_key")
                for key in list(dict_data_tmp):
                    if key not in tags:
                        dict_data_tmp.pop(key)
                return dict_data_tmp
            return None