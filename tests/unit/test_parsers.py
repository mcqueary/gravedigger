from urllib.request import Request, urlopen

import pytest
from bs4 import BeautifulSoup

from definitions import ROOT_DIR
from graver.parsers import CemeteryParser, MemorialMergedException, MemorialParser

asimov_uri = pytest.helpers.to_uri(ROOT_DIR + "/tests/data/asimov.html")
shoulders_uri = pytest.helpers.to_uri(ROOT_DIR + "/tests/data/shoulders.html")
merged_uri = pytest.helpers.to_uri(ROOT_DIR + "/tests/data/merged.html")
maiden_uri = pytest.helpers.to_uri(ROOT_DIR + "/tests/data/dolores-maiden.html")
cem_3136_uri = pytest.helpers.to_uri(ROOT_DIR + "/tests/data/cem-3136.html")

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


@pytest.mark.parametrize(
    "url, expected",
    [
        (
            merged_uri,
            "https://www.findagrave.com/memorial/260829715/wiliam-henry-boekholder",
        )
    ],
)
def test_memorial_parser_check_merged(url, expected):
    # TODO figure out  better way to do this
    req = Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urlopen(req) as response:
        soup = BeautifulSoup(response.read(), "lxml")
    merged, new_url = MemorialParser.check_merged(soup)
    assert merged is True
    assert new_url == expected


@pytest.mark.parametrize("url", [merged_uri])
def test_memorial_parser_scrape_merged_raises_exception(url):
    with pytest.raises(MemorialMergedException, match="has been merged"):
        MemorialParser().parse(url)


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


@pytest.mark.parametrize("uri", [cem_3136_uri])
def test_cemetery_parser_parse_canonical_link(uri):
    req = Request(uri, headers={"User-Agent": "Mozilla/5.0"})
    with urlopen(req) as response:
        soup = BeautifulSoup(response.read(), "lxml")
    link = CemeteryParser.parse_canonical_link(soup)
    assert link == "https://www.findagrave.com/cemetery/3136/crown-hill-memorial-park"


@pytest.mark.parametrize("uri", [cem_3136_uri])
def test_cemetery_parser_scrape(uri):
    cem = CemeteryParser().parse(uri)
    assert cem.id == 3136
    assert cem.name == "Crown Hill Memorial Park"
    assert (
        cem.url == "https://www.findagrave.com/cemetery/3136/crown-hill-memorial-park"
    )
    assert cem.location == "Dallas, Dallas County, Texas, USA"
    assert cem.coords == "32.86780,-96.86220"
