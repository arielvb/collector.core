# -*- coding: utf-8 -*-
"""Collection is the core object of the engine, a collection is a group
of files."""
from persistence import PersistenceManager
from schema import Schema
from config import Config
import logging
import os

#TODO this must be the Folder Class

class Collection(object):
    """Collection class"""

    def __init__(self, id_, schema, persistence):
        super(Collection, self).__init__()
        self.id_ = id_
        self.schema = schema
        self.persistence = persistence

    def get_id(self):
        """Returns the identifier of the collection"""
        return self.id_

    def get_name(self):
        """Returns the name of the collection"""
        return self.schema.name

    def get_image(self):
        """Returns the path of the representative image of the collection"""
        return self.schema.image

    def get_last(self, limit=10):
        """ Finds last items created at the collection."""
        return self.persistence.get_last(limit)

    def get(self, id_):
        """Returns a file by id"""
        return self.persistence.get(id_)

    def get_all(self, start_at=0, limit=0):
        """ Finds all the items, optinally results could be called
            using startAt and limit, useful for pagination.
        """
        # TODO validate startAt and limit are integers
        return self.persistence.get_all(start_at, limit)

    def query(self, term):
        """Search over the file for entrys that match the term"""
        return self.persistence.search(term)

    def save(self, obj):
        """Save the objet adding it to the file"""
        return self.persistence.save(obj)

    def delete(self, obj):
        """Deletes the objecte form the file"""
        return self.persistence.delete(obj)

    def load_references(self, item):
        """Returns a copy of the object with all the references loaded"""
        man = CollectionManager.get_instance()
        return self.persistence.load_references(man, item)

# TODO this must be the Collection class, but is not singleton and the
#  the discover method will go inside collector.Collector

class CollectionManager():

    collections = {}
    _instance = None

    @staticmethod
    def get_instance(autodiscover=False):
        if CollectionManager._instance is None:
            CollectionManager._instance = CollectionManager(autodiscover)
        return CollectionManager._instance

    def __init__(self, autodiscover=False):
        self.persistence = ''
        self.name = ''
        self.title = ''
        self.author = ''
        self.description = ''
        if CollectionManager._instance is not None:
            raise Exception('Called more than once')
        CollectionManager._instance = self
        config = Config.get_instance()
        path = os.path.join(config.get_data_path(), 'collections')
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
                    collection.persistence.all_created()
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

    def get_collection(self, collectionName):
        return self.collections[collectionName]

    @staticmethod
    def is_collection_folder(item):
        return os.path.isdir(item)
