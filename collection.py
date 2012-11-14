# -*- coding: utf-8 -*-
"""Collection is the core object of the engine, a collection is a group
of files."""
from persistence import PersistenceManager
from schema import Schema
from config import Config
import logging
import os

class Folder(object):
    """Folder class"""

    def __init__(self, id_, schema, persistence):
        super(Folder, self).__init__()
        self.id_ = id_
        self.schema = schema
        self.persistence = persistence

    def get_id(self):
        """Returns the identifier of the folder"""
        return self.id_

    def get_name(self):
        """Returns the name of the folder"""
        return self.schema.name

    def get_image(self):
        """Returns the path of the representative image of the folder"""
        return self.schema.image

    def get_last(self, limit=10):
        """ Finds last items created at the folder."""
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

    def save(self, obj):
        """Save the objet adding it to the file"""
        copy = Config.get_instance().get('copy')
        if copy != 'never':
            for i in self.schema.file.values():
                # TODO support other types of file
                if i.class_ == "image":
                    if i.is_multivalue():
                        raise Exception("Multivalue for images isn't"
                                        "supported")
                    value = obj[i.get_id()]
                    # TODO multivalue support for files
                    value = self.persistence.addfile(value, copy)
                    if value is not None:
                        obj[i.get_id()] = value

        return self.persistence.save(obj)

    def delete(self, obj):
        """Deletes the objecte form the file"""
        return self.persistence.delete(obj)

    def load_references(self, item):
        """Returns a copy of the object with all the references loaded"""
        man = Collection.get_instance()
        return self.persistence.load_references(man, item)

    def filter(self, filters):
        if not isinstance(filters, dict):
            raise ValueError("Filter must be a dictionary")
        return self.persistence.filter(filters)


class Collection():
    """A collection is a group of Folders and some proper"""
    collections = {}
    # TODO Collection is not singleton and discover, is_collection...
    #  methods will go inside collector.Collector
    _instance = None

    @staticmethod
    def get_instance(autodiscover=False):
        """Retuns the instance of the collector, if the instance doesn'try:
            exists creates a new one with the autodiscover value"""
        if Collection._instance is None:
            Collection._instance = Collection(autodiscover)
        return Collection._instance

    @staticmethod
    def is_collection_folder(item):
        """Checks that the item (path) is a Collection folder"""
        # TODO this must check more things
        return os.path.isdir(item)

    def __init__(self, autodiscover=False):
        self.storage = None
        self._raw = {}
        if Collection._instance is not None:
            raise Exception('Called more than once')
        Collection._instance = self
        config = Config.get_instance()
        path = os.path.join(config.get_data_path(), 'collections')
        if autodiscover:
            self.collections = self.load_collections(path)
        else:
            self.collections = {}

    #TODO this method needs to be in the FrontController (aka. Collector)
    def load_collections(self, path):
        """Looks in the choosed path for new collections"""
        allfiles = []
        collections = {}
        try:
            allfiles = os.listdir(path)
        except Exception as error:
            logging.exception(error)

        pers_man = PersistenceManager.get_instance()
        for item in allfiles:
            c_path = os.path.join(path, item)
            if Collection.is_collection_folder(c_path):
                self.storage = PersistenceManager.load_schema(c_path, item,
                                                     readonly=False)
                self._raw = self.storage.load()
                raw = self._raw
                persistence = raw['persistence']
                schemas = raw['schemas']
                for id_ in schemas:
                    file_ = Schema(item, id_, schemas[id_])
                    storage = pers_man.get_storage(file_,
                                                  persistence['storage'],
                                                  c_path
                                                  )
                    collection = Folder(
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

    def get_persistence(self):
        """Returns the persistence system of the Collection"""
        return self._raw['persistence']['storage']

    def get_properties(self):
        """Rerturns all the properties"""
        return self._raw

    def get_property(self, key):
        """Returns a property of the collection"""
        return self._raw.get(key, None)

    def get_collection(self, id_):
        """Returns a Collection/Subcollection"""
        return self.collections[id_]

    def get_mapping(self, key):
        """Returns the mapping for the requested key, is a shortcut to
         get_property('mappings')[key]"""
        return self._raw['mappings'][key]

    def set_properties(self, values):
        """Sets the properties of the collection, firts parameter is a
         dictionary and the allowed keys are:
            :title:    title of the  collection
            :author:  author of the collection
            :description: description of the collection
        All the keys are optional
        """
        valid_properties = ['title', 'description', 'author', 'dashboard']
        for i in values.items():
            if i[0] in valid_properties:
                self._raw[i[0]] = i[1]
        self.commit()

    def commit(self):
        """Stores persistenctly if a Storage has been defined"""
        if self.storage is not None:
            self.storage.save(self._raw)
