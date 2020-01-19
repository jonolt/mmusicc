import logging

from sqlalchemy import MetaData, Table, Column, String, PickleType
from sqlalchemy import create_engine

from mmusicc.util.allocationmap import list_tags


class MetaDB:

    def __init__(self, path):
        self._file_path = path
        self._engine = create_engine('sqlite:///' + self._file_path)
        if not list_tags:
            logging.warning("no tags found! Is project initialized")
        self._create_table(list_tags)

    def _create_table(self, list_keys):
        self.list_keys = list_keys
        sql_metadata = MetaData()
        self.tags = Table('tags', sql_metadata,
                          Column('file_path', String(200), primary_key=True))
        self.pickle_tags = Table('pickle_tags',
                                 sql_metadata,
                                 Column('file_path', String(200),
                                        primary_key=True))
        for key in list_keys:
            self.tags.append_column(Column(key, String(100)))
            self.pickle_tags.append_column(Column(key, PickleType()))

        self.tags.create(self._engine, checkfirst=True)
        self.pickle_tags.create(self._engine, checkfirst=True)

    def insert_meta(self, dict_data, primary_key):
        dict_meta = dict_data.copy()
        dict_meta["file_path"] = primary_key
        dict_meta_pickle = dict()
        dict_meta_pickle["file_path"] = primary_key
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
        with self._engine.connect() as conn:
            foo_col = Column('file_path')
            result = conn.execute(self.tags.
                                  select().
                                  where(foo_col == primary_key)).first()
            if result:
                dict_data_tmp = dict(result)
                dict_data_tmp.pop("file_path")
                for key in list(dict_data_tmp):
                    if key not in tags:
                        dict_data_tmp.pop(key)
                return dict_data_tmp
            return None

    @staticmethod
    def row2dict(row):
        # row2dict = lambda r: {c.name: str(getattr(r, c.name))
        # for c in r.__table__.columns}
        d = {}
        for column in row.__table__.columns:
            d[column.name] = str(getattr(row, column.name))
        return d
