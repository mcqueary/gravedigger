import pytest

from graver.memorial import Memorial

person_js: dict = {
    "id": 12345,
    "url": "https://www.findagrave.com/memorial/12345/",
    "name": "John Smith",
    "birth": "01 Jan 1959",
    "birthplace": "Kansas City, Jackson, Missouri, USA",
    "death": "20 Oct 1999",
    "deathplace": "Reno, Washoe, Nevada, USA",
    "burial": "Reno, Washoe, Nevada, USA",
    "plot": "Garden of Memory, C1, Plot 54",
    "coords": "23.45678000, 12.9876543",
    "more_info": False,
}
person_dmr: dict = {
    "id": 78320781,
    "url": "https://www.findagrave.com/memorial/78320781/dennis-macalistair-ritchie",
    "name": "Dennis MacAlistair Ritchie",
    "birth": "9 Sep 1941",
    "birthplace": "Bronxville, Westchester County, New York, USA",
    "death": "12 Oct 2011",
    "deathplace": "Berkeley Heights, Union County, New Jersey, USA",
    "burial": "Burial Details Unknown",
    "plot": None,
    "coords": None,
    "more_info": True,
}
people: list = [person_js, person_dmr]


@pytest.mark.parametrize("expected", people)
def test_memorial_from_dict(expected: dict):
    result = Memorial.from_dict(expected)
    assert result.id == expected["id"]
    assert result.url == expected["url"]
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
def test_memorial_save(expected: dict):
    result = Memorial.from_dict(expected).save()
    assert result.id == expected["id"]
    assert result.url == expected["url"]
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
    id: int = expected["id"]
    expected_memorial = Memorial.from_dict(expected).save()
    result = Memorial.get_by_id(id)
    assert result == expected_memorial
