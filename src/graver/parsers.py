import re
from urllib.parse import parse_qsl, urlparse
from urllib.request import Request, urlopen

from bs4 import BeautifulSoup
from cemetery import Cemetery
from memorial import Memorial, MemorialMergedException


class Parser(object):
    def __init__(self, url, name, search_url):
        self.url = url
        self.name = name
        self.search_url = search_url

    @staticmethod
    def parse_canonical_link(soup):
        link = soup.find("link", rel=re.compile("canonical"))["href"]
        return link


class MemorialParser(Parser):
    DEFAULT_URL_FORMAT = "https://www.findagrave.com/memorial/{}"
    PAGE_URL = "http://www.findagrave.com/memorial"
    NAME = "Memorial Search"
    SEARCH_URL = "search?"

    def __init__(self):
        super().__init__(
            MemorialParser.PAGE_URL, MemorialParser.NAME, MemorialParser.SEARCH_URL
        )

    @staticmethod
    def check_merged(soup: BeautifulSoup):
        merged = False
        merged_url = None
        popup = soup.find("div", class_="cover-page")
        if popup is not None:
            msg = popup.find("h2").get_text().strip()
            if msg is not None:
                if msg == "Memorial has been merged":
                    merged = True
                    for p in popup.find_all("p"):
                        anchor = p.find("a")
                        if anchor is not None:
                            merged_url = p.find("a").get("href")
        return merged, merged_url

    @staticmethod
    def parse_name(soup):
        name = soup.find("h1", id="bio-name").get_text()
        name = name.replace("Famous memorial", "")
        name = name.replace("VVeteran", "")
        name = name.strip()
        return name

    @staticmethod
    def parse_maiden_name(name: str):
        # name = name.replace("/", "\/")
        result = None
        match = re.match(".*<I>(.*)</I>.*", name, re.IGNORECASE)
        if match is not None:
            result = match.group(1)
        return result

    @staticmethod
    def parse_birth(soup):
        birthdate = None
        result = soup.find("time", itemprop="birthDate")
        if result is not None:
            birthdate = result.get_text()
        return birthdate

    @staticmethod
    def parse_birth_place(soup):
        place = None
        result = soup.find("div", itemprop="birthPlace")
        if result is not None:
            place = result.get_text()
        return place

    @staticmethod
    def parse_death(soup):
        death_date = None
        result = soup.find("span", itemprop="deathDate")
        if result is not None:
            death_date = result.get_text().split("(")[0].strip()
        return death_date

    @staticmethod
    def parse_death_place(soup):
        place = None
        result = soup.find("div", itemprop="deathPlace")
        if result is not None:
            place = result.get_text()
        return place

    @staticmethod
    def parse_cemetery_id(soup):
        cem_id = None
        div = soup.find("div", itemtype=re.compile("https://schema.org/Cemetery"))
        if div is not None:
            anchor = div.find("a")
            href = anchor["href"]
            cem_id = int(re.match(".*/([0-9]+)/.*$", href).group(1))
        return cem_id

    @staticmethod
    def parse_coords(soup):
        """Returns Google Map coordinates, if any, as a string 'nn.nnnnnnn,nn.nnnnnn'"""
        latlon = None
        span = soup.find("span", itemtype=re.compile("https://schema.org/Map"))
        if span is not None:
            anchor = span.find("a")
            href = anchor["href"]
            # just for fun
            query = urlparse(href).query
            query_args = parse_qsl(query)
            name, latlon = query_args[0]
        return latlon

    @staticmethod
    def parse_burial_plot(soup):
        plot = None
        result = soup.find("span", id="plotValueLabel")
        if result is not None:
            plot = result.get_text()
        return plot

    @staticmethod
    def parse_more_info(soup):
        return False

    def parse(self, url):
        req = Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urlopen(req) as response:
            soup = BeautifulSoup(response.read(), "lxml")

        merged, newurl = self.check_merged(soup)
        if merged:
            msg = "{url} has been merged into {newurl}".format(url=url, newurl=newurl)
            raise MemorialMergedException(msg)

        url = MemorialParser.parse_canonical_link(soup)
        id = int(re.match(".*/([0-9]+)/.*$", url).group(1))
        name = MemorialParser.parse_name(soup)
        birth = MemorialParser.parse_birth(soup)
        birthplace = MemorialParser.parse_birth_place(soup)
        death = MemorialParser.parse_death(soup)
        deathplace = MemorialParser.parse_death_place(soup)
        burial = MemorialParser.parse_cemetery_id(soup)
        plot = MemorialParser.parse_burial_plot(soup)
        coords = MemorialParser.parse_coords(soup)
        more_info = MemorialParser.parse_more_info(soup)
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


class CemeteryParser(Parser):
    PAGE_URL = "http://www.findagrave.com/cemetery"
    NAME = "Cemetery Search"
    SEARCH_URL = "search?"

    def __init__(self):
        super().__init__(
            CemeteryParser.PAGE_URL, CemeteryParser.NAME, CemeteryParser.SEARCH_URL
        )

    @staticmethod
    def parse_name(soup):
        name = None
        result = soup.find("h1", itemprop="name")
        if result is not None:
            name = result.get_text().strip()
        return name

    @staticmethod
    def parse_location(soup):
        location = None
        result = soup.find("span", itemprop="addressLocality")
        if result is not None:
            locality = result.get_text().strip()
            result = soup.find("span", itemprop="addressRegion")
            if result is not None:
                region = result.get_text().strip()
                result = soup.find("span", itemprop="addressCountry")
                if result is not None:
                    country = result.get_text().strip()
                    location = locality + ", " + region + ", " + country
        return location

    @staticmethod
    def parse_coords(soup):
        result = soup.find("span", title="Latitude:")
        if result is not None:
            lat = result.get_text()
        result = soup.find("span", title="Longitude:")
        if result is not None:
            lon = result.get_text()
        coords = lat + "," + lon
        return coords

    def parse(self, url):
        """Parse the information from a cemetery information page.

        Args:
            url (str): A findagrave cemetery URL, e.g.:
            "https://www.findagrave.com/cemetery/12345/"
        """

        req = Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urlopen(req) as response:
            soup = BeautifulSoup(response.read(), "lxml")

        url = CemeteryParser.parse_canonical_link(soup)
        id = re.match("https://www.findagrave.com/cemetery/([0-9]+)/.*", url).group(1)
        name = CemeteryParser.parse_name(soup)
        location = CemeteryParser.parse_location(soup)
        coords = CemeteryParser.parse_coords(soup)
        return Cemetery(int(id), url, name, location, coords)
