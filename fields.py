# -*- coding: utf-8 -*-
"""
Fields
------

The fields define different types of data.
"""
import logging
from abc import ABCMeta, abstractproperty, abstractmethod
from urlparse import urlparse
import os
from config import Config


class Field(object):
    """Base class for all the fields"""
    __metaclass__ = ABCMeta

    class_ = ''
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
        """Returns the identifier of the field, this identifier is unique
            at file level. But not at collection level"""
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
        """Returns the pretty name of the class_ of field"""

    def empty(self):
        """Checks if the field doesn't have any value"""
        if self.is_multivalue():
            return self.value is not None and self.value != []
        else:
            return self.value is not None or self.value is not ''


class FieldText(Field):
    """A field whit type text"""
    class_ = 'text'

    def get_pretty_type(self):
        return "Text"


class FieldWithCast(Field):

    def set_value(self, value):
        """Overrides the default method to cast the values to int"""
        if value is None or value == '':
            return
        if isinstance(value, list):
            value = [self.cast(val) for val in value]
        else:
            value = self.cast(value)
        super(FieldWithCast, self).set_value(value)

    def add_value(self, values):
        """Checks if a value is int before add it"""
        int_list = [self.cast(value) for value in values]
        super(FieldWithCast, self).set_value(int_list)

    @abstractmethod
    def cast(self, value):
        """Cast method to convert the input value"""


class FieldInt(FieldWithCast):
    """Custom field where the only accepted value are int"""
    class_ = 'int'

    def cast(self, value):
        return int(value)

    def get_pretty_type(self):
        return "Integer"


class FieldFloat(FieldWithCast):
    """Custom field where the only accepted value are float"""
    class_ = 'float'

    def get_pretty_type(self):
        return "Float"

    def cast(self, value):
        return float(value)


class FieldImage(Field):
    """Field that represents an image"""

    class_ = 'image'

    def get_value(self):
        image = self.value
        if not image is None:
            uri = urlparse(self.value)
            if uri.scheme == 'collector' and uri.netloc == 'collections':
                image = os.path.join(Config.get_instance().get_home(),
                                     uri.netloc,
                                     os.path.normpath(uri.path[1:]))
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

    class_ = 'ref'

    def __init__(self, name, multiple=False, params=None, value=None):
        super(FieldRef, self).__init__(name, multiple, params, value)
        self._validate()
        parts = self._params['ref'].split('.')
        self.ref_collection = parts[0]
        self.ref_field = parts[1]

    def _validate(self):
        """Checks that the reference is valid"""
        if not 'ref' in self._params:
            raise Exception('ref param expected')
        ref = self._params['ref'].split('.')
        if len(ref) != 2:
            raise Exception('ref param must be [collection].[name]')

    def get_fullfield(self, collections):
        """ Obtains the full object of the referenced value"""
        # TODO this must call to persistence.load_reference
        #  this new method must be a derived of persistence.load_references
        #  and return the value of the reference
        raise Exception("not implemented")

    def get_referenced_value(self, collections):
        """ Obtains the referenced value"""
        full = self.get_fullfield(collections)
        return full[self.ref_field]

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
                       'int': FieldInt, 'ref': FieldRef, 'float': FieldFloat}

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
            fieldclass_ = self.fields[config['class']]
        else:
            logging.error(
                ("FieldManager: loading field '%s' with wrong"
                    "class '%s'."),
                config['name'], config['class'])
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
        return fieldclass_(config['name'], multivalue, params)
