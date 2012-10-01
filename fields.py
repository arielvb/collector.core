# -*- coding: utf-8 -*-
# from collection import CollectionManager
"""
Fields
------

The fields define different types of data.
"""
import logging
from abc import ABCMeta, abstractproperty


class Field(object):
    """Base class for all the fields"""
    __metaclass__ = ABCMeta

    #TODO refractor to class_ (pyqt style for overrided keyworkds)
    _class = ''
    name = ''
    reference = None
    single_value = True
    value = None

    def __init__(self, name, multiple=False, params=None, value=None):
        """Creates a new Field, if multiple it allows more that one value and
         allows use the addValue method"""
        if multiple:
            self.single_value = False
            if value is None:
                self.value = []
            else:
                self.value = value
        else:
            self.value = value

        self.name = name
        self._params = params

    def get_id(self):
        return self.name.lower().replace('/', '').replace(' ', '')

    def is_multivalue(self):
        """Is true when the field is multivalued"""
        return not self.single_value

    def add_value(self, value):
        """If the field is multivalued allows add an other value, if isn't
         multivalued raises an TypeError Exception"""
        if self.is_multivalue():
            self.value.append(value)
        else:
            # TODO Custom exception
            raise TypeError('Not a multivalued field')

    def set_value(self, value):
        """Sets the value of the field, if the field is multivalued the
         new value must be a list"""
        is_list = isinstance(value, list)
        is_dict = isinstance(value, dict)
        if not self.single_value and not is_list:
            raise ValueError("Field is multivalued and the" +
                " new value isn't not a list")
        # TODO how to check value is a basic type?
        elif self.single_value and is_list or is_dict:
            raise ValueError("Field is not multivalued and the value" +
                " is a list")
        self.value = value

    def get_value(self):
        """Returns the value of the field"""
        return self.value

    def __str__(self):
        """Represents the field as a String"""
        # TODO finish and test
        value = ''
        if not self.value is None:
            value = self.value
        return self.name + ': ' + str(value)

    @abstractproperty
    def get_pretty_type(self):
        """Returns the pretty name of the _class of field"""


class FieldText(Field):
    """A field whit type text"""
    _class = 'text'

    def get_pretty_type(self):
        return "Text"


class FieldInt(Field):
    """Custom field where the only accepted value are int"""
    _class = 'int'

    def set_value(self, value):
        """Overrides the default method to cast the values to int"""
        if isinstance(value, list):
            value = [int(val) for val in value]
        else:
            value = int(value)
        super(FieldInt, self).set_value(value)

    def add_value(self, values):
        """Checks if a value is int before add it"""
        int_list = [int(value) for value in values]
        super(FieldInt, self).set_value(int_list)

    def get_pretty_type(self):
        return "Integer"


from urlparse import urlparse
import os
from config import Config


class FieldImage(Field):
    """Field that represents an image"""

    _class = 'image'

    def get_value(self):
        image = self.value
        uri = urlparse(self.value)
        if uri.scheme == 'collector' and uri.netloc == 'collections':
            image = os.path.join(Config.get_instance().get_data_path(),
                                 uri.netloc, os.path.normpath(uri.path[1:]))
        return image

    def get_path(self):
        """ Alias for self.getValue """
        return self.value

    def get_fullfield(self):
        """Returns the raw content of the image"""
        # TODO implentar obtenir el contingut de la imatge (bits)

    def get_pretty_type(self):
        return "Image"


class FieldRef(Field):
    """Defeines a reference to another field"""

    _class = 'ref'

    def __init__(self, name, multiple=False, params=None, value=None):
        super(FieldRef, self).__init__(name, multiple, params, value)
        self._validate()
        parts = self._params['ref'].split('.')
        self.ref_collection = parts[0]
        self.ref_field = parts[1]
        self.full = None

    def _validate(self):
        """Checks that the reference is valid"""
        if not 'ref' in self._params:
            raise Exception('ref param expected')
        ref = self._params['ref'].split('.')
        if len(ref) != 2:
            raise Exception('ref param must be [collection].[name]')

    def get_fullfield(self, collections):
        """ Obtains the full object of the referenced value"""
        # TODO must call to persistence object?
        if self.full is None:
            parts = self.value.split(':')
            if len(parts) == 2:
                # man = CollectionManager.get_instance()
                # col = man.getCollection(parts[0])
                col = collections.get(parts[0])
                self.full = col.get(parts[1])
            else:
                raise Exception('Malformed reference value')
        return self.full

    def get_referenced_value(self, collections):
        """ Obtains the referenced value"""
        self.full = self.get_fullfield(collections)
        return self.full[self.ref_field]

    def get_pretty_type(self):
        return "Reference"


class FieldClassNotFound(Exception):
    """Raises when a non registered class is requested using *FieldManager*"""


class FieldManager():
    """
    FieldManager allows register and obtains fields
    """

    _instance = None

    def __init__(self):
        """Creates the instance of the FieldManager if it was not previously
         created.
         Don't call this function directly use FieldManager.get_instance()"""
        if FieldManager._instance is not None:
            raise Exception("Called more that once")
        self.fields = {'text': FieldText, 'image': FieldImage,
                       'int': FieldInt, 'ref': FieldRef}

    @staticmethod
    def get_instance():
        """Returns the instance of the FieldManager"""
        if FieldManager._instance is None:
            FieldManager._instance = FieldManager()
        return FieldManager._instance

    def get(self, config):
        """Returns the field the matched field for the requested config.
         The possible keys are:
            name        string, the name of the field (required)
            class       string, the kind of field, by default "text"
            multivalue  boolean, the field allow more than one value,
                         default=False
            params      dict, extra options to pass to the field
        """
        # Check name
        if 'name' not in config:
            logging.error("FieldManager: loading field whitout name")
            raise ValueError("Missing name key")
        # Check class
        if 'class' not in config:
            config['class'] = 'text'
            logging.info("FieldManager: loading field '%s' " +
                         "without class, using text.", config['name'])
        if config['class'] in self.fields:
            field_class = self.fields[config['class']]
        else:
            logging.error("FieldManager: loading field '%s'"
                " with wrong class '%s'.", config['name'], config['class'])
            raise FieldClassNotFound('Field class ' + config['class'] +
                ' not found.')
        # Multivalue
        multivalue = False
        if 'multiple' in config:
            multivalue = config['multiple']
        # parameters
        params = None
        if 'params' in config:
            params = config['params']
        # Load the field
        return field_class(config['name'], multivalue, params)
