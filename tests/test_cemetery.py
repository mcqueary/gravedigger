from urllib.error import HTTPError

import pytest

from definitions import ROOT_DIR
from graver.cemetery import Cemetery, Driver

mixed_urls = [
    "https://www.findagrave.com/cemetery/53514",
    "https://www.findagrave.com/memorial/12345",
    "https://www.findagrave.com/cemetery/55276/memorial-search",
]

cemetery_urls = [
    "https://www.findagrave.com/cemetery/55276",
    "https://www.findagrave.com/cemetery/153/",
]

list_urls = [
    "https://www.findagrave.com/cemetery/55276/memorial-search",
    "https://www.findagrave.com/cemetery/153/memorial-search?",
]

cem_3136_uri = pytest.helpers.to_uri(ROOT_DIR + "/tests/data/cem-3136.html")

cem_fake: dict = {
    "_id": 41404,
    "findagrave_url": "https://www.findagrave.com/cemetery/41404",
    "name": "My Fake Cemetery",
    "location": "Dallas, Dallas, Texas, USA",
    "coords": "38.8775405, -77.0654917",
}


@pytest.mark.parametrize("expected", [cem_fake])
def test_cemetery_from_dict(expected: dict):
    cem = Cemetery.from_dict(expected)
    assert cem._id == expected["_id"]
    assert cem.findagrave_url == expected["findagrave_url"]
    assert cem.name == expected["name"]
    assert cem.location == expected["location"]
    assert cem.coords == expected["coords"]


@pytest.mark.parametrize("expected", [cem_fake])
def test_cemetery_to_dict(expected: dict):
    c = Cemetery.from_dict(expected)
    result = c.to_dict()
    assert result["_id"] == expected["_id"]
    assert result["findagrave_url"] == expected["findagrave_url"]
    assert result["name"] == expected["name"]
    assert result["location"] == expected["location"]
    assert result["coords"] == expected["coords"]


@pytest.mark.parametrize("uri", [cem_3136_uri])
def test_cemetery(uri):
    cem = Cemetery(uri)
    cem2 = Cemetery(uri)
    assert cem == cem2
    cem3 = Cemetery(uri, get=False, scrape=False)
    cem3._id = 41405
    # test for class inequality
    assert cem3 != 42
    # test for instance inequality
    assert cem3 != cem2

    assert cem._id == 3136
    assert cem.name == "Crown Hill Memorial Park"
    assert (
        cem.findagrave_url
        == "https://www.findagrave.com/cemetery/3136/crown-hill-memorial-park"
    )
    assert cem.location == "Dallas, Dallas County, Texas, USA"
    assert cem.coords == "32.86780,-96.86220"


@pytest.mark.integration_test
@pytest.mark.parametrize(
    "findagrave_url", ["https://www.findagrave.com/should-produce-404"]
)
def test_memorial_driver_raises_http_error(findagrave_url):
    with pytest.raises(Exception) as e:
        Driver.get(findagrave_url)
    assert e.errisinstance(HTTPError)
    assert e.value.code == 404
