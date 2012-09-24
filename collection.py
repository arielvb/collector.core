# -*- coding: utf-8 -*-
from persistence import PersistenceManager
from schema import Schema
from config import Config


class Collection(object):

    def __init__(self, collectionName, schema, persistence):
        super(Collection, self).__init__()
        self.name = collectionName
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
        #TODO this code needs use the Field Abstract Class
        #TODO group reference values for a faster load
        if 'refLoaded' in item:
            return

        fields = self.schema.fields
        collections = CollectionManager.get_instance()
        for fieldId in fields:
            field = fields[fieldId]
            if field['class'] == 'ref':
                config = field['params']['ref'].split('.')
                # TODO how to control if the references of the item aren't yet loaded
                if len(config) == 2:
                    refCollection = collections.getCollection(config[0])
                    refAttr = config[1]
                    #TODO warning when ref[0] is difrent a refCollection.name, the schema was updated
                    # but not the db
                    if 'multiple' not in field:
                        ref = item[fieldId].split(':')
                        if (len(ref) == 2):
                            refItem = refCollection.get(ref[1])
                            item[fieldId] = refItem[refAttr]
                    else:
                        _list = item[fieldId]
                        for i in range(0, len(_list)):
                            if _list[i] != '':
                                ref = _list[i].split(':')
                                refItem = refCollection.get(ref[1])
                                _list[i] = refItem[refAttr]
        item['refLoaded'] = True

import os
import json

_collectionManagerInstance = None


class CollectionManager():

    collections = {}

    def __init__(self):
        self.persistence = ''
        self.name = ''
        self.title = ''
        self.author = ''
        if _collectionManagerInstance is not None:
            raise Exception('Called more than once')
        self._config = Config.get_instance()
        path = os.path.join(self._config.get_data_path(), 'collections')
        self.collections = self.discover_collections(path)

    def discover_collections(self, path):
        allfiles = []
        collections = {}
        try:
            allfiles = os.listdir(path)
        except Exception:
            #TODO log this!
            pass
        pers_man = PersistenceManager.get_instance()
        for item in allfiles:
            c_path = os.path.join(path, item)
            if CollectionManager.is_collection_folder(c_path):
                # try:
                file = open(os.path.join(c_path, item + ".json"))
                raw = json.load(file)
                persistence = raw['persistence']
                self.author = raw['author']
                self.title = raw['name']
                self.description = raw['description']
                self.persistence = persistence['storage']
                schemas = raw['schemas']
                for id_ in schemas:
                    storage = pers_man.get_storage(item, id_,
                                                  persistence['storage'],
                                                  c_path
                                                  )
                    collection = Collection(
                        id_,
                        Schema(schemas[id_]),
                        storage)
                    collections[id_] = collection
                #TODO load more than one
                return collections
                # except Exception:
                #     pass

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

    def getConfig(self):
        return self._config

    @staticmethod
    def is_collection_folder(item):
        return os.path.isdir(item)

    @staticmethod
    def get_instance():
        global _collectionManagerInstance
        if _collectionManagerInstance is None:
            _collectionManagerInstance = CollectionManager()
        return _collectionManagerInstance
