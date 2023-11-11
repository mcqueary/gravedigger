import os
import re
import sqlite3
from dataclasses import dataclass
from enum import Enum
from urllib.request import Request, urlopen

from bs4 import BeautifulSoup

from graver.soup import (
    get_birth_date,
    get_birth_place,
    get_burial_plot,
    get_canonical_link,
    get_death_date,
    get_death_place,
    get_id,
    get_name,
)


class PageType(Enum):
    MEMORIAL = 1
    CEMETERY = 2
    LIST = 3


class NotFound(Exception):
    pass


class Page(object):
    _url: str = None
    _type: PageType = None
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

    @property
    def type(self):
        if self._type is None:
            if (
                re.match(
                    "^https://www.findagrave.com/cemetery/[0-9]+/memorial-search.*$",
                    self._url,
                )
                is not None
            ):
                self._type = PageType.LIST
            elif (
                re.match("^https://www.findagrave.com/memorial/[0-9]+.*$", self._url)
                is not None
            ):
                self._type = PageType.MEMORIAL
            elif (
                re.match("^https://www.findagrave.com/cemetery/[0-9]+.*$", self._url)
                is not None
            ):
                self._type = PageType.CEMETERY

        return self._type

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


@dataclass
class Memorial:
    """Class for keeping track of a FindAGrave memorial."""

    _id: int
    _url: str
    _name: str
    _birth: str
    _birthplace: str
    _death: str
    _deathplace: str
    _burial: str
    _plot: str
    _more_info: bool

    @property
    def id(self):
        return self._id

    @property
    def url(self):
        return self._url

    @property
    def name(self):
        return self._name

    @property
    def birth(self):
        return self._birth

    @property
    def birthplace(self):
        return self._birthplace

    @property
    def death(self):
        return self._death

    @property
    def deathplace(self):
        return self._deathplace

    @property
    def burial(self):
        return self._burial

    @property
    def plot(self):
        return self._plot

    @property
    def more_info(self):
        return self._more_info

    def __eq__(self, other):
        if self.__class__ != other.__class__:
            return False
        return self.__dict__ == other.__dict__

    @classmethod
    def get_by_id(cls, grave_id: int):
        con = sqlite3.connect(os.getenv("DATABASE_NAME", "graver.db"))
        con.row_factory = sqlite3.Row

        cur = con.cursor()
        cur.execute("SELECT * FROM graves WHERE id=?", (grave_id,))

        record = cur.fetchone()

        if record is None:
            raise NotFound

        memorial = Memorial(*record)  # Row can be unpacked as dict

        con.close()

        return memorial

    @classmethod
    def from_dict(cls, data):
        return cls(
            data.get["id"],
            data.get["name"],
            data.get["birth"],
            data.get["birthplace"],
            data.gete["death"],
            data.get["deathplace"],
            data.get["burial"],
            data.get["plot"],
            data.get["more_info"],
        )

    @classmethod
    def scrape(cls, input_url):
        tree = None
        req = Request(input_url, headers={"User-Agent": "Mozilla/5.0"})
        with urlopen(req) as response:
            tree = BeautifulSoup(response.read(), "lxml")
        url = get_canonical_link(tree)
        id = get_id(tree)
        name = get_name(tree)
        birth = get_birth_date(tree)
        birthplace = get_birth_place(tree)
        death = get_death_date(tree)
        deathplace = get_death_place(tree)
        plot = get_burial_plot(tree)
        burial = None
        more_info = False
        return Memorial(
            id, url, name, birth, birthplace, death, deathplace, burial, plot, more_info
        )

    @classmethod
    def create_table(cls, database_name="graves.db"):
        conn = sqlite3.connect(database_name)
        conn.execute(
            """CREATE TABLE IF NOT EXISTS graves
            (id INTEGER PRIMARY KEY, url TEXT,
            name TEXT, birth TEXT, birthplace TEXT, death TEXT, deathplace TEXT,
            burial TEXT, plot TEXT, more_info BOOL)"""
        )
        conn.close()

    def save(self) -> "Memorial":
        with sqlite3.connect(os.getenv("DATABASE_NAME", "graves.db")) as con:
            con.cursor().execute(
                "INSERT INTO graves (id,url,name,birth,birthplace,death,"
                + "deathplace,burial,plot,more_info) VALUES"
                + "(?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    self._id,
                    self._url,
                    self._name,
                    self._birth,
                    self._birthplace,
                    self._death,
                    self._deathplace,
                    self._burial,
                    self._plot,
                    self._more_info,
                ),
            )
            con.commit()

        return self

    # def save(self) -> "Grave":
    #     row = (grave["id"],)
    #     keys = ["graveid"]
    #     for key in grave.keys():
    #         if key == "id":
    #             continue
    #         row += (grave[key],)
    #         keys.append(key)

    #     col_names = "(" + ", ".join(keys) + ")"
    #     value_hold = "(" + "?," * (len(keys) - 1) + "?)"
    #     insert = "INSERT INTO findAGrave " + col_names + " VALUES " + value_hold

    #     try:
    #         conn = sql.connect(filename)
    #         c = conn.cursor()
    #         c.executemany(insert, [row])
    #         conn.commit()
    #         conn.close()
    #     except sql.IntegrityError:
    #         log.warn("Memorial #" + grave["id"] + " is already in database.")
    #     except Exception as e:
    #         log.exception(e)
