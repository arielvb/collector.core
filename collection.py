# -*- coding: utf-8 -*-
from persistence import PersistenceManager
from schema import Schema
from config import Config
from tests import mocks
#from schema import SchemaManager

counter = 0


class Collection(object):

    def __init__(self, collectionName, schema, persistence):
        super(Collection, self).__init__()
        self.name = collectionName
        self.schema = schema
        self.db = persistence

    def getName(self):
        return self.schema.name

    def getLast10(self):
        """ Finds last items created at the collection."""
        # TODO 10 must be a config parameter, and the function getLastInserted(self, limit)
        return self.db.getLast(10)

    def get(self, id):
        return self.db.get(id)

    def getAll(self, startAt=0, limit=0):
        """ Finds all the items, optinally results could be called
            using startAt and limit, useful for pagination.
        """
        # TODO validate startAt and limit are integers
        return self.db.getAll(startAt, limit)

    def query(self, term):
        return self.db.search(term)

    def save(self, obj):
        return self.db.save(obj)

    def getConfig(self):
        # TODO refractor to collector
        return self._config

    def loadReferences(self, item):
        #TODO this code needs use the Field Abstract Class
        #TODO group reference values for a faster load
        if 'refLoaded' in item:
            return

        fields = self.schema.fields
        for fieldId in fields:
            field = fields[fieldId]
            if field['class'] == 'ref':
                config = field['params']['ref'].split('.')
                # TODO how to control if the references of the item aren't yet loaded
                if len(config) == 2:
                    refCollection = CollectionManager.getInstance().getCollection(config[0])
                    refAttr = config[1]
                    #TODO warning when ref[0] is difrent a refCollection.name, the schema was updated
                    # but not the db
                    if 'multiple' not in field:
                        ref = item[fieldId].split(':')
                        refItem = refCollection.get(ref[1])
                        item[fieldId] = refItem[refAttr]
                    else:
                        _list = item[fieldId]
                        for i in range(0, len(_list)):
                            ref = _list[i].split(':')
                            refItem = refCollection.get(ref[1])
                            _list[i] = refItem[refAttr]
        item['refLoaded'] = True


class CollectionManager():

    collections = {}

    def __init__(self):
        global counter
        counter += 1
        if counter > 1:
            raise Exception('Called more than once')
        self._config = Config()
        # TODO autoload collections
        schemas = mocks.collections['boardgames']['schemas']
        conf_pers = mocks.collections['boardgames']['persistence']
        persitence = PersistenceManager.getInstance().getStorage('boardgames', conf_pers['storage'], conf_pers['parameters'])
        self.collections['boardgames'] = Collection('boardgames',
            Schema(schemas['boardgames']),
            persitence
            )
        persistence = PersistenceManager.getInstance().getStorage('people', conf_pers['storage'], conf_pers['parameters'])
        self.collections['people'] = Collection('people',
                Schema(schemas['people']), persistence)

    def getCollection(self, collectionName):
        return self.collections[collectionName]

    def getConfig(self):
        return self._config

    @staticmethod
    def getInstance():
        global collectionManagerInstance
        return collectionManagerInstance

collectionManagerInstance = CollectionManager()
