import logging as log
import urllib.error
import urllib.request
from urllib.request import Request, urlopen

from bs4 import BeautifulSoup


def get_soup(url):
    req = Request(url, headers={"User-Agent": "Mozilla/5.0"})
    # trunk-ignore(bandit/B310)
    with urlopen(req) as response:
        try:
            soup = BeautifulSoup(response.read(), "lxml")
        except urllib.error.HTTPError as err:
            log.exception(
                "An HTTPError was thrown when reading id "
                f"{url}: {err.code} {err.reason}"
            )
            raise
        except Exception as e:
            log.exception("The following error was thrown when reading this grave: ", e)
            raise
    return soup


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
