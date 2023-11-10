from typing import NamedTuple

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


class TestParameters(NamedTuple):
    id: int
    url: str
    name: str
    birth: str
    birthplace: str
    death: str
    deathplace: str
    burial: str
    plot: str
    more_info: bool


# @pytest.mark.parametrized.expand([TestParameters(
#   id = 10101,
#   url= "http://www.findagrave.com/memorial/12345/",
#   name="John Smith",
#   birth="01 Jan 1959",
#   birth_place="Kansas City, Jackson, Missouri, USA",
#   death="20 Oct 1999",
#   deathplace="Reno, Washoe, Nevada, USA",
#   burial="Reno, Washoe, Nevada, USA",
#   plot="Garden of Memory, C1, Plot 54",
#   more_info=False
#   )
# ])
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
    grave = Memorial(
        id, url, name, birth, birthplace, death, deathplace, burial, plot, more_info
    )
    assert grave.id == id
    assert grave.url == url


def test_memorial_save():
    Memorial.create_table()
    memorial = Memorial(
        id=10101,
        url="http://www.findagrave.com/memorial/12345/",
        name="John Smith",
        birth="01 Jan 1959",
        birthplace="Kansas City, Jackson, Missouri, USA",
        death="20 Oct 1999",
        deathplace="Reno, Washoe, Nevada, USA",
        burial="Reno, Washoe, Nevada, USA",
        plot="Garden of Memory, C1, Plot 54",
        more_info=False,
    ).save()
    assert memorial is not None
