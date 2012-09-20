# -*- coding: utf-8 -*-
#TODO redo all the class, we need to use sqlite3, or sqlalchemy
import os
from config import Config
import pickle


class Persistence(object):
    """Abstract class for Persitence"""

    def __init__(self, collectionName, params={}):
        super(Persistence, self).__init__()
        if not isinstance(params, dict):
            raise Exception('Params are not a dict')

    def get(self):
        pass

    def getAll(self):
        pass

    def getLast(self):
        pass

    def search(self):
        pass

    def save(self):
        pass


class PersistenceDict(Persistence):
    """Implementation of persistence using a python dictionary"""

    _autoid = 1
    FILE_EXTENSION = '.p'
    CONFIG_DIR_MODE = 0700
    path = None

    def __init__(self, collectionName, subcollection, params={}, data=None):
        super(PersistenceDict, self).__init__(params)
        # Obtain items from the params
        #self.items = params[collectionName]

        # Create collection folder
        # TODO this must go inside collection
        apppath = Config.getInstance().get_data_path()
        path = os.path.join(apppath, 'collections', collectionName)
        if not os.path.exists(path):
            os.makedirs(path, self.CONFIG_DIR_MODE)
        self.items = []
        if data is None:
            pickle_file = os.path.join(path, subcollection +
                                       self.FILE_EXTENSION)
            if os.path.exists(pickle_file):
                f = open(pickle_file)
                self.items = pickle.load(f)
                f.close()
            self.path = pickle_file
        else:
            self.items = data

        self._calc_autoid()

    def _calc_autoid(self):
        maxid = 0
        for i in self.items:
            maxid = max(maxid, i['id'])
        self._autoid = maxid + 1

    def getLast(self, count):
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
        for a in self.items:
            if _id == a['id']:
                return a
        return None

    def getAll(self, startAt, limit):
        return self.items

    def search(self, term):
        results = []
        term = term.lower()
        for item in self.items:
            if item['name'].lower().find(term) != -1:
                results.append(item)
        return results

    def save(self, values):
        #TODO !
        if 'id' in values:
            for item in self.items:
                if values['id'] == item['id']:
                    item.update(values)
        else:
            values['id'] = self._autoid
            self._autoid += 1
            self.items.append(values)
        self.commit()

    def delete(self, id):
        for item in self.items:
            if item['id'] == id:
                self.items.remove(item)
        self.commit()

    def commit(self):
        """Stores the changes"""
        # Store with pickle
        if not self.path is None:
            f = open(self.path, 'wb')
            pickle.dump(self.items, f)
            f.close()


class PersistenceManager(object):
    """PersistenceManager loads the correct persistence form the input
     parameters"""

    _instance = None

    def __init__(self):
        if not PersistenceManager._instance is None:
            raise Exception('Called more that once')

        super(PersistenceManager, self).__init__()
        self.storageEngine = {
            'pickle': PersistenceDict
        }

    def getStorage(self, collectionName, subcollection, storage, params={}):
        # TODO add storage cache
        return self.storageEngine[storage](collectionName, subcollection, params)

    @staticmethod
    def getInstance():
        if PersistenceManager._instance is None:
            PersistenceManager._instance = PersistenceManager()
        return PersistenceManager._instance


