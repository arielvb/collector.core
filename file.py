# -*- coding: utf-8 -*-
"""
File (Fitxa)
------------
Each element of a collection is a file.

..warning:
    This module name has the same name as the builtin function *file*.
"""


class FileInterface(object):
    """Marker for each item that must be a File"""


class File(FileInterface):
    """File is a group of fields"""

    def __init__(self, fields):
        for field in fields.items():
            setattr(self, field[0], field[1])

    def __setitem__(self, key, value):
        setattr(self, key, value)

    def __getitem__(self, key):
        return getattr(self, key, '')

    def __iter__(self):
        return iter(self.__dict__)

    def update(self, fields):
        for field in fields.items():
            setattr(self, field[0], field[1])


class FileAlchemy(FileInterface):
    """File is a group of fields"""

    def __init__(self, fields):
        for field in fields.items():
            setattr(self, field[0], str(field[1]))

    def __setitem__(self, key, value):
        setattr(self, key, value)

    def __getitem__(self, key):
        return getattr(self, key, '')

    def __iter__(self):
        return iter(self.__dict__)

    def update(self, fields):
        for field in fields.items():
            setattr(self, field[0], field[1])
