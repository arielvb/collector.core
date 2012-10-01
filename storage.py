# -*- coding: utf-8 -*-
""""Diferent file storage methods"""
from abc import ABCMeta, abstractmethod, abstractproperty
import pickle
import json
import os
import logging


class FileStorage(object):
    """The base class"""

    __metaclass__ = ABCMeta

    MODE = 0700

    def __init__(self, path, name, readonly=False):
        """Creates a new storage file, it could be read-only, if that is the
         case the save method will do nothing."""
        super(FileStorage, self).__init__()
        self.readonly = readonly
        self.path = path
        self.name = name
        self.file = os.path.join(self.path, name + "." +
                                 self.file_extension())

    def load(self):
        """Returns the content of the storage"""
        contents = None
        self.create_path()
        if os.path.exists(os.path.join(self.path, self.file)):
            contents = self.do_load()
        return contents

    def create_path(self):
        """Checks an creates the path of the storage"""
        if not os.path.exists(self.path) and not self.readonly:
            os.makedirs(self.path, FileStorage.MODE)
            logging.info("STORAGE created paths %s", self.file)

    def save(self, obj):
        """Save the object overriding the current value"""
        if not self.readonly:
            self.create_path()
            self.do_save(obj)

    @abstractproperty
    def file_extension(self):
        """Returns the file extension"""

    @abstractmethod
    def do_save(self, obj):
        """This function is called when the content must be saved"""

    @abstractmethod
    def do_load(self, obj):
        """This function is called when the content must be saved"""


class JSONStorage(FileStorage):
    """Implementation of a storage using JSON"""

    def file_extension(self):
        return 'json'

    def do_load(self):
        file_ = open(self.file)
        content = json.load(file_)
        file_.close()
        return content

    def do_save(self, obj):
        file_ = open(self.file, 'wb')
        json.dump(obj, file_, indent=4)
        file_.close()


class PickleStorage(FileStorage):
    """Implementation of a storage using Pickle"""

    def file_extension(self):
        return 'p'

    def do_load(self):
        file_ = open(self.file)
        content = pickle.load(file_)
        file_.close()
        return content

    def do_save(self, obj):
        file_ = open(self.file, 'wb')
        pickle.dump(obj, file_,)
        file_.close()
