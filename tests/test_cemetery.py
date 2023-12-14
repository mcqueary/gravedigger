import logging

import pytest
import vcr

from graver import Cemetery

logging.basicConfig()
vcr_log = logging.getLogger("vcr")
vcr_log.setLevel(logging.WARN)


@pytest.mark.parametrize(
    "expected",
    [
        pytest.helpers.load_cemetery_from_json("arlington-national-cemetery"),
        pytest.helpers.load_cemetery_from_json("crown-hill-memorial-park"),
        pytest.helpers.load_cemetery_from_json("monticello-graveyard"),
    ],
)
def test_cemetery_from_dict(expected: dict):
    cem = Cemetery.from_dict(expected)
    assert isinstance(cem, Cemetery)
    assert cem.cemetery_id == expected["cemetery_id"]
    assert cem.findagrave_url == expected["findagrave_url"]
    assert cem.name == expected["name"]
    assert cem.location == expected["location"]
    assert cem.coords == expected["coords"]


@pytest.mark.parametrize(
    "expected",
    [
        pytest.helpers.load_cemetery_from_json("arlington-national-cemetery"),
        pytest.helpers.load_cemetery_from_json("crown-hill-memorial-park"),
        pytest.helpers.load_cemetery_from_json("monticello-graveyard"),
    ],
)
def test_cemetery_to_dict(expected: dict):
    c: Cemetery = Cemetery.from_dict(expected)
    assert isinstance(c, Cemetery)
    result = c.to_dict()
    assert result["cemetery_id"] == expected["cemetery_id"]
    assert result["findagrave_url"] == expected["findagrave_url"]
    assert result["name"] == expected["name"]
    assert result["location"] == expected["location"]
    assert result["coords"] == expected["coords"]


@pytest.mark.parametrize(
    "expected, cassette",
    [
        (
            pytest.helpers.load_cemetery_from_json("crown-hill-memorial-park"),
            pytest.vcr_cassettes + "crown-hill-memorial-park.yaml",
        )
    ],
)
def test_cemetery(expected, cassette):
    with vcr.use_cassette(cassette):
        url = expected["findagrave_url"]
        cem = Cemetery(url)
        assert cem.cemetery_id == expected["cemetery_id"]
        assert cem.name == expected["name"]
        assert cem.findagrave_url == expected["findagrave_url"]
        assert cem.location == expected["location"]
        assert cem.coords == expected["coords"]

        # Test equality
        cem2 = Cemetery(url)
        assert cem == cem2
        cem3 = Cemetery(url)

        # test for class inequality
        assert cem3 != 42
        # test for instance inequality
        cem3.cemetery_id = 41405
        assert cem3 != cem2


@vcr.use_cassette(pytest.vcr_cassettes + "cemetery-monticello-graveyard.yaml")
@pytest.mark.parametrize(
    (
        "url",
        "num_expected",
    ),
    [("https://www.findagrave.com/cemetery/641519/monticello-graveyard", 270)],
)
def test_cemetery_get_num_memorials(url: str, num_expected: int):
    count = Cemetery(url).get_num_memorials()
    assert count == num_expected
