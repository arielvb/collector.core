# -*- coding: utf-8 -*-
from fields import FieldManager


class Schema(object):
    """
        Schema class
    """

    def __init__(self, collection, id_, params=None):
        super(Schema, self).__init__()
        self.id = id_
        self.collection = collection
        self.name = None
        self.fields = {}
        self.file = {}
        self.order = []
        # TODO icona e imatge per defecte
        self.ico = None
        self.image = None
        self._raw = params
        self.default = None
        if isinstance(params, dict):
            self.loadFromDict(params)

    def add_field(self, field):
        self.file[field.get_id()] = field
        if self.default is None:
            self.default = field.get_id()

    def get_field(self, name):
        return self.file[name]

    def get_fields(self):
        return self.fields

    def loadFromDict(self, config):
        """Loads schema values from a python dictionary"""
        self.name = config['name']
        fields = config['fields']
        self.fields = fields
        self.file = {}
        manager = FieldManager.get_instance()
        for field in fields.items():
            self.file[field[0]] = manager.get(field[1])

        if 'order' in config:
            self.order = []
            for item in config['order']:
                if item in self.fields:
                    self.order.append(item)
            # TODO what happens if one field key is not in the order values?
            if len(self.order) != len(fields):
                raise Exception('Order must define all the fields')
        else:
            self.order = fields.keys()
        if 'default' in config:
            self.default = config['default']
        else:
            self.default = self.order[0]
        if 'ico' in config:
            self.ico = config['ico']
        if 'image' in config:
            self.image = config['image']

    def isMultivalue(self, field):
        if 'multiple' in self.fields[field]:
            return self.fields[field]['multiple']
        else:
            return False
