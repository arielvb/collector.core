"""
Providers
---------
Each provider loads html content from diferent sources: urllib, open
"""
import urllib2
import urllib
from abc import ABCMeta, abstractmethod, abstractproperty

TIMEOUT = 60


class Provider(object):
    """Base class for all the providers"""

    __metaclass__ = ABCMeta

    def __init__(self):
        super(Provider, self).__init__()
        self.results = None

    def get(self, params):
        """Loads the content identified whith *params*"""
        if self.results is None:
            self.results = self._query_engine(params)
        return self.results

    @staticmethod
    @abstractproperty
    def get_name():
        """Returns the name of the provider"""

    @abstractmethod
    def _query_engine(self, params):
        """Returns the html content for the given params"""


class UrlProvider(Provider):
    """Provider using urllib2, loads content by url"""

    def __init__(self, query):
        super(UrlProvider, self).__init__()
        self.query = query

    @staticmethod
    def get_name():
        return "URI provider"

    def _query_engine(self, param):
        query = self.query
        if (param):
            param = urllib.quote_plus(param)
            query = query % param
        return urllib2.urlopen(query, timeout=TIMEOUT).read()


class FileProvider(Provider):
    """ Provider using the python builin function open"""

    def __init__(self, filename):
        super(FileProvider, self).__init__()
        self.filename = filename

    def _query_engine(self, params):
        return open(self.filename).read()
