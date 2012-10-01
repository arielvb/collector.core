# -*- coding: utf-8 -*-
"""PersistenceAlchemy allows Collector to store the data using SQLAlchemy"""
from persistence import Persistence
from file import File
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, Sequence
from sqlalchemy.orm import sessionmaker

import os


class Alchemy(object):

    _instance = None

    def __init__(self):
        super(Alchemy, self).__init__()
        if Alchemy._instance is not None:
            raise Exception("Called more that once")
        Alchemy._instance = self
        self.engine = {}
        self.session = {}

    @staticmethod
    def destroy():
        """Destroy the instance"""
        Alchemy._instance = None

    @staticmethod
    def get_instance():
        if Alchemy._instance is None:
            Alchemy._instance = Alchemy()
        return Alchemy._instance

    def get_engine(self, key):
        if not key in self.engine:
            self.engine[key] = create_engine('sqlite:///' + key, echo=True)
        return self.engine[key]

    def get_session(self, key):
        if not key in self.engine:
            raise Exception("key not found")
        if not key in self.session:
            self.session[key] = sessionmaker(bind=self.engine[key])()
        return self.session[key]


class PersistenceAlchemy(Persistence):

    """docstring for PersistenceAlchemy"""
    def __init__(self, schema, path, params=None):
        super(PersistenceAlchemy, self).__init__(
            schema,
            path,
            params)
        if path != ':memory:':
            file_path = os.path.join(self.path, self.collection_id + '.sqlite')
        else:
            file_path = path
        # echo is useful for debug
        self.man = Alchemy.get_instance()
        self.engine = self.man.get_engine(file_path)
        Base = declarative_base()

        attributes = PersistenceAlchemy.get_columns(schema)
        self._class = type(str(schema.collection + "_" + schema.id),
                         (File, Base), attributes)
        # TODO (important) for each field that is multivalue whe must create a new class,
        # and the attribute must be a foreing key!
        Base.metadata.create_all(self.engine)
        self._session = self.man.get_session(file_path)

    def next_id(self):
        """Returns the new id to insert in the table"""
        max_id = self.engine.execute("SELECT MAX(id) FROM %s;" %
                                self.subcollection).scalar()
        if max_id is None:
            max_id = 1
        return max_id + 1

    @staticmethod
    def get_columns(schema):
        columns = {}
        # Extra fields
        columns['__tablename__'] = schema.id
        # custom __init__

        # def m_init(self, values):
            # super(FileAlchemy, self).__init__(values)

        # columns['__init__'] = m_init

        # Note: sqlite doesn't use Sequence
        columns['id'] = Column('id', Integer, Sequence('id_seq'),
                          primary_key=True)
        for field in schema.file.values():
            columns[field.get_id()] = (
                PersistenceAlchemy.field2column(field))
        return columns

    @staticmethod
    def field2column(field):
        """Returns the equivalent SQLAlchemy column given a Field"""
        id_ = field.get_id()
        if field._class == 'text' or field._class == 'image' or field._class == 'ref':
            return Column(id_, String)
        if field._class == 'int':
            return Column(id_, Integer)

    def get(self, _id):
        # TODO nothing better that filter_by? doesn't exisits get(id)?
        return self._session.query(self._class).filter_by(id=_id).first()

    def get_last(self, count):
        # TODO
        return self._session.query(self._class).all()

    def get_all(self, start_at, limit):
        # TODO
        return self._session.query(self._class).all()

    def search(self, term):
        raise NotImplemented()

    def save(self, values):
        # TODO fixme, value must not be a dictionary must be a File
        obj = self._class(values)
        if 'id' not in values:
            self._session.add(obj)
            self._session.commit()
            values['id'] = obj.id
        else:
            obj = self._session.query(self._class).filter_by(
                id=values['id']).first()
            #TODO
            obj.update(values)
            self._session.commit()
        return obj
