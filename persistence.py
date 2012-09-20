# -*- coding: utf-8 -*-
"""Persistence allows Collector to store the data in a persistence way"""

import os
from config import Config
import pickle
from abc import ABCMeta, abstractmethod
import copy


class Persistence(object):
    """Abstract class for Persitence"""

    __metaclass__ = ABCMeta

    def __init__(self, collection_id, subcollection, params=None, data=None):
        super(Persistence, self).__init__()
        if not params is None and not isinstance(params, dict):
            raise Exception('Params are not a dict')

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
    FILE_EXTENSION = '.p'
    CONFIG_DIR_MODE = 0700
    path = None

    def __init__(self, collection_id, subcollection, params={}, data=None):
        super(PersistenceDict,
              self).__init__(collection_id, subcollection, params, data)
        # Obtain items from the params
        #self.items = params[collection_id]

        # Create collection folder
        # TODO this must go inside collection
        self.path = None
        apppath = Config.get_instance().get_data_path()
        path = os.path.join(apppath, 'collections', collection_id)
        if not os.path.exists(path):
            os.makedirs(path, self.CONFIG_DIR_MODE)
        self.items = []
        if data is None:
            pickle_file = os.path.join(path, subcollection +
                                       self.FILE_EXTENSION)
            if os.path.exists(pickle_file):
                _file = open(pickle_file)
                self.items = pickle.load(_file)
                _file.close()
            self.path = pickle_file
        else:
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
        return self.items

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
        # Store with pickle
        if not self.path is None:
            dst = open(self.path, 'wb')
            pickle.dump(self.items, dst)
            dst.close()


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

    def getStorage(self, collection_id, subcollection, storage, params={}):
        """Returns the persistence class that matches the parameters"""
        # TODO add storage cache
        return self.storages[storage](
            collection_id,
            subcollection,
            params)

    @staticmethod
    def get_instance():
        """Returns the instance of the PersistenceManager"""
        if PersistenceManager._instance is None:
            PersistenceManager._instance = PersistenceManager()
        return PersistenceManager._instance

#TODO create a new class, we need to use sqlite3, or sqlalchemy

