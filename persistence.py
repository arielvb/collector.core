# -*- coding: utf-8 -*-
"""Persistence allows Collector to store the data in a persistence way"""

from abc import ABCMeta, abstractmethod
from storage import JSONStorage
from file import FileDict
import logging
import os
import shutil
import urllib
import uuid


class Order(object):
    """Order modifier for querys an filters"""

    def __init__(self, fields, asc=True):
        super(Order, self).__init__()
        self.asc = asc
        self.fields = fields


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

    def addfile(self, filename, mode):
        """Persists a file, it will add to the storage if mode is always or
         if mode is *http* will copy only http resources. Also exists a
         *never* mode."""
        if mode == 'never':
            return filename
        http = False
        if filename.startswith('http'):
            filename, headers = urllib.urlretrieve(filename)
            http = True
        if not http and mode == 'http':
            return filename
        dst = os.path.join(self.path, "files", str(uuid.uuid4()))
        try:
            folder = os.path.join(self.path, "files")
            if not os.path.exists(folder):
                os.mkdir(folder)
            shutil.copyfile(filename, dst)
            dst = dst.replace(self.path, '')
            dst = "collector://collections/" + self.collection_id + "/" + dst

        except IOError as ioex:
            logging.exception(ioex)
            return None
        return dst

    @abstractmethod
    def delete(self, _id):
        """Deletes the entry whit identifier *_id*"""

    @abstractmethod
    def filter(self, filters):
        """Applies a set of filters before retrieve the data"""

    @abstractmethod
    def get(self, _id):
        """Returns the entry whit identifier *id*"""

    @abstractmethod
    def get_all(self, start_at, limit, order=None):
        """Returns all the entrys, allows pagination with *start_at* and
         *limit*"""

    @abstractmethod
    def get_filters(self):
        """Returns all the avaible filters"""

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
        self.class_ = type(str(schema.collection + "_" + schema.id),
                           (FileDict,), {"schema": schema.id})
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
            if self.items is None:
                self.items = []
        if data is not None:
            self.items = data

        self._calc_autoid()

    def _calc_autoid(self):
        """Searchs the max id used and set's the new autoid value"""
        maxid = 0
        for i in self.items:
            maxid = max(maxid, i['id'])
        self._autoid = maxid + 1

    def filter(self, fitlers):
        # TODO
        raise Exception("Not Implemented")

    def get_filters(self):
        #TODO
        return []

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
        if isinstance(_id, str):
            _id = int(_id)
        for item in self.items:
            if _id == item['id']:
                return FileDict(item)
        return None

    def get_all(self, start_at, limit, order=None):
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
        for item in self.items:
            if item['id'] == _id:
                self.items.remove(item)
        self.commit()

    def commit(self):
        """Stores the changes"""
        if self.data_storage is not None:
            self.data_storage.save(self.items)

    def load_references(self, collections, item):
        if 'refLoaded' in item:
            return
        item = item.copy()
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
        return JSONStorage(path, collection, readonly)

    def get_storage(self, schema, storage, path, params=None):
        """Returns the persistence class that matches the parameters"""
        return self.storages[storage](schema, path, params)

    @staticmethod
    def get_instance():
        """Returns the instance of the PersistenceManager"""
        if PersistenceManager._instance is None:
            PersistenceManager._instance = PersistenceManager()
        return PersistenceManager._instance
