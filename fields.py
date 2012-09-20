# -*- coding: utf-8 -*-
from collection import CollectionManager


class Field(object):

    _class = ''
    name = ''
    reference = None
    singleValue = True
    value = None

    def __init__(self, name, multiple=False, params=None):
        if multiple:
            self.singleValue = False
            self.value = []
        self.name = name
        self._params = params

    @staticmethod
    def _validate_image(field):
        return True

    @staticmethod
    def _validate_ref(field):
        error = False
        # Ref needs an atributte called ref
        if 'ref' not in field:
            error = True
        else:
            # ref must be composed as $collection.$table
            ref = field['ref'].split('.')
            if len(ref) != 2:
                error = True
            else:
                for token in ref:
                    if token == '':
                        error = True
        return not error

    def isMultivalue(self):
        return not self.singleValue

    def addValue(self, value):
        if self.isMultivalue():
            self.value.append(value)
        else:
            # TODO Custom exception
            raise Exception('Not a multivalue field')

    def setValue(self, value):
        is_list = isinstance(value, list)
        is_dict = isinstance(value, dict)
        if not self.singleValue and not is_list:
            raise Exception("Field is multivalue and the new value isn't not a list")
        # TODO how to check value is a basic type?
        elif self.singleValue and is_list or is_dict:
            raise Exception("Field is not multivalue and the value is a list")
        self.value = value

    def getValue(self):
        return self.value

    def __str__(self):
        # TODO finish and test
        value = ''
        if not self.value is None:
            value = self.value
        return self.name + ': ' + str(value)


class FieldText(Field):

    _class = 'text'


class FieldInt(Field):
    """Custom Field where the value's are int"""
    _class = 'int'

    def setValue(self, value):
        super(FieldInt, self).setValue(int(value))

    def addValue(self, values):
        int_list = []
        for item in values:
            int_list.append(int(item))
        super(FieldInt, self).setValue(int_list)
        pass


class FieldImage(Field):

    _class = 'image'

    def getPath(self):
        """ Alias for self.getValue """
        return self.value

    def getFullField(self):
        # TODO implentar obtenir el contingut de la imatge (bits)
        pass


class FieldRef(Field):

    _class = 'ref'
    full = None

    def __init__(self, name, multiple=False, params=None):
        super(Field, self).__init__(name, multiple, params)
        self._validate()
        parts = self._params['ref'].split()

        self.ref_collection = parts[0]
        self.ref_field = parts[1]

    def _validate(self):
        if not 'ref' in self.params:
            raise Exception('ref param expected')
        ref = self._params['ref'].split('.')
        if len(ref) != 2:
            raise Exception('ref param must be [collection].[name]')

    def getFullField(self):
        """ Obtains the full object of the referenced value"""
        # TODO must call to persitence object?
        if self.full is None:
            parts = self.value.split(':')

            if self._validateParts(parts):
                man = CollectionManager.get_instance()
                col = man.getCollection(parts[0])
                self.full = col.get(parts[1])
                self.full
                return self.full
            else:
                raise Exception('Malformed reference value')

    def getReferencedValue(self):
        """ Obtains the referenced value"""
        full = self.getFullField()
        return full[self.ref_field]

    def _validateParts(parts):
        return len(parts) == 2


class FieldClassNotFound(Exception):
    """Raises when a non registered class is requested using *FieldManager*"""

_fieldManagerInstance = None


class FieldManager():

    def __init__(self):
        global _fieldManagerInstance
        if _fieldManagerInstance is not None:
            raise Exception("Called more that once")
        _fieldManagerInstance = self
        self.fields = {'text': FieldText, 'int': FieldInt}

    @staticmethod
    def get_instance():
        global _fieldManagerInstance
        if _fieldManagerInstance is None:
            _fieldManagerInstance = FieldManager()
        return _fieldManagerInstance

    def get(self, config):
        if config['class'] in self.fields:
            field_class = self.fields[config['class']]
        else:
            # TODO custom exception
            raise FieldClassNotFound('Field class ' + config['class'] +
                ' not found.')
        multivalue = False
        params = None
        if 'multiple' in config:
            multivalue = config['multiple']
        if 'params' in config:
            params = config['params']
        return field_class(config['name'], multivalue, params)
