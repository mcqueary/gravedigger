import os
import pathlib

import pytest

from graver.parsers import MemorialParser

mixed_urls = [
    "https://www.findagrave.com/cemetery/53514",
    "https://www.findagrave.com/memorial/12345",
    "https://www.findagrave.com/cemetery/55276/memorial-search",
]

memorial_urls = [
    "https://www.findagrave.com/memorial/53514/john-smith",
    "https://www.findagrave.com/memorial/12345",
    "https://www.findagrave.com/memorial/54321/",
]

cemetery_urls = [
    "https://www.findagrave.com/cemetery/55276",
    "https://www.findagrave.com/cemetery/153/",
]

list_urls = [
    "https://www.findagrave.com/cemetery/55276/memorial-search",
    "https://www.findagrave.com/cemetery/153/memorial-search?",
]


# @pytest.mark.parametrize("url", mixed_urls)
# def test_page_url(url):
#     page = Page(url)
#     assert page is not None
#     assert page.url == url


# @pytest.mark.parametrize("url", mixed_urls)
# def test_page_type_not_none(url):
#     assert Page(url).type is not None


# @pytest.mark.parametrize("url", cemetery_urls)
# def test_cem_page(url):
#     page = CemeteryPage(url)
#     assert isinstance(page, CemeteryPage)
#     assert page.url == url

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
def test_memorial_parser_scrape(url):
    memorial = MemorialParser().parse(url)
    assert memorial is not None
