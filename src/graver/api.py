import json
import logging
import math
import os
import re
import sqlite3
from collections import namedtuple
from dataclasses import asdict, dataclass
from re import Match
from time import sleep
from typing import Dict, List, Optional, cast
from urllib.parse import parse_qsl, urlparse, urlunparse

import requests
from bs4 import BeautifulSoup, Tag
from requests import RequestException, Response

from .constants import FINDAGRAVE_BASE_URL, FINDAGRAVE_ROWS_PER_PAGE

# import graver

# from graver import constants

log = logging.getLogger(__name__)


class MemorialException(Exception):
    def __init__(self, message):
        super().__init__(message)


class MemorialParseException(MemorialException):
    def __init__(self, message):
        super().__init__(message)


class MemorialMergedException(MemorialException):
    def __init__(self, message, old_url, new_url):
        super().__init__(message)
        self.old_url = old_url
        self.new_url = new_url


class MemorialRemovedException(MemorialException):
    pass


class NotFound(MemorialException):
    pass


class Driver(object):
    recoverable_errors: Dict[int, str] = {
        500: "Internal Server Error",
        502: "Bad Gateway",
        503: "Service Unavailable",
        504: "Gateway Timeout",
        599: "Network Connect Timeout Error",
    }

    def __init__(self, **kwargs) -> None:
        self.num_retries = 0
        self.max_retries: int = int(kwargs.get("max_retries", 3))
        self.retry_ms: int = int(kwargs.get("retry_ms", 500))
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": "Mozilla/5.0"})

    def get(self, url: str, **kwargs) -> Response:
        retries = 0
        try:
            response = self.session.get(url, **kwargs)
            while (
                response.status_code in Driver.recoverable_errors.keys()
                and retries < self.max_retries
            ):
                retries += 1
                log.warning(
                    f"Driver: [{response.status_code}: {response.reason}] "
                    f"{url} -- Retrying ({retries} of {self.max_retries}, "
                    f"timeout={self.retry_ms}ms)"
                )
                sleep(self.retry_ms / 1000)
                response = self.session.get(url, **kwargs)
            self.num_retries += retries
            return response
        except requests.exceptions.RequestException as e:
            raise e


@dataclass
class Cemetery:
    """Class for keeping track of a Find A Grave cemetery."""

    cemetery_id: int
    findagrave_url: str
    name: str
    location: str
    coords: str
    num_memorials: int

    def __init__(self, findagrave_url: str, **kwargs) -> None:
        super().__init__()
        self.findagrave_url = findagrave_url
        self.cemetery_id = kwargs.get("cemetery_id", None)
        self.name = kwargs.get("name", None)
        self.location = kwargs.get("location", None)
        self.coords = kwargs.get("coords", None)
        self.num_memorials = kwargs.get("num_memorials", None)
        # behavior args
        self.driver = kwargs.get("driver", Driver())
        self.get = kwargs.get("get", True)
        self.scrape = kwargs.get("scrape", True)
        self.params: dict = {}

        if self.get:
            response = self.driver.get(findagrave_url, params=self.params)
            self.soup = BeautifulSoup(response.content, "html.parser")

        if self.scrape:
            self.scrape_cemetery_info()

    def scrape_cemetery_info(self):
        self.scrape_canonical_url()
        self.cemetery_id = int(
            re.match(
                "https://www.findagrave.com/cemetery/([0-9]+)/.*", self.findagrave_url
            ).group(1)
        )
        self.search_url = (
            f"{FINDAGRAVE_BASE_URL}"
            f"/cemetery/{self.cemetery_id}"
            f"/memorial-search?"
        )
        self.scrape_name()
        self.scrape_location()
        self.scrape_coords()
        self.scrape_num_memorials()

    def __eq__(self, other):
        if self.__class__ != other.__class__:
            return False
        return (
            self.cemetery_id == other.cemetery_id
            and self.findagrave_url == other.findagrave_url
            and self.name == other.name
            and self.location == other.location
            and self.coords == other.coords
        )

    @classmethod
    def from_dict(cls, d):
        return Cemetery(**d, get=False, scrape=False)

    def to_dict(self):
        d = asdict(self)
        return d

    @classmethod
    def create_table(cls, database_name="graves.db"):
        conn = sqlite3.connect(database_name)
        conn.execute(
            """CREATE TABLE IF NOT EXISTS cemeteries
            (cemetery_id INTEGER PRIMARY KEY, url TEXT,
            name TEXT, location TEXT, coords TEXT, more_info BOOL)"""
        )
        conn.close()

    def scrape_canonical_url(self):
        link = self.soup.find("link", rel=re.compile("canonical"))
        if link is not None:
            self.findagrave_url = link["href"]

    def scrape_name(self):
        if (result := self.soup.find("h1", itemprop="name")) is not None:
            self.name = result.get_text().strip()

    def scrape_location(self):
        location = None
        if (result := self.soup.find("span", itemprop="addressLocality")) is not None:
            locality = result.get_text().strip()
            if (result := self.soup.find("span", itemprop="addressRegion")) is not None:
                region = result.get_text().strip()
                if (
                    result := self.soup.find("span", itemprop="addressCountry")
                ) is not None:
                    country = result.get_text().strip()
                    location = locality + ", " + region + ", " + country
        self.location = location

    def scrape_coords(self):
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

    def scrape_num_memorials(self):
        count = 0
        if (div := self.soup.find("div", id="MemorialsAll")) is not None:
            if (ul := div.find("ul")) is not None:
                if (a := ul.find("a")) is not None:
                    count = re.match("View Memorials ([0-9,]+)", a.get_text()).group(1)
                    count = int(count.replace(",", ""))
        self.num_memorials = count


@dataclass(frozen=True)
class Memorial:
    """Class for keeping track of a Find A Grave memorial."""

    memorial_id: int
    findagrave_url: str
    prefix: str
    name: str
    suffix: str
    nickname: str
    maiden_name: str
    original_name: str
    famous: bool
    veteran: bool
    birth: str
    birth_place: str
    death: str
    death_place: str
    memorial_type: str
    burial_place: str
    cemetery_id: int
    plot: str
    coords: str
    has_bio: bool

    def __eq__(self, other):
        if self.__class__ != other.__class__:
            return False
        return (
            self.memorial_id == other.memorial_id
            and self.findagrave_url == other.findagrave_url
            and self.prefix == other.prefix
            and self.name == other.name
            and self.suffix == other.suffix
            and self.nickname == other.nickname
            and self.maiden_name == other.maiden_name
            and self.original_name == other.original_name
            and self.famous == other.famous
            and self.veteran == other.veteran
            and self.birth == other.birth
            and self.birth_place == other.birth_place
            and self.death == other.death
            and self.death_place == other.death_place
            and self.memorial_type == other.memorial_type
            and self.burial_place == other.burial_place
            and self.cemetery_id == other.cemetery_id
            and self.plot == other.plot
            and self.coords == other.coords
            and self.has_bio == other.has_bio
        )

    @classmethod
    def from_dict(cls, d):
        return cls(**d)

    def to_dict(self):
        d = asdict(self)
        return d

    def to_json(self, **kwargs):
        return json.dumps(self.to_dict(), ensure_ascii=False, **kwargs)

    @staticmethod
    def search(cemetery: Cemetery = cast(Cemetery, None), **kwargs):
        return _SearchWorker(cemetery, **kwargs).search()

    @classmethod
    def create_table(cls, database_name="graves.db"):
        conn = sqlite3.connect(database_name)
        conn.execute(
            """CREATE TABLE IF NOT EXISTS graves
            (
                memorial_id INTEGER PRIMARY KEY,
                findagrave_url TEXT,
                prefix TEXT,
                name TEXT,
                suffix TEXT,
                nickname TEXT,
                maiden_name TEXT,
                original_name TEXT,
                famous BOOL,
                veteran BOOL,
                birth TEXT,
                birth_place TEXT,
                death TEXT,
                death_place TEXT,
                memorial_type TEXT,
                cemetery_id INTEGER,
                burial_place TEXT,
                plot TEXT,
                coords TEXT,
                has_bio BOOL
            )"""
        )
        conn.close()

    def save(self) -> "Memorial":
        with sqlite3.connect(os.getenv("DATABASE_NAME", "graves.db")) as con:
            con.cursor().execute(
                "INSERT OR REPLACE INTO graves VALUES ("
                ":memorial_id, "
                ":findagrave_url, "
                ":prefix, "
                ":name, "
                ":suffix, "
                ":nickname, "
                ":maiden_name, "
                ":original_name, "
                ":famous, "
                ":veteran, "
                ":birth, "
                ":birth_place, "
                ":death, "
                ":death_place, "
                ":memorial_type, "
                ":cemetery_id, "
                ":burial_place, "
                ":plot, "
                ":coords, "
                ":has_bio"
                ")",
                self.__dict__,
            )
            con.commit()

        return self

    @classmethod
    def parse(cls, findagrave_url: str, **kwargs):
        return _MemorialParser(findagrave_url, **kwargs).parse()

    @classmethod
    def get_by_id(cls, memorial_id: int):
        dbname = os.getenv("DATABASE_NAME", "graves.db")
        con = sqlite3.connect(dbname)
        con.row_factory = sqlite3.Row

        cur = con.cursor()
        cur.execute("SELECT * FROM graves WHERE memorial_id=?", (memorial_id,))

        record = cur.fetchone()

        if record is None:
            raise NotFound(f"memorial_id={memorial_id} not present in {dbname}")

        memorial = Memorial(**record)  # Row can be unpacked as dict

        con.close()

        return memorial


class _MemorialParser:
    def __init__(self, findagrave_url: str, **kwargs) -> None:
        self.memorial_id = kwargs.get("memorial_id", None)
        self.findagrave_url = findagrave_url
        self.prefix = kwargs.get("prefix", None)
        self.name = kwargs.get("name", None)
        self.suffix = kwargs.get("suffix", None)
        self.nickname = kwargs.get("nickname", None)
        self.maiden_name = kwargs.get("maiden_name", None)
        self.original_name = kwargs.get("original_name", None)
        self.famous = kwargs.get("famous", None)
        self.veteran = kwargs.get("veteran", None)
        self.birth = kwargs.get("birth", None)
        self.birth_place = kwargs.get("birth_place", None)
        self.death = kwargs.get("death", None)
        self.death_place = kwargs.get("death_place", None)
        self.memorial_type = kwargs.get("memorial_type", None)
        self.burial_place = kwargs.get("burial_place", None)
        self.cemetery_id = kwargs.get("cemetery_id", None)
        self.plot = kwargs.get("plot", None)
        self.coords = kwargs.get("coords", None)
        self.has_bio = kwargs.get("has_bio", None)
        # # behavior/instance args
        self.driver = kwargs.get("driver", Driver())
        self.get = kwargs.get("get", True)
        self.scrape = kwargs.get("scrape", True)
        # self.soup: Optional[Tag] = None
        self.soup = None
        self.m: dict = {}

        # Valid URL but not a Memorial
        # if "/memorial/" not in self.findagrave_url:
        #     raise MemorialException(f"Invalid memorial URL: {self.findagrave_url}")

        if self.get:
            try:
                response = self.driver.get(self.findagrave_url)
                self.soup = BeautifulSoup(response.content, "html.parser")

                if response.ok:
                    self.scrape_canonical_url()
                else:
                    if response.status_code == 404:
                        if self.check_removed():
                            msg = f"{self.findagrave_url} has been removed"
                            raise MemorialRemovedException(msg)
                        elif (new_url := self.check_merged()) is not None:
                            msg = (
                                f"{self.findagrave_url} has been merged into {new_url}"
                            )
                            raise MemorialMergedException(
                                msg, self.findagrave_url, new_url
                            )
                        else:
                            response.raise_for_status()
                    else:
                        response.raise_for_status()
            except RequestException as ex:
                raise MemorialParseException(ex) from ex

        if self.scrape:
            self.scrape_page()

    def parse(self):
        pass
        return Memorial(
            memorial_id=self.memorial_id,
            findagrave_url=self.findagrave_url,
            prefix=self.prefix,
            name=self.name,
            suffix=self.suffix,
            nickname=self.nickname,
            maiden_name=self.maiden_name,
            original_name=self.original_name,
            famous=self.famous,
            veteran=self.veteran,
            birth=self.birth,
            birth_place=self.birth_place,
            death=self.death,
            death_place=self.death_place,
            memorial_type=self.memorial_type,
            burial_place=self.burial_place,
            cemetery_id=self.cemetery_id,
            plot=self.plot,
            coords=self.coords,
            has_bio=self.has_bio,
        )

    def check_removed(self):
        popup = self.soup.find("div", class_="jumbotron text-center")
        if popup is not None:
            if "This memorial has been removed." in popup.get_text(strip=True):
                return True
        return False

    def check_merged(self) -> Optional[str]:
        merged_url: Optional[str] = None
        if self.soup is not None:
            popup = cast(Tag, self.soup.find("div", class_="jumbotron text-center"))
            if popup is not None:
                if "Memorial has been merged" in popup.get_text(strip=True):
                    for p in popup.find_all("p"):
                        anchor = p.find("a")
                        if anchor is not None:
                            new_path: str = p.find("a")["href"]
                            parsed = urlparse(self.findagrave_url)
                            merged_url = urlunparse(parsed._replace(path=new_path))
        return merged_url

    def scrape_canonical_url(self):
        self.findagrave_url = self.soup.find("link", rel=re.compile("canonical"))[
            "href"
        ]

    @staticmethod
    def scrape_name(name_tag: Tag, memorial_link: str):
        NameParts = namedtuple(
            "NameParts", "prefix, name, nickname, maiden_name, suffix"
        )
        name = name_tag.get_text()
        name = name.replace("Famous memorial", "")
        name = name.replace("VVeteran", "")
        name = name.strip()

        prefix, suffix = _MemorialParser.get_prefix_suffix(name, memorial_link)
        if prefix is not None:
            name = name.replace(f"{prefix} ", "")
        if suffix is not None:
            name = name.replace(f" {suffix}", "")
        if (nickname := _MemorialParser.get_nickname(name)) is not None:
            name = name.replace(f" \u201c{nickname}\u201d", "")
        if name_tag.i is not None:
            maiden_name = name_tag.i.get_text(strip=True)
            name = name.replace(f" {maiden_name} ", " ")
        else:
            maiden_name = None

        return NameParts(prefix, name, nickname, maiden_name, suffix)

    @staticmethod
    def get_prefix_suffix(name: str, memorial_link: str):
        # simple name is derived from the final path component in a memorial link
        # e.g. /memorial/12345/john-q-smith (simple name is "john q smith")
        prefix = None
        suffix = None

        elements = memorial_link.split("/")
        simple_name = elements[len(elements) - 1]
        simple_name_tokens = simple_name.split("-")
        full_name_tokens = name.split(" ")

        for idx in range(0, len(full_name_tokens)):
            if full_name_tokens[idx].lower().replace(".", "") != simple_name_tokens[0]:
                if prefix is None:
                    prefix = full_name_tokens[idx]
                else:
                    prefix += f" {full_name_tokens[idx]}"
            else:
                break

        tok = full_name_tokens[len(full_name_tokens) - 1].replace(".", "")
        if tok.lower() != simple_name_tokens[len(simple_name_tokens) - 1]:
            suffix = full_name_tokens[len(full_name_tokens) - 1]
        return prefix, suffix

    @staticmethod
    def get_nickname(name: str):
        nick = None
        pattern = r"\u201c(.*)\u201d"
        if (match := re.search(pattern, name)) is not None:
            nick = match.group(1)
        return nick

    def scrape_names(self, tag):
        parts = _MemorialParser.scrape_name(tag, self.findagrave_url)
        self.name = parts.name
        self.maiden_name = parts.maiden_name
        self.nickname = parts.nickname
        self.prefix = parts.prefix
        self.suffix = parts.suffix

    def scrape_famous(self, tag):
        if tag.find("span", title="Famous memorial") is not None:
            self.famous = True

    def scrape_veteran(self, tag):
        if tag.find("span", string=re.compile("Veteran")) is not None:
            self.veteran = True

    def scrape_birth_info(self, tag: Tag):
        birth_info = cast(Tag, tag.find_next("dd"))
        self.birth = cast(Tag, birth_info.find("time", itemprop="birthDate")).get_text()
        if (birth_place := birth_info.find("div", itemprop="birthPlace")) is not None:
            self.birth_place = birth_place.get_text()

    def scrape_death_info(self, tag: Tag):
        death_info = cast(Tag, tag.find_next("dd"))
        self.death = (
            cast(Tag, death_info.find("span", itemprop="deathDate"))
            .get_text()
            .split("(")[0]
            .strip()
        )
        if (death_place := death_info.find("div", itemprop="deathPlace")) is not None:
            self.death_place = death_place.get_text()

    def scrape_coords(self, tag: Tag):
        """Returns Google Map coordinates, if any, as a string 'nn.nnnnnnn,nn.nnnnnn'"""
        latlon = None
        if (
            span := tag.find("span", itemtype=re.compile("https://schema.org/Map"))
        ) is not None:
            anchor: Tag = cast(Tag, span.find("a"))
            href: str = cast(str, anchor["href"])
            # just for fun
            query = urlparse(href).query
            query_args = parse_qsl(query)
            name, latlon = query_args[0]
        self.coords = latlon

    def scrape_burial_info(self, tag: Tag):
        self.memorial_type = tag.get_text(strip=True).replace("Read More", "")

        dd = cast(Tag, tag.find_next("dd"))

        # Coords can exist regardless of burial type (which may be a site bug)
        self.scrape_coords(dd)
        if (cemetery := dd.find("div", itemtype="https://schema.org/Cemetery")) is None:
            if (place := dd.find("span", id="otherPlace")) is not None:
                self.burial_place = place.get_text(strip=True)
        else:
            # Known location
            cemetery = cast(Tag, cemetery)
            self.scrape_cemetery_id(cemetery)
            cemetery_name: str = cemetery.get_text(strip=True)
            cemetery_address = cast(Tag, dd.find("span", itemprop="address")).get_text(
                strip=True
            )
            cemetery_address = cemetery_address.replace(",", ", ")
            self.burial_place = ", ".join([cemetery_name, cemetery_address])

    def scrape_cemetery_id(self, cem: Tag):
        if (href := cast(str, cast(Tag, cem.find("a"))["href"])) is not None:
            match: Optional[Match[str]] = re.search("/([0-9]+)/", href)
            assert match is not None
            self.cemetery_id = int(match.group(1))

    def scrape_plot_info(self, dt: Tag):
        self.plot = cast(Tag, dt.find_next("dd")).get_text(strip=True)

    def scrape_memorial_id(self, dt: Tag):
        dd = cast(Tag, dt.find_next("dd"))
        m_id = cast(Tag, dd.find("span", id="memNumberLabel"))
        self.memorial_id = int(m_id.get_text(strip=True))

    def scrape_vitals(self):
        for div in self.soup.find_all("div"):
            if div.find("h1", id="bio-name"):
                return div

    def scrape_has_bio(self):
        if self.soup.find("meta", property="og:description") is not None:
            self.has_bio = True

    def scrape_page(self):
        self.scrape_has_bio()

        # Get vital statistics and burial info
        vitals = self.scrape_vitals()
        headline = vitals.find("h1", id="bio-name")
        self.scrape_famous(headline)
        self.scrape_veteran(headline)
        self.scrape_names(headline)
        dt_list = vitals.find("dl").find_all("dt")
        for dt in dt_list:
            text = dt.get_text(strip=True)
            if text.startswith("Original Name"):
                oname = dt.find_next("dd")
                self.original_name = oname.get_text()
            # elif dt.find("span", id="birthLabel") is not None:
            elif text == "Birth":
                self.scrape_birth_info(dt)
            elif text == "Death":
                self.scrape_death_info(dt)
            elif (
                text == "Burial"
                or text.startswith("Cenotaph")
                or text.startswith("Monument")
            ):
                self.scrape_burial_info(dt)
            elif text == "Plot":
                self.scrape_plot_info(dt)
            elif text == "Memorial ID":
                self.scrape_memorial_id(dt)


class _SearchWorker:
    def __init__(  # noqa: max-complexity=23
        self, cemetery: Cemetery = cast(Cemetery, None), **kwargs
    ) -> None:
        self.cemetery: Cemetery = cemetery
        self.params: dict = {}

        self.max_results: int = kwargs.pop("max_results", 0)
        self.page: int = kwargs.get("page", None)
        self.driver: Driver
        self.search_url: str

        if self.cemetery is None:
            self.driver = kwargs.pop("driver", Driver())
            self.search_url = f"{FINDAGRAVE_BASE_URL}/memorial/search?"
            # query params
            self.params["firstname"] = kwargs.get("firstname", "")
            self.params["middlename"] = kwargs.get("middlename", "")
            self.params["lastname"] = kwargs.get("lastname", "")
            self.process_birth_year(**kwargs)
            self.process_death_year(**kwargs)
            self.params["location"] = kwargs.get("location", "")
            self.params["locationId"] = kwargs.get("locationId", "")
            kwargs["memorialid"] = kwargs.get("memorialid", "")
            self.params["mcid"] = kwargs.get("mcid", "")
            self.params["linkedToName"] = kwargs.get("linkedToName", "")
            # Date added. "all" or n (where n = last n days)
            self.params["datefilter"] = kwargs.get("datefilter", "")
            # orderby: r (random?), n/n- (newest first/oldest first), b/b- (birth),
            # d/d- (death), pl (plot)
            self.params["orderby"] = kwargs.get("orderby", "r")
            self.params["plot"] = kwargs.get("plot", "")
            # famous and sponsored are mutually exclusive
            self.process_famous(**kwargs) or self.process_sponsored(**kwargs)

            self.process_no_cemetery(**kwargs)
            # cenotaph and monument are mutually exclusive
            self.process_cenotaph(**kwargs) or self.process_monument(**kwargs)
            self.process_veteran(**kwargs)
        else:
            self.driver = cemetery.driver
            self.search_url = cemetery.search_url
            # query params
            self.params["firstname"] = kwargs.get("firstname", "")
            self.params["middlename"] = kwargs.get("middlename", "")
            self.params["lastname"] = kwargs.get("lastname", "")
            self.params["cemeteryName"] = self.cemetery.name
            self.process_birth_year(**kwargs)
            self.process_death_year(**kwargs)
            kwargs["memorialid"] = kwargs.get("memorialid", "")
            self.params["mcid"] = kwargs.get("mcid", "")
            self.params["linkedToName"] = kwargs.get("linkedToName", "")
            # Date added. "all" or n (where n = last n days)
            self.params["datefilter"] = kwargs.get("datefilter", "")
            # orderby: r (random?), n/n- (newest first/oldest first), b/b- (birth),
            # d/d- (death), pl (plot)
            self.params["orderby"] = kwargs.get("orderby", "r")
            self.params["plot"] = kwargs.get("plot", "")
            # famous and sponsored are mutually exclusive
            self.process_famous(**kwargs) or self.process_sponsored(**kwargs)
            # cenotaph and monument are mutually exclusive
            self.process_cenotaph(**kwargs) or self.process_monument(**kwargs)
            self.process_veteran(**kwargs)

        # Memorial types
        # Not buried in a cemetery

        # Include:
        self.process_include_nickname(**kwargs)
        self.process_include_maiden_name(**kwargs)
        self.process_include_titles(**kwargs)
        self.process_exact_name(**kwargs) or self.process_fuzzy_names(**kwargs)

        # Filters
        self.process_photo_filter(**kwargs)
        self.process_gps_filter(**kwargs)
        self.process_flowers(**kwargs)
        self.process_has_plot(**kwargs)

        # get the page requested
        self.process_page(**kwargs)

    def process_birth_year(self, **kwargs):
        # date filters are:
        # "unknown" (looks for value="unknown"), "before", "after",
        # or n (i.e. +/- n years)
        if (datefilter := kwargs.get("birthyearfilter", "")) != "unknown":
            self.params["birthyear"] = kwargs.get("birthyear", "")
        self.params["birthyearfilter"] = datefilter
        return True

    def process_death_year(self, **kwargs):
        # date filters are:
        # "unknown" (looks for value="unknown"), "before", "after",
        # or n (i.e. +/- n years)
        if (datefilter := kwargs.get("deathyearfilter", "")) != "unknown":
            self.params["deathyear"] = kwargs.get("deathyear", "")
        self.params["deathyearfilter"] = datefilter
        return True

    def process_no_cemetery(self, **kwargs):
        if self.cemetery is None:
            if "noCemetery" in kwargs:
                # location is mutually exclusive with noCemetery
                self.params.pop("location")
                self.params.pop("locationId")
                self.params["noCemetery"] = str(kwargs.get("noCemetery")).lower()

    def process_famous(self, **kwargs):
        if "famous" in kwargs:
            self.params["famous"] = str(kwargs.get("famous")).lower()
            return True
        return False

    def process_sponsored(self, **kwargs):
        if "sponsored" in kwargs:
            self.params["sponsored"] = str(kwargs.get("sponsored")).lower()
            return True
        return False

    def process_cenotaph(self, **kwargs):
        if "cenotaph" in kwargs:
            self.params["cenotaph"] = str(kwargs.get("cenotaph")).lower()
            return True
        return False

    def process_monument(self, **kwargs):
        if "monument" in kwargs:
            self.params["monument"] = str(kwargs.get("monument")).lower()
            return True
        return False

    def process_veteran(self, **kwargs):
        if "isVeteran" in kwargs:
            self.params["isVeteran"] = str(kwargs.get("isVeteran")).lower()
            return True
        return False

    def process_include_nickname(self, **kwargs):
        if "includeNickName" in kwargs:
            self.params["includeNickName"] = str(kwargs.get("includeNickName")).lower()
            return True
        return False

    def process_include_maiden_name(self, **kwargs):
        if "includeMaidenName" in kwargs:
            self.params["includeMaidenName"] = str(
                kwargs.get("includeMaidenName")
            ).lower()
            return True
        return False

    def process_include_titles(self, **kwargs):
        if "includeTitles" in kwargs:
            self.params["includeTitles"] = str(kwargs.get("includeTitles")).lower()
            return True
        return False

    def process_exact_name(self, **kwargs):
        if "exactName" in kwargs:
            self.params["exactName"] = str(kwargs.get("exactName")).lower()
            return True
        return False

    def process_fuzzy_names(self, **kwargs):
        if "fuzzyNames" in kwargs:
            self.params["fuzzyNames"] = str(kwargs.get("fuzzyNames")).lower()
            return True
        return False

    def process_photo_filter(self, **kwargs):
        # "photos"/"nophotos" (mutex)
        if "photofilter" in kwargs:
            self.params["photofilter"] = kwargs.get("photofilter")
            return True
        return False

    def process_gps_filter(self, **kwargs):
        # "gps"/"nogps"
        if "gpsfilter" in kwargs:
            self.params["gpsfilter"] = kwargs.get("gpsfilter")
            return True
        return False

    def process_flowers(self, **kwargs):
        # "true"/""
        if "flowers" in kwargs:
            self.params["flowers"] = str(kwargs.get("flowers")).lower()
            return True
        return False

    def process_has_plot(self, **kwargs):
        if "hasPlot" in kwargs:
            value = str(kwargs.get("hasPlot")).lower()
            if value == "false":
                self.params.pop("plot")
            self.params["hasPlot"] = value
            return True
        return False

    def process_page(self, **kwargs):
        # page of search results
        if self.page is not None:
            self.params["page"] = self.page
            return True
        return False

    def search(self):
        rs = []
        # Load the first page to learn how many results there may be
        log.debug(f"Search params={self.params}")
        response = self.driver.get(self.search_url, params=self.params)
        soup = BeautifulSoup(response.content, "html.parser")

        # If this query isn't for a specific page, calculate how many
        # pages the results will span
        if self.page is not None:
            count = FINDAGRAVE_ROWS_PER_PAGE
        else:
            count = self.scrape_count(soup)

        # limit results to user specified maximum
        if 0 < self.max_results < count:
            count = self.max_results

        num_pages = math.ceil(count / FINDAGRAVE_ROWS_PER_PAGE)

        # scrape the page we already have (page 1)
        results = self.scrape_results_page(soup, max_results=(count - len(rs)))
        rs.extend(results)

        # scrape additional pages, if there are any left to get
        for i in range(2, num_pages + 1):
            self.params["page"] = i
            response = self.driver.get(self.search_url, params=self.params)
            soup = BeautifulSoup(response.content, "html.parser")

            results = self.scrape_results_page(soup, max_results=(count - len(rs)))
            rs.extend(results)

        return ResultSet(response.request.url, rs)

    def scrape_count(self, soup: BeautifulSoup) -> int:
        count = 0
        if (
            tag := soup.find("h1", string=re.compile("[0-9,]+ matching records? found"))
        ) is not None:
            line = tag.get_text(strip=True)
            match: Optional[Match[str]] = re.match("[0-9,]+", line)
            assert match is not None
            num_str = match.group(0)
            num_str = num_str.replace(",", "")
            count = int(num_str)
        return count

    def scrape_memorial_url(self, tag: Tag, mem: dict) -> Optional[str]:
        path = None
        if (anchor := cast(Tag, tag.find("a"))) is not None:
            path = cast(str, anchor["href"])
            path = f"{FINDAGRAVE_BASE_URL}{path}"
        mem["findagrave_url"] = path
        match: Optional[Match[str]] = re.match(".*/([0-9]+)/.*", path)
        assert match is not None
        mid = match.group(1)
        mem["memorial_id"] = int(mid)
        return path

    def scrape_memorial_type(self, tag: Tag, mem: dict):
        if (h2 := tag.find("h2")) is not None:
            if (button := cast(Tag, h2.find("button"))) is not None:
                if button.get_text() == "Cenotaph":
                    mem["memorial_type"] = "Cenotaph"
                elif button.get_text() == "Monument":
                    mem["memorial_type"] = "Monument"
            else:
                mem["memorial_type"] = "Burial"

    def scrape_memorial_names(self, tag: Tag, mem: dict):
        name_grave = cast(Tag, tag.find("h2", {"class": "name-grave"}))
        # get the full name
        name_tag = cast(Tag, name_grave.find("i", {"class": "pe-2"}))
        parts = _MemorialParser.scrape_name(name_tag, mem["findagrave_url"])
        mem["name"] = parts.name
        mem["maiden_name"] = parts.maiden_name
        mem["suffix"] = parts.suffix
        mem["prefix"] = parts.prefix
        mem["nickname"] = parts.nickname

    def scrape_memorial_dates(self, tag: Tag, mem: dict):
        grave = cast(Tag, tag.find("div", {"class": "memorial-item---grave"}))
        birth_death = cast(
            Tag, grave.find("b", {"class": re.compile("birthDeathDates.*")})
        ).get_text(strip=True)
        # pattern is "date" endash "date"
        dates = birth_death.split(" \u2013 ")
        if len(dates) == 2:
            mem["birth"] = dates[0]
            mem["death"] = dates[1]

    def scrape_memorial_famous(self, tag: Tag, mem: dict) -> None:
        if tag.find("span", title="Famous Memorial") is not None:
            mem["famous"] = True

    def scrape_memorial_veteran(self, tag: Tag, mem: dict):
        if (h2 := cast(Tag, tag.find("h2", {"class": "name-grave"}))) is not None:
            if h2.find("span", title="Veteran") is not None:
                mem["veteran"] = True

    def scrape_memorial_cemetery_info(self, tag, mem):
        if self.cemetery is not None:
            mem["cemetery_id"] = self.cemetery.cemetery_id
            mem["burial_place"] = f"{self.cemetery.name}, {self.cemetery.location}"

        # Cemetery info and optional plot info
        if (form := tag.form) is not None:
            # Get the cemetery path e.g. '/cemetery/12345/the-cemetery-name'
            path = form.get("action")
            cem_name = form.get_text(strip=True)
            if self.cemetery is None:
                mem["cemetery_id"] = int(re.match(".*/([0-9]+)/.*$", path).group(1))
                if (p := form.find_next("p")) is not None:
                    cem_location = p.get_text(strip=True)
                    cem_location = " ".join(cem_location.split())
                    mem["burial_place"] = f"{cem_name}, {cem_location}"
                if (p := p.find_next_sibling("p")) is not None:
                    mem["plot"] = p.get_text(strip=True).replace("Plot info:", "")
        elif tag.p is not None:
            mem["plot"] = tag.p.get_text(strip=True).replace("Plot info: ", "")

    def scrape_results_page(
        self, page_soup: BeautifulSoup, cemetery=None, max_results=0
    ) -> List[Memorial]:
        divs = page_soup.find_all("div", role="group")
        results: List[Memorial] = []

        for div in divs:
            # mem = {}
            mem = {
                "memorial_id": None,
                "findagrave_url": None,
                "prefix": None,
                "name": None,
                "suffix": None,
                "nickname": None,
                "maiden_name": None,
                "original_name": None,
                "famous": None,
                "veteran": None,
                "birth": None,
                "birth_place": None,
                "death": None,
                "death_place": None,
                "memorial_type": None,
                "burial_place": None,
                "cemetery_id": None,
                "plot": None,
                "coords": None,
                "has_bio": None,
            }

            self.scrape_memorial_url(div, mem)
            mem_item_info = div.find("div", {"class": "memorial-item--info"})
            mem_item_grave = div.find("div", {"class": "memorial-item---grave"})
            self.scrape_memorial_type(mem_item_grave, mem)
            self.scrape_memorial_names(mem_item_info, mem)
            self.scrape_memorial_dates(mem_item_info, mem)
            self.scrape_memorial_famous(mem_item_info, mem)
            self.scrape_memorial_veteran(mem_item_info, mem)
            mem_cem_info = div.find("div", {"class": "memorial-item---cemet"})
            self.scrape_memorial_cemetery_info(mem_cem_info, mem)
            results.append(Memorial.from_dict(mem))
            if 0 < max_results == len(results):
                break

        return results


class ResultSet(list):
    """A ResultSet is just a list that keeps track of the object
    that created it."""

    def __init__(self, source, result=()) -> None:
        super(ResultSet, self).__init__(result)
        self.source = source
