# -*- coding: utf-8 -*-
"""Persistence allows Collector to store the data in a persistence way"""

from abc import ABCMeta, abstractmethod
import copy
from storage import JSONStorage
from file import FileDict


class Persistence(object):
    """Abstract class for Persitence"""

    __metaclass__ = ABCMeta

    def __init__(self, schema, path, params=None):
        super(Persistence, self).__init__()
        if not params is None and not isinstance(params, dict):
            raise Exception('Params are not a dict')
        self.path = path
        self.schema = schema
        self.collection_id = schema.collection
        self.subcollection = schema.id
        self.params = params

    @abstractmethod
    def get(self, _id):
        """Returns the entry whit identifier *id*"""

    @abstractmethod
    def get_all(self, start_at, limit):
        """Returns all the entrys, allows pagination with *start_at* and
         *limit*"""

    @abstractmethod
    def get_last(self, count):
        """Returns the last inserted items, maximum *count*"""

    @abstractmethod
    def search(self, term):
        """Search entry who match the parameter term"""

    @abstractmethod
    def save(self, values):
        """Saves the values if they have a valid id or creates a new entry"""

    @abstractmethod
    def load_references(self, collections, item):
        """Loads all the referenced values"""

    def all_created(self):
        """Hook: called when all the files of the collection has been loaded"""


class PersistenceDict(Persistence):
    """Implementation of persistence using a python dictionary"""

    _autoid = 1

    def __init__(self, schema, path, params=None):
        super(PersistenceDict, self).__init__(schema, path, params)
        self.items = []
        self.data_storage = None
        self.memory = False
        # configure
        self.configure()

    def configure(self):
        """Configures the storage system"""
        # Read params
        if self.params is None:
            self.params = {}
        params = self.params
        self.memory = params.get('memory', False)
        data = params.get('data', None)
        if self.path is not None:
            self.data_storage = JSONStorage(
                self.path,
                self.subcollection,
                self.memory)
            self.items = self.data_storage.load()
        elif data is not None:
            self.items = data

        self._calc_autoid()

    def _calc_autoid(self):
        """Searchs the max id used and set's the new autoid value"""
        maxid = 0
        for i in self.items:
            maxid = max(maxid, i['id'])
        self._autoid = maxid + 1

    def get_last(self, count):
        """Returns the last items created, the number of items are defined
         with the count parameter, the items are orderded by last inserted"""
        result = self.items[-count:]
        # Reverse the count
        objects = []
        result.reverse()
        for item in result:
            objects.append(FileDict(item))
        return objects

    def get(self, _id):
        # TODO validate id is integer
        if isinstance(_id, str):
            _id = int(_id)
        for item in self.items:
            if _id == item['id']:
                return FileDict(item)
        return None

    def get_all(self, start_at, limit):
        """Returns all the items starting at *start_at*, the results could
         be limited whit *limit*"""
        result = []
        objects = []
        if limit == 0:
            objects = self.items[start_at:]
        else:
            objects = self.items[start_at:(start_at + limit)]
        for item in objects:
            result.append(FileDict(item))
        return result

    def search(self, term):
        results = []
        term = term.lower()
        for item in self.items:
            if item['title'].lower().find(term) != -1:
                results.append(FileDict(item))
        return results

    def save(self, values):
        if 'id' in values:
            for item in self.items:
                if values['id'] == item['id']:
                    item.update(values)
        else:
            values['id'] = self._autoid
            self._autoid += 1
            self.items.append(values)
        self.commit()

    def delete(self, _id):
        """Deletes the entry whit identifier *_id*"""
        for item in self.items:
            if item['id'] == _id:
                self.items.remove(item)
        self.commit()

    def commit(self):
        """Stores the changes"""
        if self.data_storage is not None:
            self.data_storage.save(self.items)

    def load_references(self, collections, item):
        #TODO group reference values for a faster load
        item = copy.deepcopy(item)
        if 'refLoaded' in item:
            return

        fields = self.schema.file
        for field in fields.values():
            id_ = field.get_id()
            if field.class_ == 'ref':
                ref_collection = collections.get_collection(
                    field.ref_collection
                )
                if not field.is_multivalue():
                    ref = item[id_]
                    ref_item = ref_collection.get(ref)
                    if ref_item is not None:
                        item[id_] = ref_item[field.ref_field]
                else:
                    _list = item[id_]
                    for i in range(0, len(_list)):
                        if _list[i] != '':
                            ref = _list[i]
                            ref_item = ref_collection.get(ref)
                            if ref_item is not None:
                                _list[i] = ref_item[field.ref_field]
                            # else:
                                # _list[i] = u'Error: Unknown value'
        item['refLoaded'] = True
        return item


class PersistenceManager(object):
    """PersistenceManager loads the correct persistence form the input
     parameters"""

    _instance = None

    def __init__(self):
        if not PersistenceManager._instance is None:
            raise Exception('Called more that once')

        super(PersistenceManager, self).__init__()
        from persistence_sql import PersistenceAlchemy

        self.storages = {
            'pickle': PersistenceDict,
            'sqlalchemy': PersistenceAlchemy
        }

    @staticmethod
    def load_schema(path, collection, readonly):
        """Returns an schema represented as a python dict"""
        return JSONStorage(path, collection, readonly).load()

    def get_storage(self, schema, storage, path, params=None):
        """Returns the persistence class that matches the parameters"""
        return self.storages[storage](schema, path, params)

    @staticmethod
    def get_instance():
        """Returns the instance of the PersistenceManager"""
        if PersistenceManager._instance is None:
            PersistenceManager._instance = PersistenceManager()
        return PersistenceManager._instance
