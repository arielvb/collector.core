from engine.persistence import PersitenceManager
from engine.config import Config
from schema import SchemaManager

counter = 0


class CollectionManager():

    def __init__(self):
        global counter
        counter += 1
        if counter > 1:
            raise Exception('Called more than once')
        self._config = Config()

    def getPersistence(self, collectionName):
        # TODO sanitize collectionName
        return PersitenceManager(collectionName)

    def getCollection(self, collectionName):
        return Collection(collectionName)

    def getConfig(self):
        return self._config

    @staticmethod
    def getInstance():
        global collectionManagerInstance
        return collectionManagerInstance

collectionManagerInstance = CollectionManager()


class Collection():

    def __init__(self, collectionName):
        self.name = collectionName
        self.schema = SchemaManager.getInstance().get(self.name)
        self.db = CollectionManager.getInstance().getPersistence(collectionName)

    def getFullName(self):
        self.schema.getFullName()

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

    def save(self, obj):
        return self.db.save(obj)



    def getConfig(self):
        # TODO refractor to collector
        return self._config
