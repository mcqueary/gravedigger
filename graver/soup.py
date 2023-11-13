import logging as log
import re
from urllib.parse import parse_qsl, urlparse
from urllib.request import Request, urlopen

from bs4 import BeautifulSoup


def get_soup(url):
    req = Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urlopen(req) as response:
        try:
            soup = BeautifulSoup(response.read(), "lxml")
        except Exception as e:
            log.exception("The following error was thrown when reading this grave: ", e)
            raise
    return soup


def get_canonical_link(soup):
    link = soup.find("link", rel=re.compile("canonical"))["href"]
    return link


def get_id(soup):
    link = get_canonical_link(soup)
    return int(re.match(".*/([0-9]+)/.*$", link).group(1))


def get_name(soup):
    name = None
    try:
        name = soup.find("h1", id="bio-name").get_text()
        name = name.replace("Famous memorial", "")
        name = name.replace("VVeteran", "")
        name = name.strip()
        return name
    except Exception as e:
        log.exception(
            "The following error was thrown when getting the name from this grave: ", e
        )


def get_birth_date(soup):
    birthdate = None
    try:
        result = soup.find("time", itemprop="birthDate")
        if result is not None:
            birthdate = result.get_text()
            return birthdate
    except Exception as e:
        log.exception(
            "The following error was thrown when getting the birth date from this"
            " grave: ",
            e,
        )


def get_birth_place(soup):
    place = None
    try:
        result = soup.find("div", itemprop="birthPlace")
        if result is not None:
            place = result.get_text()
        return place
    except Exception as e:
        log.exception(
            "The following error was thrown when getting the birth place from this"
            " grave: ",
            e,
        )


def get_death_date(soup):
    death_date = None
    try:
        result = soup.find("span", itemprop="deathDate")
        if result is not None:
            death_date = result.get_text().split("(")[0].strip()

        return death_date
    except Exception as e:
        log.exception(
            "The following error was thrown when getting the death date from this"
            " grave: ",
            e,
        )


def get_death_place(soup):
    place = None
    try:
        result = soup.find("div", itemprop="deathPlace")
        if result is not None:
            place = result.get_text()
        return place
    except Exception as e:
        log.exception(
            "The following error was thrown when getting the death place from this"
            " grave: ",
            e,
        )


def get_cemetery_id(soup):
    div = soup.find("div", itemtype=re.compile("https://schema.org/Cemetery"))
    anchor = div.find("a")
    href = anchor["href"]
    cem_id = int(re.match(".*/([0-9]+)/.*$", href).group(1))
    return cem_id


def get_coords(soup):
    """Returns Google Map coordinates, if present, as a string 'nn.nnnnnnn,nn.nnnnnn'"""
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


def get_burial_plot(soup):
    plot = None
    try:
        result = soup.find("span", id="plotValueLabel")
        if result is not None:
            plot = result.get_text()
        return plot
    except Exception as e:
        log.exception(
            "The following error was thrown when getting the burial plot from this"
            " grave: ",
            e,
        )
