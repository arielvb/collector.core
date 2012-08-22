# -*- coding: utf-8 -*-

from tests import mocks
#TODO redo all the class, we need to use sqlite3, or sqlalchemy


class PersitenceManager():

    _autoid = 1

    def __init__(self, collectionName):
        self.items = collectionName == 'boardgames' and mocks.boardgames or mocks.people
        maxid = 0
        for i in self.items:
            maxid = max(maxid, i['id'])
        self._autoid = maxid + 1

    def getLast(self, count):
        result = self.items[:count]
        return result

    def get(self, _id):
        # TODO validate id is integer
        for a in self.items:
            if _id == a['id']:
                return a
        return None

    def getAll(self, startAt, limit):
        return self.items

    def save(self, item):
        #TODO !
        if 'id' in item:
            for a in self.items:
                if item['id'] == a['id']:
                    a.update(item)
        else:
            item['id'] = self._autoid
            self._autoid += 1
            self.items.append(item)

if __name__ == '__main__':
    PersitenceManager()
