import os
import re
import sqlite3
from dataclasses import asdict, dataclass
from urllib.parse import parse_qsl, urlparse
from urllib.request import Request, urlopen

from bs4 import BeautifulSoup


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

    findagrave_url: str
    id: int
    name: str
    maiden_name: str
    birth: str
    birthplace: str
    death: str
    deathplace: str
    burial: str
    cem_id: int
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
        "id",
        "url",
        "name",
        "maiden_name",
        "birth",
        "birthplace",
        "death",
        "deathplace",
        "burial",
        "cem_id" "plot",
        "coords",
        "more_info",
    ]

    def __init__(self, findagrave_url: str = None, **kwargs):
        super().__init__()
        # data args
        self.findagrave_url = findagrave_url
        self.id = kwargs.get("id", None)
        self.name = kwargs.get("name", None)
        self.maiden_name = kwargs.get("maiden_name", None)
        self.birth = kwargs.get("birth", None)
        self.birthplace = kwargs.get("birthplace", None)
        self.death = kwargs.get("death", None)
        self.deathplace = kwargs.get("deathplace", None)
        self.burial = kwargs.get("burial", None)
        self.cem_id = kwargs.get("cem_id", None)
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
        return asdict(self)

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

    def get_name(self):
        name = self.soup.find("h1", id="bio-name")
        if name:
            maiden = name.find("i")
            if maiden:
                self.maiden_name = maiden.get_text()
            name = name.get_text()
            if maiden:
                name = name.replace(self.maiden_name, "")
            name = name.replace("Famous memorial", "")
            name = name.replace("VVeteran", "")
            name = name.strip()
            self.name = name

    def get_birth(self):
        birthdate = None
        result = self.soup.find("time", itemprop="birthDate")
        if result is not None:
            birthdate = result.get_text()
        self.birth = birthdate

    def get_birth_place(self):
        place = None
        result = self.soup.find("div", itemprop="birthPlace")
        if result is not None:
            place = result.get_text()
        self.birthplace = place

    def get_death(self):
        death_date = None
        result = self.soup.find("span", itemprop="deathDate")
        if result is not None:
            death_date = result.get_text().split("(")[0].strip()
        self.death = death_date

    def get_death_place(self):
        place = None
        result = self.soup.find("div", itemprop="deathPlace")
        if result is not None:
            place = result.get_text()
        self.deathplace = place

    def get_cemetery_id(self):
        cem_id = None
        div = self.soup.find("div", itemtype=re.compile("https://schema.org/Cemetery"))
        if div is not None:
            anchor = div.find("a")
            href = anchor["href"]
            cem_id = int(re.match(".*/([0-9]+)/.*$", href).group(1))
        self.burial = cem_id

    def get_coords(self):
        """Returns Google Map coordinates, if any, as a string 'nn.nnnnnnn,nn.nnnnnn'"""
        latlon = None
        span = self.soup.find("span", itemtype=re.compile("https://schema.org/Map"))
        if span is not None:
            anchor = span.find("a")
            href = anchor["href"]
            # just for fun
            query = urlparse(href).query
            query_args = parse_qsl(query)
            name, latlon = query_args[0]
        self.coords = latlon

    def get_burial_plot(self):
        plot = None
        result = self.soup.find("span", id="plotValueLabel")
        if result is not None:
            plot = result.get_text()
        self.plot = plot

    def get_more_info(self):
        self.more_info = False

    def scrape_page(self):
        merged, new_url = self.check_merged()
        if merged:
            msg = "{url} has been merged into {newurl}".format(
                url=self.findagrave_url, newurl=new_url
            )
            raise MemorialMergedException(msg)

        self.get_canonical_url()
        self.id = int(re.match(".*/([0-9]+)/.*$", self.url).group(1))
        self.get_name()
        self.get_birth()
        self.get_birth_place()
        self.get_death()
        self.get_death_place()
        self.get_cemetery_id()
        self.get_burial_plot()
        self.get_coords()
        self.get_more_info()

    @classmethod
    def create_table(cls, database_name="graves.db"):
        conn = sqlite3.connect(database_name)
        conn.execute(
            """CREATE TABLE IF NOT EXISTS graves
            (id INTEGER PRIMARY KEY, findagrave_url TEXT,
            name TEXT, maiden_name TEXT, birth TEXT, birthplace TEXT,
            death TEXT, deathplace TEXT, burial TEXT, plot TEXT,
            coords TEXT, more_info BOOL)"""
        )
        conn.close()

    def save(self) -> "Memorial":
        with sqlite3.connect(os.getenv("DATABASE_NAME", "graves.db")) as con:
            con.cursor().execute(
                "INSERT OR REPLACE INTO graves (id,findagrave_url,name,maiden_name,"
                + "birth,birthplace,death,"
                + "deathplace,burial,plot,coords,more_info) VALUES"
                + "(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    self.id,
                    self.findagrave_url,
                    self.name,
                    self.maiden_name,
                    self.birth,
                    self.birthplace,
                    self.death,
                    self.deathplace,
                    self.burial,
                    self.plot,
                    self.coords,
                    self.more_info,
                ),
            )
            con.commit()

        return self

    @classmethod
    def get_by_id(cls, grave_id: int):
        con = sqlite3.connect(os.getenv("DATABASE_NAME", "graves.db"))
        con.row_factory = sqlite3.Row

        cur = con.cursor()
        cur.execute("SELECT * FROM graves WHERE id=?", (grave_id,))

        record = cur.fetchone()

        if record is None:
            raise NotFound

        memorial = Memorial(
            **record, get=False, scrape=False
        )  # Row can be unpacked as dict

        con.close()

        return memorial
