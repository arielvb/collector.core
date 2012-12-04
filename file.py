# -*- coding: utf-8 -*-
"""
File (Fitxa)
------------
Each element of a collection is a file.

..warning:
    This module name has the same name as the builtin function *file*.
"""
import copy


class File(object):
    """Marker for each item that must be a File. Be carefull this class isn't
     abstract (abc) to avoid errors with sqlalchemy."""

    def get(self, field, load_reference=True):
        """Returns the value for the requested field, if the field is a
         reference returns the referenced value by default, this can be
         modified with the *load_reference* parameter.
        """

    def update(self, fields):
        """Updates the file with the new values"""

    def copy(self):
        """Returns a copy of the field as a python dictionary"""

    def __getitem__(self, key):
        return getattr(self, key, '')

    def __contains__(self, key):
        return hasattr(self, key)

    def __iter__(self):
        return iter(self.__dict__)


class FileDict(File):
    """File is a group of fields"""

    def __init__(self, fields):
        super(FileDict, self).__init__()
        for field in fields.items():
            setattr(self, field[0], field[1])

    def __setitem__(self, key, value):
        setattr(self, key, value)

    def update(self, fields):
        for field in fields.items():
            setattr(self, field[0], field[1])

    def get(self, field, load_reference=True):
        return self[field]

    def copy(self):
        return copy.deepcopy(self.__dict__.copy())
