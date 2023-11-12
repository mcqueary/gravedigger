import os
import sqlite3
from dataclasses import asdict, dataclass
from urllib.request import Request, urlopen

from bs4 import BeautifulSoup

from graver.soup import (
    get_birth_date,
    get_birth_place,
    get_burial_plot,
    get_canonical_link,
    get_coords,
    get_death_date,
    get_death_place,
    get_id,
    get_name,
)

# from graver.page import Page


class GraverException(Exception):
    pass


class MemorialMergedException(GraverException):
    pass


class NotFound(Exception):
    pass


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
    _coords: str
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
    def coords(self):
        return self._coords

    @property
    def more_info(self):
        return self._more_info

    def __eq__(self, other):
        if self.__class__ != other.__class__:
            return False
        return self.__dict__ == other.__dict__

    @classmethod
    def from_dict(cls, d):
        return Memorial(**d)

    def to_dict(self):
        return asdict(self)

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
    def scrape(cls, input_url):
        tree = None
        req = Request(input_url, headers={"User-Agent": "Mozilla/5.0"})
        with urlopen(req) as response:
            tree = BeautifulSoup(response.read(), "lxml")
        url = get_canonical_link(tree)
        coords = get_coords(tree)
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
            id,
            url,
            name,
            birth,
            birthplace,
            death,
            deathplace,
            burial,
            plot,
            coords,
            more_info,
        )

    @classmethod
    def create_table(cls, database_name="graves.db"):
        conn = sqlite3.connect(database_name)
        conn.execute(
            """CREATE TABLE IF NOT EXISTS graves
            (id INTEGER PRIMARY KEY, url TEXT,
            name TEXT, birth TEXT, birthplace TEXT, death TEXT, deathplace TEXT,
            burial TEXT, plot TEXT, coords TEXT, more_info BOOL)"""
        )
        conn.close()

    def save(self) -> "Memorial":
        with sqlite3.connect(os.getenv("DATABASE_NAME", "graves.db")) as con:
            con.cursor().execute(
                "INSERT OR REPLACE INTO graves (id,url,name,birth,birthplace,death,"
                + "deathplace,burial,plot,coords,more_info) VALUES"
                + "(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
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
                    self._coords,
                    self._more_info,
                ),
            )
            con.commit()

        return self
