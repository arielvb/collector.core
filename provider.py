import urllib2
import urllib


class Provider():

    results = None

    def get(self, name):
        if self.results is None:
            self.results = self._query_engine(name)
        return self.results


class UrlProvider(Provider):

    query = None

    def __init__(self, query):
        self.query = query

    def _query_engine(self, param):
        query = self.query
        if (param):
            param = urllib.quote_plus(param)
            query = query % param
        return urllib2.urlopen(query).read()


class FileProvider(Provider):

    def __init__(self, filename):
        self.filename = filename

    def _query_engine(self, params):
        return open(self.filename).read()
