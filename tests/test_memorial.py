from urllib.error import HTTPError

import pytest

from definitions import ROOT_DIR
from graver.memorial import Driver, Memorial, MemorialMergedException, NotFound

merged_uri = pytest.helpers.to_uri(ROOT_DIR + "/tests/data/merged.html")
asimov_uri = pytest.helpers.to_uri(ROOT_DIR + "/tests/data/asimov.html")
hopper_uri = pytest.helpers.to_uri(ROOT_DIR + "/tests/data/hopper.html")
shoulders_uri = pytest.helpers.to_uri(ROOT_DIR + "/tests/data/shoulders.html")
maiden_uri = pytest.helpers.to_uri(ROOT_DIR + "/tests/data/dolores-maiden.html")
cem_3136_uri = pytest.helpers.to_uri(ROOT_DIR + "/tests/data/cem-3136.html")
ritchie_uri = pytest.helpers.to_uri(ROOT_DIR + "/tests/data/ritchie.html")

person_gh: dict = {
    "_id": 1784,
    "findagrave_url": "https://www.findagrave.com/memorial/1784/grace-brewster-hopper",
    "name": "RADM Grace Brewster Hopper",
    "maiden_name": "Murray",
    "birth": "9 Dec 1906",
    "birthplace": "New York, New York County, New York, USA",
    "death": "1 Jan 1992",
    "deathplace": "Arlington, Arlington County, Virginia, USA",
    "burial": "Arlington, Arlington County, Virginia, USA",
    "plot": "Section 59, Grave 973, Map grid FF 24.5",
    "coords": "38.8775405, -77.0654917",
    "more_info": True,
}
person_dmr: dict = {
    "_id": 78320781,
    "findagrave_url": ritchie_uri,
    "name": "Dennis MacAlistair Ritchie",
    "maiden_name": None,
    "birth": "9 Sep 1941",
    "birthplace": "Bronxville, Westchester County, New York, USA",
    "death": "12 Oct 2011",
    "deathplace": "Berkeley Heights, Union County, New Jersey, USA",
    "burial": "Burial Details Unknown",
    "plot": None,
    "coords": None,
    "more_info": True,
}
people: list = [person_gh, person_dmr]


@pytest.mark.parametrize(
    "findagrave_url",
    [
        asimov_uri,
        shoulders_uri,
    ],
)
def test_memorial(findagrave_url):
    memorial = Memorial(findagrave_url)
    assert memorial is not None
    # test class inequality
    assert memorial != 42


@pytest.mark.parametrize("expected", people)
def test_memorial_from_dict(expected: dict):
    result = Memorial.from_dict(expected)
    assert result._id == expected["_id"]
    assert result.findagrave_url == expected["findagrave_url"]
    assert result.name == expected["name"]
    assert result.maiden_name == expected["maiden_name"]
    assert result.birth == expected["birth"]
    assert result.birthplace == expected["birthplace"]
    assert result.death == expected["death"]
    assert result.deathplace == expected["deathplace"]
    assert result.burial == expected["burial"]
    assert result.plot == expected["plot"]
    assert result.coords == expected["coords"]
    assert result.more_info == expected["more_info"]


@pytest.mark.parametrize("expected", people)
def test_memorial_to_dict(expected: dict):
    m = Memorial.from_dict(expected)
    result = m.to_dict()
    assert result["_id"] == expected["_id"]
    assert result["findagrave_url"] == expected["findagrave_url"]
    assert result["name"] == expected["name"]
    if "maiden_name" in expected:
        assert "maiden_name" in result
        assert result["maiden_name"] == expected["maiden_name"]
    assert result["birth"] == expected["birth"]
    assert result["birthplace"] == expected["birthplace"]
    assert result["death"] == expected["death"]
    assert result["deathplace"] == expected["deathplace"]
    assert result["burial"] == expected["burial"]
    assert result["plot"] == expected["plot"]
    assert result["coords"] == expected["coords"]
    assert result["more_info"] == expected["more_info"]


@pytest.mark.parametrize("expected", people)
def test_memorial_save(expected: dict):
    result = Memorial.from_dict(expected).save()
    assert result._id == expected["_id"]
    assert result.findagrave_url == expected["findagrave_url"]
    assert result.name == expected["name"]
    assert result.birth == expected["birth"]
    assert result.birthplace == expected["birthplace"]
    assert result.death == expected["death"]
    assert result.deathplace == expected["deathplace"]
    assert result.burial == expected["burial"]
    assert result.plot == expected["plot"]
    assert result.coords == expected["coords"]
    assert result.more_info == expected["more_info"]


@pytest.mark.parametrize("expected", people)
def test_memorial_get_by_id(expected: dict):
    id: int = expected["_id"]
    expected_memorial = Memorial.from_dict(expected).save()
    result = Memorial.get_by_id(id)
    assert result == expected_memorial


@pytest.mark.parametrize("findagrave_url", [maiden_uri])
def test_memorial_get_maiden_name(findagrave_url):
    # TODO figure out better way to do this with a fixture
    m = Memorial(findagrave_url)
    assert m.maiden_name is not None
    assert m.maiden_name == "Smith"


@pytest.mark.parametrize("findagrave_url", [merged_uri])
def test_memorial_merged(findagrave_url):
    m = Memorial(findagrave_url, scrape=False)
    merged, new_url = m.check_merged()
    assert merged is True


@pytest.mark.parametrize("findagrave_url", [merged_uri])
def test_memorial_merged_raises_exception(findagrave_url):
    with pytest.raises(MemorialMergedException, match="has been merged"):
        Memorial(findagrave_url)


@pytest.mark.parametrize("findagrave_url", [hopper_uri])
def test_memorial_with_coords(findagrave_url):
    m = Memorial(findagrave_url)
    assert m.coords is not None
    assert m.coords != ""


@pytest.mark.parametrize("_id", [99999, -12345])
def test_memorial_by_id_not_found(_id):
    with pytest.raises(NotFound):
        Memorial.get_by_id(_id)


@pytest.mark.integration_test
@pytest.mark.parametrize(
    "findagrave_url", ["https://www.findagrave.com/should-produce-404"]
)
def test_memorial_driver_raises_http_error(findagrave_url):
    with pytest.raises(Exception) as e:
        Driver.get(findagrave_url)
    assert e.errisinstance(HTTPError)
    assert e.value.code == 404


@pytest.mark.integration_test
@pytest.mark.parametrize(
    "url",
    [
        "https://secure.findagrave.com/cgi-bin/fg.cgi?page=gr&GRid=534",
        "https://www.findagrave.com/memorial/534",
    ],
)
def test_memorial_live(url):
    memorial = Memorial(url)
    assert memorial._id == 534
    assert memorial.name == "Andrew Jackson"
