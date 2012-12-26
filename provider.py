"""
Providers
---------
Each provider loads html content from diferent sources: urllib, open
"""
import urllib2
import urllib
from abc import ABCMeta, abstractmethod, abstractproperty
import logging
from cookielib import CookieJar
from StringIO import StringIO
import gzip

TIMEOUT = 120


class Provider(object):
    """Base class for all the providers"""

    __metaclass__ = ABCMeta

    def __init__(self):
        super(Provider, self).__init__()
        self.results = None

    def get(self, params):
        """Loads the content identified whith *params*,
         and caches the results"""
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

    def flush(self):
        """Flushes the cache"""
        self.results = None


class UrlProvider(Provider):
    """Provider using urllib2 and cookielib"""

    def __init__(self, query):
        super(UrlProvider, self).__init__()
        self.query = query
        self.cookie = CookieJar()
        self.opener = urllib2.build_opener(
            urllib2.HTTPCookieProcessor(self.cookie))
        self.opener.addheaders = [
            ('User-agent',
             'Mozilla/5.0 (X11; U; Linux i686; en-US;'
             ' rv:1.9.0.1) Gecko/2008071615 Fedora/3.0.1-1.fc9'
             'Firefox/3.0.1'),
            ('Accept-encoding', 'gzip, deflate')]

    @staticmethod
    def get_name():
        return "URI provider"

    def _query_engine(self, param):
        query = self.make_query(param)
        results = self.opener.open(query, timeout=TIMEOUT)
        html = None
        if results.info().get('Content-Encoding') == 'gzip':
            buf = StringIO(results.read())
            f = gzip.GzipFile(fileobj=buf)
            html = f.read()
        else:
            html = results.read()
        return html

    def make_query(self, param):
        """Creates an url from the base query and the params"""
        query = self.query
        if (param):
            param = urllib.quote_plus(param.encode('utf-8'))
            query = query % str(param)
        logging.debug("Provider: loading url %s", query)
        return query


class FileProvider(Provider):
    """ Provider using the python built-in function open"""

    def __init__(self, filename):
        super(FileProvider, self).__init__()
        self.filename = filename

    def _query_engine(self, params):
        return open(self.filename).read()
