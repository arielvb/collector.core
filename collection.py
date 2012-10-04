# -*- coding: utf-8 -*-
from persistence import PersistenceManager
from schema import Schema
from config import Config
import logging
import os


class Collection(object):

    def __init__(self, id_, schema, persistence):
        super(Collection, self).__init__()
        self.name = id_
        self.schema = schema
        self.db = persistence

    def getName(self):
        return self.schema.name

    def get_image(self):
        return self.schema.image

    def getLast(self, limit=10):
        """ Finds last items created at the collection."""
        return self.db.get_last(limit)

    def get(self, id):
        return self.db.get(id)

    def get_all(self, startAt=0, limit=0):
        """ Finds all the items, optinally results could be called
            using startAt and limit, useful for pagination.
        """
        # TODO validate startAt and limit are integers
        return self.db.get_all(startAt, limit)

    def query(self, term):
        return self.db.search(term)

    def save(self, obj):
        return self.db.save(obj)

    def delete(self, obj):
        return self.db.delete(obj)

    def getConfig(self):
        # TODO refractor to collector
        return self._config

    def loadReferences(self, item):
        man = CollectionManager.get_instance()
        return self.db.load_references(man, item)


class CollectionManager():

    collections = {}
    _instance = None

    @staticmethod
    def get_instance():
        if CollectionManager._instance is None:
            CollectionManager._instance = CollectionManager()
        return CollectionManager._instance

    def __init__(self, autodiscover=True):
        self.persistence = ''
        self.name = ''
        self.title = ''
        self.author = ''
        self.description = ''
        if CollectionManager._instance is not None:
            raise Exception('Called more than once')
        CollectionManager._instance = self
        self._config = Config.get_instance()
        path = os.path.join(self._config.get_data_path(), 'collections')
        if autodiscover:
            self.collections = self.discover_collections(path)
        else:
            self.collections = {}

    def discover_collections(self, path):
        allfiles = []
        collections = {}
        try:
            allfiles = os.listdir(path)
        except Exception as error:
            logging.exception(error)

        pers_man = PersistenceManager.get_instance()
        for item in allfiles:
            c_path = os.path.join(path, item)
            if CollectionManager.is_collection_folder(c_path):
                #TODO remove readonly argument
                raw = PersistenceManager.load_schema(c_path, item,
                                                     readonly=True)
                persistence = raw['persistence']
                self.author = raw['author']
                self.title = raw['name']
                self.description = raw['description']
                self.persistence = persistence['storage']
                schemas = raw['schemas']
                for id_ in schemas:
                    file_ = Schema(item, id_, schemas[id_])
                    storage = pers_man.get_storage(file_,
                                                  self.persistence,
                                                  c_path
                                                  )
                    collection = Collection(
                        id_,
                        file_,
                        storage)
                    collections[id_] = collection
                # TODO this notify must be a hook
                for collection in collections.values():
                    collection.db.all_created()
                #TODO load more than one
                return collections
                # except Exception:
                #     pass
        return collections

    def get_author(self):
        return self.author

    def get_title(self):
        return self.title

    def get_persistence(self):
        return self.persistence

    def get_description(self):
        return self.description

    def getCollection(self, collectionName):
        return self.collections[collectionName]

    get_collection = getCollection

    def getConfig(self):
        return self._config

    @staticmethod
    def is_collection_folder(item):
        return os.path.isdir(item)
