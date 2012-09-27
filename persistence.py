# -*- coding: utf-8 -*-
"""Persistence allows Collector to store the data in a persistence way"""

import os
from config import Config
import pickle
from abc import ABCMeta, abstractmethod
import copy
from storage import PickleStorage, JSONStorage


class Persistence(object):
    """Abstract class for Persitence"""

    __metaclass__ = ABCMeta

    def __init__(self, collection_id, subcollection, path, params=None):
        super(Persistence, self).__init__()
        if not params is None and not isinstance(params, dict):
            raise Exception('Params are not a dict')
        self.path = path
        self.collection_id = collection_id
        self.subcollection = subcollection
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


class PersistenceDict(Persistence):
    """Implementation of persistence using a python dictionary"""

    _autoid = 1

    def __init__(self, collection_id, subcollection, path, params=None):
        super(PersistenceDict, self).__init__(collection_id,
         subcollection, path, params)
        self.items = []
        self.data_storage = None
        self.memory = False
        # configure
        self.configure()
        # Create collection folder
        # self._create_path()

    def configure(self):
        """Configures the storage system"""
        # Read params
        if self.params is None:
            self.params = {}
        params = self.params
        self.memory = params.get('memory', False)
        data = params.get('data', None)
        if self.path is not None:
            self.data_storage = PickleStorage(
                self.path,
                self.subcollection,
                self.memory)
            self.items = self.data_storage.load()
            # pickle_file = os.path.join(self.path, self.subcollection +
            #                            self.FILE_EXTENSION)
            # if os.path.exists(pickle_file):
            #     _file = open(pickle_file)
            #     self.items = pickle.load(_file)
            #     _file.close()
            #     self.pickle_file = pickle_file
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
        result.reverse()
        return result

    def get(self, _id):
        # TODO validate id is integer
        if isinstance(_id, str):
            _id = int(_id)
        for item in self.items:
            if _id == item['id']:
                return copy.deepcopy(item)
        return None

    def get_all(self, start_at, limit):
        """Returns all the items starting at *start_at*, the results could
         be limited whit *limit*"""
        if limit == 0:
            return self.items[start_at:]
        else:
            return self.items[start_at:(start_at + limit)]

    def search(self, term):
        results = []
        term = term.lower()
        for item in self.items:
            if item['name'].lower().find(term) != -1:
                results.append(copy.deepcopy(item))
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
        # Store with pickle
        # if not (self.pickle_file is None and self.memory):
        #     dst = open(self.pickle_file, 'wb')
        #     pickle.dump(self.items, dst)
        #     dst.close()


class PersistenceManager(object):
    """PersistenceManager loads the correct persistence form the input
     parameters"""

    _instance = None

    def __init__(self):
        if not PersistenceManager._instance is None:
            raise Exception('Called more that once')

        super(PersistenceManager, self).__init__()
        self.storages = {
            'pickle': PersistenceDict
        }

    @staticmethod
    def load_schema(path, collection, readonly):
        return JSONStorage(path, collection, readonly).load()

    def get_storage(self, collection_id, subcollection, storage,
                   path, params=None):
        """Returns the persistence class that matches the parameters"""
        return self.storages[storage](
            collection_id,
            subcollection,
            path,
            params)

    @staticmethod
    def get_instance():
        """Returns the instance of the PersistenceManager"""
        if PersistenceManager._instance is None:
            PersistenceManager._instance = PersistenceManager()
        return PersistenceManager._instance

#TODO create a new class, we need to use sqlite3, or sqlalchemy
