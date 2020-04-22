import logging
import pathlib

from sqlalchemy import MetaData, Table, Column, String, PickleType
from sqlalchemy import create_engine

from mmusicc.util.allocationmap import list_tags


class MetaDB:
    """Object representing a database connection in Metadata,

    holds connection parameters and inserts and reads data. When writing to the
    Database, always all data is written, while you can load only select which
    tags to load. See https://docs.sqlalchemy.org/en/13/core/engines.html for
    Database Url examples.

    There will be two tables. One only containing strings and string
    representation of objects and one containing the pickled strings or
    objects. This way all object types can be restored at loading while at the
    same time the database can be search with standard database queries.

    Args:
        database_url (str): database url following RFC-1738*. If the sting,
            does not contain '://', a filepath for a sqlite database is
            assumed.
    """

    def __init__(self, database_url):
        if "://" not in database_url:
            # it is assumed the database url is filepath and therefore SQLite
            database_url = pathlib.Path(database_url).expanduser().resolve()
            database_url = "sqlite:///" + str(database_url)
        self._database_url = database_url
        self._engine = create_engine(self._database_url)
        if not list_tags:
            logging.warning("no tags found! Is project initialized")
        self._create_table(list_tags)

    @property
    def database_url(self):
        """Get URL of connected database."""
        return self._engine.url

    def _create_table(self, list_keys):
        """Create a Tables in Database if it does not already exists,

        where each column represents a tag (=key in list_keys).

        Args:
            list keys (list of str): list of tags in Metadata
        """
        self.list_keys = list_keys
        sql_metadata = MetaData()
        self.tags = Table(
            "tags", sql_metadata, Column("_primary_key", String(200), primary_key=True)
        )
        self.pickle_tags = Table(
            "pickle_tags",
            sql_metadata,
            Column("_primary_key", String(200), primary_key=True),
        )
        for key in list_keys:
            self.tags.append_column(Column(key, String(100)))
            self.pickle_tags.append_column(Column(key, PickleType()))

        self.tags.create(self._engine, checkfirst=True)
        self.pickle_tags.create(self._engine, checkfirst=True)

    def insert_meta(self, dict_data, primary_key):
        """Inserts a row into the database, with the values from the dict.

        Args:
            dict_data  (dict): metadata dictionary (`Dict[str, object]`) to be
                written.
            primary_key (str): unique identifier of the item which data is to
                be written. Metadata uses the absolute filepath.
        """
        dict_meta_pickle = dict_data.copy()
        dict_meta_pickle["_primary_key"] = primary_key
        dict_meta = dict()
        dict_meta["_primary_key"] = primary_key
        for key in list(dict_meta_pickle):
            dict_meta[key] = str(dict_meta_pickle[key])

        with self._engine.connect() as conn:
            conn.execute(self.tags.insert().values(dict_meta))
            conn.execute(self.pickle_tags.insert().values(dict_meta_pickle))

    def read_meta(self, primary_key, tags=None):
        """returns values of a row with given primary key as metadata dict.

        Args:
            primary_key         (str): unique identifier of the item which data
                is to read (eg. Filepath).
            tags        (list of str): list of strings to be read, reads all if
                None. Defaults to None.

        Returns:
            dict_data (dict<str:obj>): metadata dictionary
        """
        with self._engine.connect() as conn:
            foo_col = Column("_primary_key")
            result = conn.execute(
                self.pickle_tags.select().where(foo_col == primary_key)
            ).first()
            if result:
                dict_data_tmp = dict(result)
                dict_data_tmp.pop("_primary_key")
                if tags:
                    for key in list(dict_data_tmp):
                        if key not in tags:
                            dict_data_tmp.pop(key)
                return dict_data_tmp
            return None

    def get_list_of_primary_keys(self):
        """reads the primary keys from database and returns them.

        Returns:
            list of str: list of primary key strings in database
        """
        with self._engine.connect() as conn:
            result = list(conn.execute("SELECT _primary_key FROM tags"))
            return [s[0] for s in result]
