# -*- coding: utf-8 -*-
"""PersistenceAlchemy allows Collector to store the data using SQLAlchemy"""

# Take a look to dictionary collections p.95 true page: 109

from persistence import Persistence
from file import FileAlchemy
from engine.filter import Filter
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.ext.associationproxy import association_proxy
from sqlalchemy import Column, Integer, String, Sequence, ForeignKey
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.pool import StaticPool
import os


class FilterEquals(Filter):
    """The equivalence filter"""

    @staticmethod
    def get_id():
        return 'equals'

    @staticmethod
    def get_description():
        return "An equivalence relationship"

    @staticmethod
    def get_name():
        return "="

    @staticmethod
    def filter(params):
        """Builds the query filter"""
        if not isinstance(params, list) or len(params) != 3:
            raise ValueError()
        left = params[1]
        right = params[2]
        query = getattr(params[0], left) == right
        return query


class FilterLike(Filter):
    """The like filter"""

    @staticmethod
    def get_id():
        return 'like'

    @staticmethod
    def get_description():
        return "Looks if a text is containet into another"

    @staticmethod
    def get_name():
        return "contains"

    @staticmethod
    def filter(params):
        """Builds the query filter"""
        if not isinstance(params, list) or len(params) != 3:
            raise ValueError()
        left = params[1]
        right = params[2]
        query = getattr(params[0], left).contains(right)
        return query


class Alchemy(object):
    """ Alchemy connects the PersistenceAlchemy with the sessions
     of SQLAlchemy"""

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
        self.filters = self._create_filters()
        self.base = declarative_base()

    @classmethod
    def _create_filters(cls):
        """Creates the default avaible filters for SQLAlchemy"""
        filters = {}
        for i in [FilterEquals, FilterLike]:
            filters[i.get_id()] = i()
        # i = FilterEquals()
        # filters[i.get_id()] = i
        # i = FilterLike()
        # filters[i.get_id()] = i
        return filters

    @staticmethod
    def destroy():
        """Destroy the instance"""
        Alchemy._instance = None

    @staticmethod
    def get_instance():
        """Returns the alchemy instance"""
        if Alchemy._instance is None:
            Alchemy._instance = Alchemy()
        return Alchemy._instance

    def get_engine(self, key):
        """Rertuns the sqlalchemy engine, for the requested DB"""
        if not key in self.engine:
            self.engine[key] = create_engine('sqlite:///' + key,
             connect_args={'check_same_thread': False},
             poolclass=StaticPool, echo=Alchemy.echo)
        return self.engine[key]

    def get_session(self, key):
        """Returns the session for the requested DB"""
        if not key in self.engine:
            raise Exception("key not found")
        if not key in self.session:
            self.session[key] = sessionmaker(bind=self.engine[key])()
        return self.session[key]

    def get_filter(self, key):
        """Returns the requested filter"""
        return self.filters[key]


def _multivalue_table_init(self, k):
    """__init__ for the multivalue association table"""
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
                         (FileAlchemy, self.man.base), attributes)
        self._session = self.man.get_session(file_path)

    def all_created(self):
        self.man.base.metadata.create_all(self.engine)

    def next_id(self):
        """Returns the new id to insert in the table"""
        max_id = self.engine.execute("SELECT MAX(id) FROM %s;" %
                                self.subcollection).scalar()
        if max_id is None:
            max_id = 1
        return max_id + 1

    def filter(self, filters):
        query = self.build_filter_query(filters)
        return self._session.query(self.class_).filter(query).all()

    def build_filter_query(self, filters):
        """Builds a query filter"""
        query = None
        alchemy = Alchemy.get_instance()
        for i in filters:
            if i in alchemy.filters and i in ['equals', 'like']:
                params = [self.class_]
                params.extend(filters[i])
                query = alchemy.get_filter(i).filter(
                    params
                )
            # TODO iterate over all and join them with an "and"
        return query

    def get_columns(self, schema):
        """Generates the columns and subclasses needed to build
         the schema table"""
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
                    '__init__': _multivalue_table_init
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
                      (self.man.base,), assoc_attr)

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
            return self._session.query(self.class_).offset(start_at).all()
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

    def delete(self, id_):
        obj = self._session.query(self.class_).get(id_)
        if not obj is None:
            self._session.delete(obj)
            self._session.commit()

    def load_references(self, collections, item):
        """Loads all the referenced values using sqlalchemy relations"""
        if 'refLoaded' in item:
            return
        out = {'id': item['id']}
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
