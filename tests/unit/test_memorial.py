import os
import pathlib

import pytest
from bs4 import BeautifulSoup

from graver.memorial import Memorial

soup = BeautifulSoup(open("./tests/unit/asimov.html"), "lxml")


def test_memorial():
    id = 10101
    url = "https://www.findagrave.com/memorial/12345/"
    name = "John Smith"
    birth = "01 Jan 1959"
    birthplace = "Kansas City, Jackson, Missouri, USA"
    death = "20 Oct 1999"
    deathplace = "Reno, Washoe, Nevada, USA"
    burial = "Reno, Washoe, Nevada, USA"
    plot = "Garden of Memory, C1, Plot 54"
    coords = "23.45678000, 12.9876543"
    more_info = False
    result = Memorial(
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
    assert result.id == id
    assert result.url == url
    assert result.name == name
    assert result.birth == birth
    assert result.birthplace == birthplace
    assert result.death == death
    assert result.deathplace == deathplace
    assert result.burial == burial
    assert result.plot == plot
    assert result.coords == coords
    assert result.more_info == more_info


asimov_abs_path = os.path.abspath("tests/unit/asimov.html")
asimov_uri = pathlib.Path(asimov_abs_path).as_uri()

shoulders_abs_path = os.path.abspath("tests/unit/shoulders.html")
shoulders_uri = pathlib.Path(shoulders_abs_path).as_uri()


@pytest.mark.parametrize(
    "url",
    [
        asimov_uri,
        shoulders_uri,
    ],
)
def test_memorial_scrape(url):
    memorial = Memorial.scrape(url)
    assert memorial is not None
    assert memorial.id is not None
    assert memorial.name is not None


@pytest.mark.parametrize(
    "id",
    [
        "78320781",
    ],
)
@pytest.mark.parametrize(
    "url",
    [
        "https://www.findagrave.com/memorial/78320781/dennis-macalistair-ritchie",
    ],
)
@pytest.mark.parametrize(
    "name",
    [
        "Dennis MacAlistair Ritchie",
    ],
)
@pytest.mark.parametrize("birth", ["9 Sep 1941"])
@pytest.mark.parametrize(
    "birthplace", ["Bronxville, Westchester County, New York, USA"]
)
@pytest.mark.parametrize("death", ["12 Oct 2011"])
@pytest.mark.parametrize(
    "deathplace", ["Berkeley Heights, Union County, New Jersey, USA"]
)
@pytest.mark.parametrize("burial", ["Burial Details Unknown"])
@pytest.mark.parametrize("plot", [None])
@pytest.mark.parametrize("coords", [None])
@pytest.mark.parametrize("more_info", [True])
def test_memorial_save(
    id, url, name, birth, birthplace, death, deathplace, burial, plot, coords, more_info
):
    Memorial.create_table()
    result = Memorial(
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
    ).save()

    assert result.id == id
    assert result.url == url
    assert result.name == name
    assert result.birth == birth
    assert result.birthplace == birthplace
    assert result.death == death
    assert result.deathplace == deathplace
    assert result.burial == burial
    assert result.plot == plot
    assert result.coords == coords
    assert result.more_info == more_info


def test_memorial_get_by_id():
    Memorial.create_table()
    expected = Memorial(
        10101,
        "http://www.findagrave.com/memorial/12345/",
        "John Smith",
        "01 Jan 1959",
        "Kansas City, Jackson, Missouri, USA",
        "20 Oct 1999",
        "Reno, Washoe, Nevada, USA",
        "Reno, Washoe, Nevada, USA",
        "Garden of Memory, C1, Plot 54",
        None,
        False,
    ).save()
    result = Memorial.get_by_id(10101)
    assert result == expected
