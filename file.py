# -*- coding: utf-8 -*-
"""
File (Fitxa)
------------
The basic element of a collection.

..warning:
    This module name has the same name as the builtin function *file*.
"""

from fields import FieldManager
from schema import Schema


class File(object):
    """The basic element of a collection"""
    def __init__(self, schema, fields=None):
        super(File, self).__init__()
        if (schema is None or not isinstance(schema, Schema)):
            raise Exception("Bad Arguments")
        # if isinstance(fields, dict):
        #     if len(fields) > 0:
        #         for field in fields:
        #             if not isinstance(fields[0], Field):
        #                 raise Exception("Bad Arguments")
        #     # else:
        #     #     raise Exception("Bad Arguments")
        #     self.fields = fields
        if isinstance(fields, dict):
            self.fields = self._load_fields_from_dict(fields, schema)
        elif fields is None:
            self.fields = {}
        else:
            raise Exception("Bad Arguments")

        # TODO refractor _load_fields_from_dict and the code above to the
        #  class Schema
        # Create empty fields
        man = FieldManager.get_instance()
        for field in schema.fields:
            if not field in self.fields:
                self.fields[field] = man.get(schema.fields[field])

    @classmethod
    def _load_fields_from_dict(cls, dictvalues, schema):
        """ Trasnlates the *dictvalues* of basic types using the schema of
        the *collection* into *Field* objects"""
        fields = {}
        man = FieldManager.get_instance()
        for field in schema.fields:
            fields[field] = man.get(schema.fields[field])
            if field in dictvalues:
                fields[field].set_value(dictvalues[field])
        return fields
