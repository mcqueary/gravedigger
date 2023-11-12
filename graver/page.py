from urllib.request import Request, urlopen

from bs4 import BeautifulSoup

# from graver.soup import get_canonical_link


class Page(object):
    _url: str
    _html: bytes
    _soup: BeautifulSoup

    def __init__(self, url):
        self._url = url

    def __eq__(self, other):
        if self.__class__ != other.__class__:
            return False
        return self.__dict__ == other.__dict__

    @property
    def url(self):
        return self._url

    @property
    def html(self):
        if self._html is None:
            req = Request(self._url, headers={"User-Agent": "Mozilla/5.0"})
            with urlopen(req) as response:
                self._html = response.read()
            with urlopen(req) as response:
                self._html = BeautifulSoup(response.read(), "lxml")
        return self._html

    @property
    def soup(self):
        if self._soup is None:
            if self._html is not None:
                self._soup = BeautifulSoup(self._html, "lxml")
        return self._soup

    # def scrape(cls, input_url):
    #     tree = None
    #     req = Request(input_url, headers={"User-Agent": "Mozilla/5.0"})
    #     with urlopen(req) as response:
    #         tree = BeautifulSoup(response.read(), "lxml")
    #     # url = get_canonical_link(tree)

    #     return Page(input_url)


class CemeteryPage(Page):
    pass
