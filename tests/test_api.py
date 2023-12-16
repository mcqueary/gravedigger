import logging
import re

import pytest
import requests
import vcr
from requests import HTTPError

import graver.api
from graver import (
    Cemetery,
    Driver,
    Memorial,
    MemorialMergedException,
    MemorialRemovedException,
)

logging.basicConfig()
vcr_log = logging.getLogger("vcr")
vcr_log.setLevel(logging.WARN)


def get_cassette(name: str):
    return f"{pytest.vcr_cassettes}{name}.yaml"


memorials = [
    "andrew-jackson",
    "carl-sagan",
    "dennis-macalistair-ritchie",
    "george-washington",
    "grace-brewster-hopper",
    "isaac-asimov",
    "john-j-pershing",
    "john-quincy-adams",
    "martin-luther-king",
    "rod-serling",
    "thomas-jefferson",
]

famous_memorials = [
    "andrew-jackson",
    "carl-sagan",
    "george-washington",
    "grace-brewster-hopper",
    "isaac-asimov",
    "john-j-pershing",
    "martin-luther-king",
    "rod-serling",
    "thomas-jefferson",
]


def test_vcr():
    with vcr.use_cassette(pytest.vcr_cassettes + "synopsis.yaml"):
        response = requests.get("http://www.iana.org/domains/reserved")
        assert b"Example domains" in response.content


@pytest.mark.parametrize("url", ["https://www.findagrave.com/memorial/544"])
@pytest.mark.parametrize(
    "status_code, reason",
    [
        (500, "Internal Server Error"),
        (502, "Bad Gateway"),
        (503, "Service Unavailable"),
        (504, "Gateway Timeout"),
        (599, "Network Connect Timeout Error"),
    ],
)
def test_driver_retries_recoverable_errors(url, status_code, reason, requests_mock):
    requests_mock.get(
        url,
        [
            {"status_code": status_code, "reason": reason},
            {"status_code": 200, "reason": "None"},
        ],
    )
    driver = Driver(retry_ms=10, max_retries=1)
    response = driver.get(url)
    assert response.ok and response.status_code == 200
    assert driver.num_retries == 1


@pytest.mark.parametrize(
    "url, cassette",
    [
        (
            "https://www.findagrave.com/memorial/should-produce-404",
            pytest.vcr_cassettes + "404-memorial.yaml",
        ),
        (
            "https://www.findagrave.com/cemetery/should-produce-404",
            pytest.vcr_cassettes + "404-cemetery.yaml",
        ),
    ],
)
def test_driver_raises_http_error(url, cassette):
    # FIXME
    with vcr.use_cassette(cassette):
        with pytest.raises(HTTPError) as excinfo:
            Memorial.parse(url)
        assert "404 Client Error: Not Found" in excinfo.value.args[0]


@pytest.mark.parametrize("name", memorials)
def test_memorial_parse(
    name: str,
):
    mem_dict = pytest.helpers.load_memorial_from_json(name)
    cassette = get_cassette(name)
    with vcr.use_cassette(cassette):
        m = Memorial.parse(mem_dict["findagrave_url"])
        assert isinstance(m, Memorial)
        expected_m = Memorial.from_dict(mem_dict)
        assert m == expected_m


@pytest.mark.parametrize("name", memorials)
def test_memorial_from_dict(name: str):
    expected = pytest.helpers.load_memorial_from_json(name)
    result = Memorial.from_dict(expected)
    assert result.memorial_id == expected["memorial_id"]
    assert result.findagrave_url == expected["findagrave_url"]
    if "prefix" in expected.keys():
        assert result.prefix == expected["prefix"]
    else:
        assert result.prefix is None
    assert result.name == expected["name"]
    if "suffix" in expected.keys():
        assert result.suffix == expected["suffix"]
    else:
        assert result.suffix is None
    assert result.maiden_name == expected["maiden_name"]
    assert result.original_name == expected["original_name"]
    assert result.famous == expected["famous"]
    assert result.veteran == expected["veteran"]
    assert result.birth == expected["birth"]
    assert result.birth_place == expected["birth_place"]
    assert result.death == expected["death"]
    assert result.death_place == expected["death_place"]
    assert result.memorial_type == expected["memorial_type"]
    assert result.plot == expected["plot"]
    assert result.coords == expected["coords"]
    assert result.has_bio == expected["has_bio"]


@pytest.mark.parametrize("name", memorials)
def test_memorial_to_dict(name: str):
    expected = pytest.helpers.load_memorial_from_json(name)
    m = Memorial.from_dict(expected)
    result = m.to_dict()
    assert result["memorial_id"] == expected["memorial_id"]
    assert result["findagrave_url"] == expected["findagrave_url"]
    assert result["name"] == expected["name"]
    if "maiden_name" in expected:
        assert "maiden_name" in result
        assert result["maiden_name"] == expected["maiden_name"]
    assert result["original_name"] == expected["original_name"]
    assert result["famous"] == expected["famous"]
    assert result["veteran"] == expected["veteran"]
    assert result["birth"] == expected["birth"]
    assert result["birth_place"] == expected["birth_place"]
    assert result["death"] == expected["death"]
    assert result["death_place"] == expected["death_place"]
    assert result["memorial_type"] == expected["memorial_type"]
    assert result["plot"] == expected["plot"]
    assert result["coords"] == expected["coords"]
    assert result["has_bio"] == expected["has_bio"]


@pytest.mark.parametrize("name", memorials)
def test_memorial_save(name: str, database):
    expected = pytest.helpers.load_memorial_from_json(name)
    result = Memorial.from_dict(expected).save()
    assert result.memorial_id == expected["memorial_id"]
    assert result.findagrave_url == expected["findagrave_url"]
    assert result.name == expected["name"]
    assert result.original_name == expected["original_name"]
    assert result.birth == expected["birth"]
    assert result.birth_place == expected["birth_place"]
    assert result.death == expected["death"]
    assert result.death_place == expected["death_place"]
    assert result.memorial_type == expected["memorial_type"]
    assert result.plot == expected["plot"]
    assert result.coords == expected["coords"]
    assert result.has_bio == expected["has_bio"]


@pytest.mark.parametrize("name", memorials)
def test_memorial_get_by_id(name: str, database):
    expected = pytest.helpers.load_memorial_from_json(name)
    mid: int = expected["memorial_id"]
    expected_memorial = Memorial.from_dict(expected).save()
    result: Memorial = Memorial.get_by_id(mid)
    assert result == expected_memorial


@pytest.mark.parametrize("memorial_id", [99999, -12345])
def test_memorial_by_id_not_found(memorial_id, database):
    with pytest.raises(graver.api.NotFound):
        Memorial.get_by_id(memorial_id)


@vcr.use_cassette(
    pytest.vcr_cassettes + "test_memorial_parser_merged_raises_exception.yaml"
)
@pytest.mark.parametrize(
    "requested_url, new_url",
    [
        (
            "https://www.findagrave.com/memorial/244781332/william-h-boekholder",
            "https://www.findagrave.com/memorial/260829715/wiliam-henry-boekholder",
        )
    ],
)
def test_memorial_parser_merged_raises_exception(requested_url, new_url):
    with pytest.raises(MemorialMergedException, match="has been merged") as ex_info:
        Memorial.parse(requested_url)
    assert ex_info.value.new_url == new_url


@vcr.use_cassette(
    pytest.vcr_cassettes + "test_memorial_parser_removed_raises_exception.yaml"
)
@pytest.mark.parametrize(
    "findagrave_url",
    [
        "https://www.findagrave.com/memorial/261491035/dolores-higginbotham",
    ],
)
def test_memorial_parser_removed_raises_exception(findagrave_url):
    with pytest.raises(MemorialRemovedException, match="has been removed"):
        Memorial.parse(findagrave_url)


@pytest.mark.parametrize(
    "person, cassette",
    [
        (
            pytest.helpers.load_memorial_from_json("james-fenimore-cooper"),
            pytest.vcr_cassettes + "james-fenimore-cooper-search-results.yaml",
        ),
        (
            pytest.helpers.load_memorial_from_json("john-j-pershing"),
            pytest.vcr_cassettes + "john-j-pershing-search-results.yaml",
        ),
    ],
)
def test_search(person: dict, cassette):
    with vcr.use_cassette(cassette):
        names = person["name"].split(" ")
        first_name = names[0]
        middle_name = ""
        last_name = names[len(names) - 1]
        if len(names) > 2:
            middle_name = names[1]

        birth_year: str = person["birth"][-4:]
        death_year: str = person["death"][-4:]
        results = Memorial.search(
            firstname=first_name,
            middlename=middle_name,
            lastname=last_name,
            birthyear=birth_year,
            deathyear=death_year,
            max_results=1,
        )
        assert results is not None
        assert len(results) == 1
        for result in results:
            assert first_name in result.name
            assert middle_name in result.name
            assert last_name in result.name
            assert birth_year == result.birth[-4:]
            assert death_year == result.death[-4:]
            assert result.nickname == person["nickname"]


@vcr.use_cassette(pytest.vcr_cassettes + "test_search_max_results.yaml")
@pytest.mark.parametrize(
    "args, expected", [({"lastname": "Jackson", "max_results": 37}, 37)]
)
def test_search_max_results(args, expected):
    logging.getLogger().setLevel(logging.DEBUG)
    rs = Memorial.search(**args)
    assert 0 < len(rs) <= expected
    pass


@pytest.mark.parametrize("name", famous_memorials)
def test_search_famous_people(name: str):
    person = pytest.helpers.load_memorial_from_json(name)
    cassette = get_cassette(f"test_search_famous_people-{name}")
    with vcr.use_cassette(cassette):
        parts = person["name"].split(" ")
        first = parts[0]
        last = parts[len(parts) - 1]
        if len(parts) > 2:
            middle = parts[1]
        else:
            middle = ""

        patt = re.compile(r"\d{4}$")
        birth_year = re.search(patt, person["birth"]).group(0)
        death_year = re.search(patt, person["death"]).group(0)
        results = Memorial.search(
            firstname=first,
            middlename=middle,
            lastname=last,
            birthyear=birth_year,
            deathyear=death_year,
            famous=True,
        )
        assert len(results) >= 1
        assert (m := results[0]) is not None
        assert isinstance(m, Memorial)
        assert m.memorial_id == person["memorial_id"]
        assert first in m.name
        if middle != "":
            assert middle in m.name
        assert last in m.name
        assert birth_year in m.birth
        assert death_year in m.death
        assert m.famous


@vcr.use_cassette(pytest.vcr_cassettes + "test_search_empty.yaml")
def test_search_empty():
    results = Memorial.search()
    assert len(results) == 0


@pytest.mark.parametrize(
    "cemetery_url, cassette",
    [
        (
            "https://www.findagrave.com/cemetery/641519",
            pytest.vcr_cassettes + "test-search-monticello-cemetery-famous-vets.yaml",
        )
    ],
)
def test_search_cemetery_famous_veterans(cemetery_url, cassette):
    with vcr.use_cassette(cassette):
        c = Cemetery(cemetery_url)
        results = Memorial.search(c, famous="true", isVeteran="true")
        assert results is not None
        assert len(results) > 0
        for m in results:
            assert m.famous
            assert m.veteran


@pytest.mark.parametrize(
    ("cemetery_url", "cemetery_cassette", "results_cassette", "expected_count"),
    [
        (
            "https://www.findagrave.com/cemetery/641519/monticello-graveyard",
            pytest.vcr_cassettes + "cemetery-monticello-graveyard.yaml",
            pytest.vcr_cassettes + "test-search-cemetery-monticello-vets.yaml",
            18,
        )
    ],
)
def test_cemetery_search(
    cemetery_url, cemetery_cassette, results_cassette, expected_count
):
    with vcr.use_cassette(cemetery_cassette):
        cem = Cemetery(cemetery_url)
    with vcr.use_cassette(results_cassette):
        results = Memorial.search(cem, isVeteran=True)
        assert results is not None
        assert len(results) == expected_count


@vcr.use_cassette(pytest.vcr_cassettes + "test_cemetery_search_max_results.yaml")
@pytest.mark.parametrize(
    "url, max_results", [("https://www.findagrave.com/cemetery/641519", 37)]
)
def test_cemetery_search_max_results(url, max_results):
    rs = Memorial.search(Cemetery(url), max_results=max_results)
    assert len(rs) == max_results


@vcr.use_cassette(
    pytest.vcr_cassettes + "test_cemetery_search_identifies_memorial_type_monument.yaml"
)
def test_cemetery_search_identifies_memorial_type_monument():
    cem = Cemetery("https://www.findagrave.com/cemetery/1990395/honolulu-memorial")
    rs = Memorial.search(cem, firstname="Adrian", lastname="Williams")
    assert len(rs) == 1
    m = rs[0]
    assert isinstance(m, Memorial)
    assert m.memorial_type == "Monument"


@vcr.use_cassette(
    pytest.vcr_cassettes + "test_cemetery_search_identifies_memorial_type_cenotaph.yaml"
)
def test_cemetery_search_identifies_memorial_type_cenotaph():
    cem = Cemetery("https://www.findagrave.com/cemetery/1990395/honolulu-memorial")
    rs = Memorial.search(cem, firstname="Harold", lastname="Costill")
    assert len(rs) == 1
    m = rs[0]
    assert isinstance(m, Memorial)
    assert m.memorial_type == "Cenotaph"


@pytest.mark.parametrize(
    "cem_url, cassette",
    [
        (
            "https://www.findagrave.com/cemetery/49269/arlington-national-cemetery",
            pytest.vcr_cassettes + "arlington-national-cemetery-search-results.yaml",
        )
    ],
)
def test_cemetery_search_multi_page(cem_url, cassette):
    with vcr.use_cassette(cassette):
        rs = Memorial.search(Cemetery(cem_url), max_results=40)
        assert len(rs) == 40


@pytest.mark.parametrize(
    ("url", "expected_name", "expected_id", "cassette"),
    [
        (
            "https://www.findagrave.com/cemetery/2783285/rachel-levy-gravesite",
            "Rachel Machado Levy",
            257624726,
            pytest.vcr_cassettes
            + "test_cemetery_search_all-rachel-levy-gravesite.yaml",
        )
    ],
)
def test_cemetery_search_all(url, expected_name, expected_id, cassette):
    with vcr.use_cassette(cassette):
        cem = Cemetery(url)
        assert cem.num_memorials > 0
        results = Memorial.search(cem)
        assert len(results) == cem.num_memorials
        m: Memorial = results[0]
        assert m.name == expected_name
        assert m.memorial_id == expected_id


@pytest.mark.parametrize(
    "cemetery_url, cemetery_id, page_num",
    [("https://www.findagrave.com/cemetery/641519", 641519, 3)],
)
def test_cemetery_search_specific_page(cemetery_url, cemetery_id, page_num):
    with vcr.use_cassette(
        pytest.vcr_cassettes
        + f"test_cemetery_search-cemetery-{cemetery_id}-p{page_num}.yaml"
    ):
        rs = Memorial.search(Cemetery(cemetery_url), page=page_num)
        assert len(rs) == 20
        assert f"page={page_num}" in rs.source
