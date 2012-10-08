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
        # TODO (important) for each field that is multivalue whe must
        # create a new class, and the attribute must be a foreing key!
        # or ... take a look to sqlalchemy: Relationships
        # For reference value also a relations must be defeined
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
            elif field.class_ == 'ref':
                value = Column(Integer,
                             ForeignKey(field.ref_collection + '.id'))
            if field.is_multivalue():
                # One to many
                #             _id
                # [schema] 1 ----> * [values]
                assoc_table = str(schema.id + '_' + id_)
                ref_table = type(assoc_table,
                      (self.man.Base,), {
                      '__tablename__': assoc_table,
                      'id': Column(Integer, primary_key=True),
                      schema.id + '_id': Column(Integer,
                             ForeignKey(schema.id + '.id')),
                      'value': value,
                      '__init__': multivalue_table_init
                      })
                columns[id_ + 'relation'] = relationship(ref_table)
                columna = association_proxy(id_ + 'relation', 'value')
            else:
                if field.class_ == 'ref':
                    if field.is_multivalue():
                        raise Exception("Multivalue ref is "
                            "not supported by SQL")
                    # assoc_table = str(schema.id + '_' + id_)
                    # ref_table = type(assoc_table,
                    #       (self.man.Base,), {
                    #       '__tablename__': assoc_table,
                    #       'id': Column(Integer, primary_key=True),
                    #       schema.id + '_id': Column(Integer,
                    #              ForeignKey(schema.id + '.id')),
                    #       field.ref_collection + '_id': Column(Integer,
                    #         ForeignKey(field.ref_collection + '.id'))
                    #       })
                    # columns['relation' + '_' + id_] = relationship(ref_table, uselist=False,
                    #                              backref=id_ + 'backref')
                    # This case is only for references that aren't multivalue
                    #  for multivalues references, is needed a extra table, the
                    #  code comented up and down is and aproximitation.

                    # Many to one:
                    # without backref: [boardgames] * ---> 1 [designers]
                    # with backref [boardgames] * <---> 1 [designers]
                    columna = value
                    rel = schema.collection + "_" + field.ref_collection
                    columns[id_ + '_relation'] = relationship(rel,
                        primaryjoin="%s.%s==%s.id" %
                             (class_prefix + schema.id,
                              id_,
                              class_prefix + field.ref_collection),
                        backref=schema.id + ' ' + id_
                        )

                    # self._assoc.append(ref_table)
                    # columna = association_proxy('relation' + '_' + id_,
                    #             field.ref_collection + '_id'    ,
                    #             creator = lambda value: ref_table())
                else:
                    # if field.class_ in ['int', 'text' or 'image']
                    columna = value
            columns[id_] = columna
        # TODO clean debug line
        # from PyQt4.Qt import qDebug; qDebug("AAA " + str(columns))
        return columns

    def get(self, _id):
        return self._session.query(self.class_).get(_id)

    def get_last(self, count):
        return self._session.query(self.class_).limit(count)

    def get_all(self, start_at, limit):
        # TODO
        return self._session.query(self.class_).all()

    def search(self, term):
        return self._session.query(self.class_).filter(
            getattr(self.class_, self.schema.default).contains(term)
            ).all()

    def save(self, values):
        # TODO fixme, value must not be a dictionary must be a File
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
        # TODO implement multivalue references
        if 'refLoaded' in item:
            return
        out = {}
        fields = self.schema.file
        for field in fields.values():
            id_ = field.get_id()
            if field.class_ == 'ref':
                ref = getattr(item, id_ + '_relation')
                if ref is not None:
                    out[id_] = getattr(ref, field.ref_field)
                else:
                    out[id_] = ''
            elif field.is_multivalue():
                out[id_] = item[id_].copy()
            else:
                out[id_] = item[id_]

        out['refLoaded'] = True
        return out
