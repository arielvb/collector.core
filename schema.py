# -*- coding: utf-8 -*-
from tests import mocks


class Schema(object):
    """
        Schema class
    """

    def __init__(self, dictConfig=None):
        super(Schema, self).__init__()
        self.name = None
        self.fields = {}
        self.order = []
        if dictConfig:
            self.loadFromDict(dictConfig)

    def loadFromDict(self, config):
        """Loads schema from a dict"""
        self.name = config['name']
        fields = config['fields']
        self.fields = fields
        # for field in fields:
        #     if Field.validate(fields[field]):
        #         self.fields[field] = fields[field]
        #     else:
        #         raise Exception('Field ' + field + ' not valid')
        if 'order' in config:
            self.order = []
            for item in config['order']:
                if item in self.fields:
                    self.order.append(item)
            # TODO what happens if one field key is not in the order values?
            if len(self.order) != len(fields):
                raise Exception('Order must defeine all the fields')
        else:
            self.order = fields.keys()
        if 'default' in config:
            self.default = config['default']
        else:
            self.default = self.fields[0]

    def isMultiple(self, field):
        if 'multiple' in self.fields[field]:
            return self.fields[field]['multiple']
        else:
            return False

counter = 0


class SchemaManager():

    def __init__(self):
        global counter
        counter += 1
        if counter > 1:
            raise Exception('Called more than once')
        self.schemas = {}
        # TODO the schemas must be provieded by a SchemaConfig
        self.schemas['boardgames'] = Schema(mocks.schemas['boardgames'])
        self.schemas['people'] = Schema(mocks.schemas['people'])

    def get(self, name):
        #TODO implement
        if name in self.schemas:
            return self.schemas[name]
        else:
            raise Exception('Schema not found')

    def update(self, schema):
        #TODO
        raise Exception("Not implemented")

    def create(self, schema):
        #TODO
        raise Exception("Not implemented")

    @staticmethod
    def getInstance():
        global schemaManagerInstance
        return schemaManagerInstance

schemaManagerInstance = SchemaManager()


if __name__ == '__main__':
    Schema().loadFromDict(mocks.schemas['boardgames'])
