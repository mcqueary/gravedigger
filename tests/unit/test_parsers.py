import os
import pathlib
from urllib.request import Request, urlopen

import pytest
from bs4 import BeautifulSoup

from graver.parsers import MemorialMergedException, MemorialParser

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


merged_abs_path = os.path.abspath("tests/unit/merged.html")
merged_uri = pathlib.Path(merged_abs_path).as_uri()


@pytest.mark.parametrize("url", [merged_uri])
def test_memorial_parser_check_merged(url):
    # TODO figure out  better way to do this
    req = Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urlopen(req) as response:
        soup = BeautifulSoup(response.read(), "lxml")
    merged, new_url = MemorialParser.check_merged(soup)
    assert merged is True
    assert (
        new_url
        == "https://www.findagrave.com/memorial/260829715/wiliam-henry-boekholder"
    )


@pytest.mark.parametrize("url", [merged_uri])
def test_memorial_parser_scrape_merged_raises_exception(url):
    with pytest.raises(MemorialMergedException, match="has been merged"):
        MemorialParser().parse(url)


maiden_abs_path = os.path.abspath("tests/unit/dolores-maiden.html")
maiden_uri = pathlib.Path(maiden_abs_path).as_uri()


# @pytest.mark.parametrize("url", [maiden_uri])
def test_memorial_parser_parse_maiden_name():
    # TODO figure out better way to do this with a fixture
    # req = Request(url, headers={"User-Agent": "Mozilla/5.0"})
    # with urlopen(req) as response:
    #     soup = BeautifulSoup(response.read(), "lxml")
    maiden = MemorialParser.parse_maiden_name("Dolores <I>Smith</I> Higginbotham")
    assert maiden == "Smith"
    maiden = MemorialParser.parse_maiden_name("Dolores <i>Smith</i> Higginbotham")
    assert maiden == "Smith"
    maiden = MemorialParser.parse_maiden_name("Dolores <i>Bar-Baz</i> Higginbotham")
    assert maiden == "Bar-Baz"
    maiden = MemorialParser.parse_maiden_name("Dolores <i>Bar/Baz</i> Higginbotham")
    assert maiden == "Bar/Baz"
    maiden = MemorialParser.parse_maiden_name("Dolores Higginbotham")
    assert maiden is None
