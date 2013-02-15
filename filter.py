# -*- coding: utf-8 -*-
"""Filters"""
from abc import ABCMeta, abstractmethod


class Filter(object):
    """Base class for filters"""

    __metaclass__ = ABCMeta

    @staticmethod
    @abstractmethod
    def get_id():
        """Returns the filter identifier"""

    @staticmethod
    @abstractmethod
    def get_name():
        """Returns the human friendly name of the filter"""

    @staticmethod
    @abstractmethod
    def get_description():
        """Returns the description of the filter"""

    @staticmethod
    @abstractmethod
    def get_filter(params):
        """Returns the filter query"""
        # TODO maybe is better **kargs


class FilterUnion(Filter):
    """Base class for filter union"""


class FilterRegistry(object):
    """A registry for the avaible filters"""

    filters = {}
    unions = {}

    def register(self, filter_):
        """Regiters a new filter"""
        if issubclass(filter_, FilterUnion):
            self.unions[filter_.get_id()] = filter_
        else:
            self.filters[filter_.get_id()] = filter_

    def get_filter(self, id_):
        """Returns the requested filter"""
        return self.filters[id_]

    def get_union(self, id_):
        """Returns a filter union"""
        return self.unions[id_]
