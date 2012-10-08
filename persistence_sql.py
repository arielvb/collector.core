# -*- coding: utf-8 -*-
"""PersistenceAlchemy allows Collector to store the data using SQLAlchemy"""

# Take a look to dictionary collections p.95 true page: 109

from persistence import Persistence
from file import FileAlchemy
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.ext.associationproxy import association_proxy
from sqlalchemy import Column, Integer, String, Sequence, ForeignKey
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.pool import StaticPool
import os


class Alchemy(object):

    _instance = None
    echo = False

    def __init__(self):
        super(Alchemy, self).__init__()
        if Alchemy._instance is not None:
            raise Exception("Called more that once")
        Alchemy._instance = self
        self.engine = {}
        self.session = {}
        self.classes = {}
        self.Base = declarative_base()

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
            self.engine[key] = create_engine('sqlite:///' + key,
             connect_args={'check_same_thread': False},
             poolclass=StaticPool, echo=Alchemy.echo)
        return self.engine[key]

    def get_session(self, key):
        if not key in self.engine:
            raise Exception("key not found")
        if not key in self.session:
            self.session[key] = sessionmaker(bind=self.engine[key])()
        return self.session[key]


def multivalue_table_init(self, k):
    self.value = k


class PersistenceAlchemy(Persistence):

    """PersistenceAlchemy"""
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
        self._assoc = []

        attributes = self.get_columns(schema)
        self.class_ = type(str(schema.collection + "_" + schema.id),
                         (FileAlchemy, self.man.Base), attributes)
        self._session = self.man.get_session(file_path)

    def all_created(self):
        self.man.Base.metadata.create_all(self.engine)

    def next_id(self):
        """Returns the new id to insert in the table"""
        max_id = self.engine.execute("SELECT MAX(id) FROM %s;" %
                                self.subcollection).scalar()
        if max_id is None:
            max_id = 1
        return max_id + 1

    def get_columns(self, schema):
        columns = {}
        # Extra fields
        columns['__tablename__'] = schema.id
        columns['schema'] = schema

        # Note: sqlite doesn't use Sequence, its for Oracle
        columns['id'] = Column('id', Integer, Sequence('id_seq'),
                          primary_key=True)
        class_prefix = schema.collection + "_"

        for field in schema.file.values():
            id_ = field.get_id()
            value = Column(String)
            if field.class_ == 'int':
                value = Column(Integer)
            elif field.class_ == 'long':
                value = Column(Integer)
            elif field.class_ == 'ref':
                value = Column(Integer,
                             ForeignKey(field.ref_collection + '.id'))
                # Many to one:
                # without backref: [boardgames] * ---> 1 [designers]
                # with backref [boardgames] * <---> 1 [designers]
                rel = schema.collection + "_" + field.ref_collection
                columns[id_ + '_relation'] = relationship(rel,
                    primaryjoin="%s.%s==%s.id" %
                         (class_prefix + schema.id,
                          id_,
                          class_prefix + field.ref_collection),
                    backref=schema.id + ' ' + id_
                    )
            if field.is_multivalue():
                # One to many
                #             _id
                # [schema] 1 ----> * [values]
                assoc_table = str(schema.id + '_' + id_)
                assoc_attr = {
                    '__tablename__': assoc_table,
                    'id': Column(Integer, primary_key=True),
                    schema.id + '_id': Column(Integer,
                         ForeignKey(schema.id + '.id')),
                    'value': value,
                    '__init__': multivalue_table_init
                    }
                if field.class_ == 'ref':
                    # Reference fields are a bit special
                    # Many to many
                    rel = schema.collection + "_" + field.ref_collection
                    assoc_attr['ref'] = relationship(rel,
                            primaryjoin="%s.%s==%s.id" %
                                 (assoc_table,
                                  'value',
                                  class_prefix + field.ref_collection),
                            )
                ref_table = type(assoc_table,
                      (self.man.Base,), assoc_attr)

                columns[id_ + '_relation'] = relationship(ref_table)
                columna = association_proxy(id_ + '_relation', 'value')
            else:
                columna = value
            columns[id_] = columna
        return columns

    def get(self, _id):
        return self._session.query(self.class_).get(_id)

    def get_last(self, count):
        return self._session.query(self.class_).limit(count)

    def get_all(self, start_at, limit):
        if limit == 0:
            return self._session.query(self.class_).offset(start_at)
        else:
            return (self._session.query(self.class_).offset(start_at)
                    .limit(limit))

    def search(self, term):
        return self._session.query(self.class_).filter(
            getattr(self.class_, self.schema.default).contains(term)
            ).all()

    def save(self, values):
        obj = self.class_(values)
        if 'id' not in values:
            self._session.add(obj)
            self._session.commit()
            values['id'] = obj.id
        else:
            obj = self._session.query(self.class_).get(values['id'])
            obj.update(values)
            self._session.commit()
        return obj

    def load_references(self, collections, item):
        """Loads all the referenced values using sqlalchemy relations"""
        if 'refLoaded' in item:
            return
        out = {}
        fields = self.schema.file
        for field in fields.values():
            id_ = field.get_id()
            if field.class_ == 'ref':
                if not field.is_multivalue():
                    ref = getattr(item, id_ + '_relation')
                    if ref is not None:
                        out[id_] = getattr(ref, field.ref_field)
                    else:
                        out[id_] = ''
                    del ref
                else:
                    refs = getattr(item, id_ + '_relation')
                    out[id_] = []
                    for i in refs:
                        ref = getattr(i, 'ref')
                        out[id_].append(getattr(ref, field.ref_field))

            elif field.is_multivalue():
                out[id_] = item[id_].copy()
            else:
                out[id_] = item[id_]

        out['refLoaded'] = True
        return out
