# -*- coding: utf-8 -*-


class Schema(object):
    """
        Schema class
    """

    def __init__(self, params=None):
        super(Schema, self).__init__()
        self.name = None
        self.fields = {}
        self.order = []
        # TODO icona e imatge per defecte
        self.ico = None
        self.image = None
        self._raw = params
        if isinstance(params, dict):
            self.loadFromDict(params)

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
        if 'multiple' in self.fields[field]:
            return self.fields[field]['multiple']
        else:
            return False
