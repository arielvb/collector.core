# -*- coding: utf-8 -*-


class Schema(object):
    """
        Schema class
    """

    def __init__(self, configDict=None):
        super(Schema, self).__init__()
        self.name = None
        self.fields = {}
        self.order = []
        # TODO icona e imatge per defecte
        self.ico = None
        self.image = None
        if isinstance(configDict, dict):
            self._raw = configDict
            self.loadFromDict(configDict)

    def loadFromDict(self, config):
        """Loads schema from a python dictionary"""
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
        if 'ico' in config:
            self.ico = config['ico']
        if 'image' in config:
            self.image = config['image']

    def isMultivalue(self, field):
        """ Returns True if the field is multivalue """
        if 'multiple' in self.fields[field]:
            return self.fields[field]['multiple']
        else:
            return False

counter = 0


# class SchemaManager():

#     def __init__(self):
#         global counter
#         counter += 1
#         if counter > 1:
#             raise Exception('Called more than once')
#         self.schemas = {}
#         # TODO the schemas must be provieded by a SchemaConfig
#         schemas = mocks.collections['boardgames']['schemas']
#         self.schemas['boardgames'] = Schema(schemas['boardgames'])
#         self.schemas['people'] = Schema(schemas['people'])

#     def get(self, name):
#         #TODO implement
#         if name in self.schemas:
#             return self.schemas[name]
#         else:
#             raise Exception('Schema not found')

#     def update(self, schema):
#         #TODO
#         raise Exception("Not implemented")

#     def create(self, schema):
#         #TODO
#         raise Exception("Not implemented")

#     @staticmethod
#     def getInstance():
#         global _schemaManagerInstance
#         return _schemaManagerInstance

# _schemaManagerInstance = SchemaManager()
