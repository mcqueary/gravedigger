import os
import re
import sqlite3
from dataclasses import asdict, dataclass
from typing import cast
from urllib.parse import parse_qsl, urlparse
from urllib.request import Request, urlopen

from bs4 import BeautifulSoup, ResultSet, Tag

SENTINEL = cast(None, object())  # have a sentinel that pretends to be 'None'


class MemorialException(Exception):
    pass


class MemorialMergedException(MemorialException):
    pass


class MemorialRemovedException(MemorialException):
    pass


class NotFound(MemorialException):
    pass


class Driver(object):
    soup: BeautifulSoup = None

    @staticmethod
    def get(findagrave_url: str):
        req = Request(findagrave_url, headers={"User-Agent": "Mozilla/5.0"})
        with urlopen(req) as response:
            return BeautifulSoup(response.read(), "lxml")


@dataclass
class Memorial:
    """Class for keeping track of a Find A Grave memorial."""

    _id: int
    findagrave_url: str
    name: str
    maiden_name: str
    original_name: str  # for "famous" people
    birth: str
    birth_place: str
    death: str
    death_place: str
    memorial_type: str
    burial_place: str
    cemetery_id: int
    plot: str
    coords: str
    more_info: bool
    # behavior args
    get: bool
    scrape: bool
    soup = BeautifulSoup

    CANONICAL_URL_FORMAT = "https://www.findagrave.com/memorial/{}"

    # TODO: Use this information
    COLUMNS = [
        "_id",
        "url",
        "name",
        "maiden_name",
        "original_name" "birth",
        "birth_place",
        "death",
        "death_place",
        "memorial_type",
        "burial_place",
        "cemetery_id",
        "plot",
        "coords",
        "more_info",
    ]

    def __init__(self, findagrave_url: str = None, **kwargs):
        super().__init__()
        # data args
        self._id = kwargs.get("_id", None)
        self.findagrave_url = findagrave_url
        self.name = kwargs.get("name", None)
        self.maiden_name = kwargs.get("maiden_name", None)
        self.original_name = kwargs.get("original_name", None)
        self.birth = kwargs.get("birth", None)
        self.birth_place = kwargs.get("birth_place", None)
        self.death = kwargs.get("death", None)
        self.death_place = kwargs.get("death_place", None)
        self.memorial_type = kwargs.get("memorial_type", None)
        self.burial_place = kwargs.get("burial_place", None)
        self.cemetery_id = kwargs.get("cemetery_id", None)
        self.plot = kwargs.get("plot", None)
        self.coords = kwargs.get("coords", None)
        self.more_info = kwargs.get("more_info", False)
        # behavior args
        self.get = kwargs.get("get", True)
        self.scrape = kwargs.get("scrape", True)

        self.soup = None

        if self.get:
            self.soup = Driver().get(self.findagrave_url)

        if self.scrape:
            self.scrape_page()

    def __eq__(self, other):
        if self.__class__ != other.__class__:
            return False
        return self.__dict__ == other.__dict__

    @classmethod
    def from_dict(cls, d):
        return cls(**d, get=False, scrape=False)

    def to_dict(self):
        d = asdict(self)
        d.pop("get")
        d.pop("scrape")
        return d

    def check_merged(self):
        merged = False
        merged_url = None
        popup = self.soup.find("div", class_="cover-page")
        if popup:
            msg = popup.find("h2").get_text().strip()
            if msg:
                if msg == "Memorial has been merged":
                    merged = True
                    for p in popup.find_all("p"):
                        anchor = p.find("a")
                        if anchor:
                            merged_url = p.find("a").get("href")
        return merged, merged_url

    def get_canonical_url(self):
        self.url = self.soup.find("link", rel=re.compile("canonical"))["href"]

    def get_name(self, bio):
        name = bio.find("h1", id="bio-name")
        if name:
            maiden = name.find("i")
            if maiden:
                self.maiden_name = maiden.get_text()
            name = name.get_text()
            if maiden:
                name = name.replace(f" {self.maiden_name} ", " ")
            name = name.replace("Famous memorial", "")
            name = name.replace("VVeteran", "")
            name = name.strip()
            self.name = name

    def get_birth_info(self, tag: Tag):
        if tag is not None:
            birth_info = tag.find_next("dd")
            self.birth = birth_info.find("time", itemprop="birthDate").get_text()
            birth_place = birth_info.find("div", itemprop="birthPlace")
            if birth_place is not None:
                self.birth_place = birth_place.get_text()

    def get_death_info(self, tag: Tag):
        if tag is not None:
            death_info = tag.find_next("dd")
            self.death = (
                death_info.find("span", itemprop="deathDate")
                .get_text()
                .split("(")[0]
                .strip()
            )
            death_place = death_info.find("div", itemprop="deathPlace")
            if death_place is not None:
                self.death_place = death_place.get_text()

    def get_burial_info(self, tag: Tag):
        self.memorial_type = tag.get_text().replace("Read More", "")
        dd = tag.find_next("dd")

        place = ""

        cemetery: Tag = dd.find("div", itemtype="https://schema.org/Cemetery")
        if cemetery is None:
            if dd.find("span", id="otherPlace") is not None:
                self.burial_place = dd.find("span", id="otherPlace").get_text().strip()
        else:
            self.get_cemetery_id(cemetery)
            cemetery_name = cemetery.find("span", itemprop="name")
            if cemetery_name is not None:
                cemetery_name = cemetery_name.get_text()
                place += f"{cemetery_name}, "

            cemetery_location = dd.find("span", itemprop="address")
            if cemetery_location is not None:
                tag = cemetery.find_next("span", id="cemeteryCityName")
                if tag is not None:
                    cem_city = tag.get_text()
                    place += f"{cem_city}, "
                tag = cemetery.find_next("span", id="cemeteryCountyName")
                if tag is not None:
                    cem_county = tag.get_text()
                    place += f"{cem_county}, "
                tag = cemetery.find_next("span", id="cemeteryStateName")
                if tag is not None:
                    cem_state = tag.get_text()
                    place += f"{cem_state}, "
                tag = cemetery.find_next("span", id="cemeteryCountryName")
                if tag is not None:
                    cem_country = tag.get_text()
                    place += cem_country
                self.burial_place = place

        self.get_coords(dd)

    def get_cemetery_id(self, cem: Tag):
        cemetery_id = None
        if cem is not None:
            href = cem.find("a")["href"]
            cemetery_id = int(re.match(".*/([0-9]+)/.*$", href).group(1))
        self.cemetery_id = int(cemetery_id)

    def get_plot_info(self, tag: Tag):
        if tag is not None:
            self.plot = tag.find_next("dd").find("span", "plotValueLabel").get_text()

    def get_coords(self, tag: Tag):
        """Returns Google Map coordinates, if any, as a string 'nn.nnnnnnn,nn.nnnnnn'"""
        latlon = None
        span = tag.find("span", itemtype=re.compile("https://schema.org/Map"))
        if span is not None:
            anchor = span.find("a")
            href = anchor["href"]
            # just for fun
            query = urlparse(href).query
            query_args = parse_qsl(query)
            name, latlon = query_args[0]
        self.coords = latlon

    def get_more_info(self, bio: BeautifulSoup):
        self.more_info = False

    def get_bio(self):
        divs: list[BeautifulSoup] = self.soup.find_all("div")
        for div in divs:
            if div.find("h1", id="bio-name"):
                return div

    def scrape_page(self):
        merged, new_url = self.check_merged()
        if merged:
            msg = "{url} has been merged into {newurl}".format(
                url=self.findagrave_url, newurl=new_url
            )
            raise MemorialMergedException(msg)

        self.get_canonical_url()
        self._id = int(re.match(".*/([0-9]+)/.*$", self.url).group(1))
        # Get biographical info
        bio = self.get_bio()
        self.get_name(bio)
        dt_list: ResultSet = bio.find("dl").find_all("dt")
        for dt in dt_list:
            if dt.find("span", id="birthLabel") is not None:
                self.get_birth_info(dt)
            elif dt.find("span", id="deathLabel") is not None:
                self.get_death_info(dt)
            elif dt.find("span", id="cemeteryLabel") is not None:
                self.get_burial_info(dt)

        self.get_more_info(bio)

    @classmethod
    def create_table(cls, database_name="graves.db"):
        conn = sqlite3.connect(database_name)
        conn.execute(
            """CREATE TABLE IF NOT EXISTS graves
            (
                _id INTEGER PRIMARY KEY,
                findagrave_url TEXT,
                name TEXT,
                maiden_name TEXT,
                birth TEXT,
                birth_place TEXT,
                death TEXT,
                death_place TEXT,
                memorial_type TEXT,
                cemetery_id INTEGER,
                burial_place TEXT,
                plot TEXT,
                coords TEXT,
                more_info BOOL
            )"""
        )
        conn.close()

    def save(self) -> "Memorial":
        with sqlite3.connect(os.getenv("DATABASE_NAME", "graves.db")) as con:
            con.cursor().execute(
                "INSERT OR REPLACE INTO graves VALUES ("
                ":_id, "
                ":findagrave_url, "
                ":name, "
                ":maiden_name, "
                ":birth, "
                ":birth_place, "
                ":death, "
                ":death_place, "
                ":memorial_type, "
                ":cemetery_id, "
                ":burial_place, "
                ":plot, "
                ":coords, "
                ":more_info"
                ")",
                self.__dict__,
            )
            con.commit()

        return self

    @classmethod
    def get_by_id(cls, grave_id: int):
        con = sqlite3.connect(os.getenv("DATABASE_NAME", "graves.db"))
        con.row_factory = sqlite3.Row

        cur = con.cursor()
        cur.execute("SELECT * FROM graves WHERE _id=?", (grave_id,))

        record = cur.fetchone()

        if record is None:
            raise NotFound

        memorial = Memorial(
            **record, get=False, scrape=False
        )  # Row can be unpacked as dict

        con.close()

        return memorial
