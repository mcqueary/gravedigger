import re
import sqlite3
from dataclasses import asdict, dataclass
from urllib.request import Request, urlopen

from bs4 import BeautifulSoup


class CemeteryException(Exception):
    pass


class Driver(object):
    soup: BeautifulSoup = None

    @staticmethod
    def get(findagrave_url: str):
        req = Request(findagrave_url, headers={"User-Agent": "Mozilla/5.0"})
        with urlopen(req) as response:
            return BeautifulSoup(response.read(), "lxml")


@dataclass
class Cemetery:
    """Class for keeping track of a Find A Grave cemetery."""

    # data
    _id: int = None
    findagrave_url: str = None
    name: str = None
    location: str = None
    coords: str = None
    # Behavior flags
    get: bool = True
    scrape: bool = True

    def __init__(self, findagrave_url: str = None, **kwargs):
        super().__init__()
        self.findagrave_url = findagrave_url
        self._id = kwargs.get("_id", None)
        self.name = kwargs.get("name", None)
        self.location = kwargs.get("location", None)
        self.coords = kwargs.get("coords", None)
        # behavior args
        self.get = kwargs.get("get", True)
        self.scrape = kwargs.get("scrape", True)

        self.soup: BeautifulSoup = None

        if self.get:
            self.soup = Driver().get(findagrave_url)

        if self.scrape:
            self.scrape_page()

    def scrape_page(self):
        self.get_canonical_link()
        self._id = int(
            re.match(
                "https://www.findagrave.com/cemetery/([0-9]+)/.*", self.findagrave_url
            ).group(1)
        )
        self.get_name()
        self.get_location()
        self.get_coords()

    def __eq__(self, other):
        if self.__class__ != other.__class__:
            return False
        return self.__dict__ == other.__dict__

    @classmethod
    def from_dict(cls, d):
        return Cemetery(**d, get=False, scrape=False)

    def to_dict(self):
        return asdict(self)

    @classmethod
    def create_table(cls, database_name="graves.db"):
        conn = sqlite3.connect(database_name)
        conn.execute(
            """CREATE TABLE IF NOT EXISTS cemeteries
            (_id INTEGER PRIMARY KEY, url TEXT,
            name TEXT, location TEXT, coords TEXT, more_info BOOL)"""
        )
        conn.close()

    def get_canonical_link(self):
        link = self.soup.find("link", rel=re.compile("canonical"))["href"]
        if link:
            self.findagrave_url = link

    def get_name(self):
        result = self.soup.find("h1", itemprop="name")
        if result:
            self.name = result.get_text().strip()

    def get_location(self):
        location = None
        result = self.soup.find("span", itemprop="addressLocality")
        if result is not None:
            locality = result.get_text().strip()
            result = self.soup.find("span", itemprop="addressRegion")
            if result is not None:
                region = result.get_text().strip()
                result = self.soup.find("span", itemprop="addressCountry")
                if result is not None:
                    country = result.get_text().strip()
                    location = locality + ", " + region + ", " + country
        self.location = location

    def get_coords(self):
        lat = None
        lon = None
        result = self.soup.find("span", title="Latitude:")
        if result:
            lat = result.get_text()
        result = self.soup.find("span", title="Longitude:")
        if result:
            lon = result.get_text()
        if lat and lon:
            self.coords = lat + "," + lon
