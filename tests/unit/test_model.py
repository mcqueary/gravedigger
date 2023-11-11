import os
import pathlib

import pytest
from bs4 import BeautifulSoup

from graver.models import Memorial, Page, PageType

soup = BeautifulSoup(open("./tests/unit/asimov.html"), "lxml")

mixed_urls = [
    "https://www.findagrave.com/cemetery/53514",
    "https://www.findagrave.com/memorial/12345",
    "https://www.findagrave.com/cemetery/55276/memorial-search",
]


@pytest.mark.parametrize("url", mixed_urls)
def test_page_url(url):
    page = Page(url)
    assert page is not None
    assert page.url == url


@pytest.mark.parametrize("url", mixed_urls)
def test_page_type_not_none(url):
    assert Page(url).type is not None


memorial_urls = [
    "https://www.findagrave.com/memorial/53514/john-smith",
    "https://www.findagrave.com/memorial/12345",
    "https://www.findagrave.com/memorial/54321/",
]


@pytest.mark.parametrize("url", memorial_urls)
def test_page_is_memorial(url):
    assert Page(url).type is PageType.MEMORIAL


cemetery_urls = [
    "https://www.findagrave.com/cemetery/55276",
    "https://www.findagrave.com/cemetery/153/",
]


@pytest.mark.parametrize("url", cemetery_urls)
def test_page_is_cemetery(url):
    assert Page(url).type is PageType.CEMETERY


list_urls = [
    "https://www.findagrave.com/cemetery/55276/memorial-search",
    "https://www.findagrave.com/cemetery/153/memorial-search?",
]


@pytest.mark.parametrize("url", list_urls)
def test_page_is_list(url):
    assert Page(url).type is PageType.LIST


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
    more_info = False
    result = Memorial(
        id, url, name, birth, birthplace, death, deathplace, burial, plot, more_info
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
@pytest.mark.parametrize("more_info", [True])
def test_memorial_save(
    id, url, name, birth, birthplace, death, deathplace, burial, plot, more_info
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
        False,
    ).save()
    result = Memorial.get_by_id(10101)
    assert result == expected
