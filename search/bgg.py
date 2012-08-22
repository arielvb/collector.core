#!/usr/bin/env python

from engine.provider import UrlProvider, FileProvider
# Import BeautifulSoup4
from bs4 import BeautifulSoup

# BeautifulSoup4 documentation
# http://www.crummy.com/software/BeautifulSoup/bs4/doc/


BGG_BASE_URL = 'http://boardgamegeek.com/'
BGG_SEARCH_QUERY = 'http://boardgamegeek.com/geeksearch.php?action=search&objecttype=boardgame&q=%s&B1=Go'
BGG_SEARCH_SELECTOR = ".collection_objectname"


def bgg_search_filter(html):
    soup = BeautifulSoup(html)
    results = soup.select(BGG_SEARCH_SELECTOR)
    return bgg_search_sanitizer(results)


def bgg_search_sanitizer(htmlList):
    """ BeautifulSoup specific: getText """
    output = []
    for html in htmlList:
        output.append([
                html.get_text().replace("\n", ''),
                html.find('a').get('href')
            ])
    return output


def bgg_search_provider():
    return UrlProvider(BGG_SEARCH_QUERY)


def bgg_attr_provider(path):
    return UrlProvider(BGG_BASE_URL + path)


def bgg_attr_filter(html):
    soup = BeautifulSoup(html)
    results = {}
    results['title'] = soup.select('.geekitem_title a span')[0].getText()
    taula = soup.select('.geekitem_infotable')[0]
    rows = taula.findAll('tr')
    results['designer'] = rows[0].findAll('td')[1].getText().strip().replace("\n\n", '').split("\n")
    results['artist'] = rows[1].findAll('td')[1].getText().strip().replace("\n\n", '').split("\n")
    results['publisher'] = rows[2].findAll('td')[1].getText().strip().replace("\n\n", '').split("\n")
    if results['publisher'][-1] == u'Show More \xbb':
        results['publisher'].pop()
    return results


def mock_bgg_search_provider():
    return FileProvider("test/geeksearch.php.html")


def search(name, engine, post):
    """Search..."""
    html = engine().get(name)
    return post(html)


def attr(path, engine, post):
    html = engine(path).get('')
    return post(html)

if __name__ == "__main__":
    query = raw_input("Game board name: ")
    results = search(query, bgg_search_provider, bgg_search_filter)
    print "Search results: ",
    print results
    fields = attr(results[0][1], bgg_attr_provider, bgg_attr_filter)
    print fields
