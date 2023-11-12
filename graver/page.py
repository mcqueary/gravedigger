from urllib.request import Request, urlopen

from bs4 import BeautifulSoup


class Page(object):
    _url: str = None
    _html: bytes
    _soup: BeautifulSoup = None

    def __init__(self, url):
        self._url = url

    def __eq__(self, other):
        if self.__class__ != other.__class__:
            return False
        return self.__dict__ == other.__dict__

    @property
    def url(self):
        return self._url

    # @property
    # def type(self):
    #     if self._type is None:
    #         if (
    #             re.match(
    #                 "^https://www.findagrave.com/cemetery/[0-9]+/memorial-search.*$",
    #                 self._url,
    #             )
    #             is not None
    #         ):
    #             self._type = PageType.LIST
    #         elif (
    #             re.match("^https://www.findagrave.com/memorial/[0-9]+.*$", self._url)
    #             is not None
    #         ):
    #             self._type = PageType.MEMORIAL
    #         elif (
    #             re.match("^https://www.findagrave.com/cemetery/[0-9]+.*$", self._url)
    #             is not None
    #         ):
    #             self._type = PageType.CEMETERY

    #     return self._type

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
