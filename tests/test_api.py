import json
import logging
import re
from typing import Any

import pytest
import requests
from urllib3 import exceptions

import graver.api
from graver import (
    Cemetery,
    Driver,
    Memorial,
    MemorialMergedException,
    MemorialParseException,
    MemorialRemovedException,
)
from tests.test import Test


logging.getLogger().setLevel(logging.INFO)


class TestApi(Test):
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


class TestDriver(TestApi):
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
    def test_driver_retries_recoverable_errors(
        self, url, status_code, reason, requests_mock
    ):
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
        "url", ["https://www.findagrave.com/memorial/7/john-quincy-adams"]
    )
    def test_driver_unrecoverable_http_error(self, url, helpers, requests_mock):
        requests_mock.reset()
        requests_mock.get(
            url,
            [
                {"status_code": 403, "reason": "Forbidden"},
            ],
        )
        with pytest.raises(
            MemorialParseException, match=f"403 Client Error: Forbidden for url: {url}"
        ):
            Memorial.parse(url)

    @pytest.mark.parametrize(
        "url", ["https://www.findagrave.com/memorial/7/john-quincy-adams"]
    )
    def test_driver_unrecoverable_requests_error(
        self, url, helpers, caplog, requests_mock
    ):
        requests_mock.reset()
        requests_mock.get(
            url,
            exc=requests.exceptions.ConnectTimeout(
                exceptions.MaxRetryError(None, url, None), None
            ),
        )
        with pytest.raises(MemorialParseException, match="Max retries exceeded"):
            Memorial.parse(url)


class TestMemorial(TestApi):
    pass

    def test_memorial_not_equal_different_class(self):
        m = Memorial.from_dict(Test.load_memorial_from_json("james-fenimore-cooper"))
        assert m != str("A string object")

    @pytest.mark.parametrize("name", TestApi.memorials)
    def test_memorial_parse(self, name: str, driver):
        mem_dict = Test.load_memorial_from_json(name)
        m = Memorial.parse(mem_dict["findagrave_url"], driver=driver)
        assert isinstance(m, Memorial)
        expected_m = Memorial.from_dict(mem_dict)
        assert m == expected_m

    @pytest.mark.parametrize("name", TestApi.memorials)
    def test_memorial_from_dict(self, name: str):
        expected = Test.load_memorial_from_json(name)
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

    @pytest.mark.parametrize("name", TestApi.memorials)
    def test_memorial_to_dict(self, name: str):
        expected = Test.load_memorial_from_json(name)
        m = Memorial.from_dict(expected)
        result = m.to_dict()
        assert result["memorial_id"] == expected["memorial_id"]
        assert result["findagrave_url"] == expected["findagrave_url"]
        assert result["prefix"] == expected["prefix"]
        assert result["name"] == expected["name"]
        assert result["suffix"] == expected["suffix"]
        assert result["nickname"] == expected["nickname"]
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
        assert result["burial_place"] == expected["burial_place"]
        assert result["cemetery_id"] == expected["cemetery_id"]
        assert result["plot"] == expected["plot"]
        assert result["coords"] == expected["coords"]
        assert result["has_bio"] == expected["has_bio"]

    @pytest.mark.parametrize("name", TestApi.memorials)
    def test_memorial_to_json(self, name):
        d = Test.load_memorial_from_json(name)
        m1 = Memorial.from_dict(d)
        json_str = m1.to_json()
        m2 = Memorial.from_dict(json.loads(json_str))
        assert m2 == m1

    @pytest.mark.parametrize(
        "url",
        [
            "https://www.findagrave.com/memorial/should-produce-404",
        ],
    )
    def test_memorial_parse_raises_exception_on_unexpected_404(
        self, url, helpers, tmp_path, caplog, driver
    ):
        with pytest.raises(
            MemorialParseException, match=f"404 Client Error: Not Found for url: {url}"
        ):
            Memorial.parse(url, driver=driver)

    @pytest.mark.parametrize(
        "requested_url, new_url",
        [
            (
                "https://www.findagrave.com/memorial/244781332/william-h-boekholder",
                "https://www.findagrave.com/memorial/260829715/wiliam-henry-boekholder",
            )
        ],
    )
    def test_memorial_parser_merged_raises_exception(
        self, requested_url, new_url, driver
    ):
        with pytest.raises(
            MemorialMergedException,
            match=f"{requested_url} has been merged into {new_url}",
        ) as ex_info:
            Memorial.parse(requested_url, driver=driver)
        assert ex_info.value.new_url == new_url

    @pytest.mark.parametrize(
        "findagrave_url",
        [
            "https://www.findagrave.com/memorial/261491035/dolores-higginbotham",
        ],
    )
    def test_memorial_parser_removed_raises_exception(self, findagrave_url, driver):
        with pytest.raises(MemorialRemovedException, match="has been removed"):
            Memorial.parse(findagrave_url, driver=driver)


class TestCemetery(TestApi):
    def test_not_equal_different_class(self):
        m = Cemetery.from_dict(Test.load_cemetery_from_json("monticello-graveyard"))
        assert m != str("A string object")

    @pytest.mark.parametrize(
        "expected",
        [
            Test.load_cemetery_from_json("arlington-national-cemetery"),
            Test.load_cemetery_from_json("crown-hill-memorial-park"),
            Test.load_cemetery_from_json("monticello-graveyard"),
        ],
    )
    def test_cemetery_from_dict(self, expected: dict):
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
            Test.load_cemetery_from_json("arlington-national-cemetery"),
            Test.load_cemetery_from_json("crown-hill-memorial-park"),
            Test.load_cemetery_from_json("monticello-graveyard"),
        ],
    )
    def test_cemetery_to_dict(self, expected: dict):
        c: Cemetery = Cemetery.from_dict(expected)
        assert isinstance(c, Cemetery)
        result = c.to_dict()
        assert result["cemetery_id"] == expected["cemetery_id"]
        assert result["findagrave_url"] == expected["findagrave_url"]
        assert result["name"] == expected["name"]
        assert result["location"] == expected["location"]
        assert result["coords"] == expected["coords"]
        assert result["num_memorials"] == expected["num_memorials"]

    @pytest.mark.parametrize(
        "expected",
        [
            Test.load_cemetery_from_json("crown-hill-memorial-park"),
        ],
    )
    def test_cemetery(self, expected, driver):
        url = expected["findagrave_url"]
        expected_cem = Cemetery.from_dict(expected)
        cem = Cemetery(url, driver=driver)
        assert cem == expected_cem
        assert cem.cemetery_id == expected["cemetery_id"]
        assert cem.name == expected["name"]
        assert cem.findagrave_url == expected["findagrave_url"]
        assert cem.location == expected["location"]
        assert cem.coords == expected["coords"]


class TestDatabaseOps(TestApi):
    @pytest.mark.parametrize("name", TestApi.memorials)
    def test_memorial_save(self, name: str, database):
        expected = Test.load_memorial_from_json(name)
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

    @pytest.mark.parametrize("name", TestApi.memorials)
    def test_memorial_get_by_id(self, name: str, database):
        expected = Test.load_memorial_from_json(name)
        mid: int = expected["memorial_id"]
        expected_memorial = Memorial.from_dict(expected).save()
        result: Memorial = Memorial.get_by_id(mid)
        assert result == expected_memorial

    @pytest.mark.parametrize("memorial_id", [99999, -12345])
    def test_memorial_by_id_not_found(self, memorial_id, database):
        with pytest.raises(graver.api.NotFound):
            Memorial.get_by_id(memorial_id)


class TestSearch(TestApi):
    @pytest.mark.parametrize(
        "person",
        [
            Test.load_memorial_from_json("james-fenimore-cooper"),
            Test.load_memorial_from_json("john-j-pershing"),
        ],
    )
    def test_search(self, person: dict, driver):
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
            driver=driver,
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

    # @pytest.mark.parametrize(
    #     "param: dict[str, Any]",
    #     [
    #         {"famous": True},
    #         {"famous": False},
    #         {"sponsored": True},
    #         {"sponsored": False},
    #         {"noCemetery": True},
    #         {"cenotaph": True},
    #         {"cenotaph": False},
    #         {"monument": True},
    #         {"monument": False},
    #         {"isVeteran": True},
    #         {"isVeteran": False},
    #         {"photofilter": "photos"},
    #         {"photofilter": "nophotos"},
    #         {"gpsfilter": "gps"},
    #         {"gpsfilter": "nogps"},
    #         {"flowers": True},
    #         {"flowers": False},
    #         {"hasPlot": True},
    #         {"hasPlot": False},
    #     ],
    # )
    # @pytest.mark.parametrize("key, value", [("famous", [True, False])])
    # def test_search_parameters(self, key, value, driver):
    #     max_results = 5
    #     args: dict[str, any] = {
    #         "driver": driver,
    #         "max_results": max_results,
    #         key: value,
    #     }
    #     rs = Memorial.search(**args)
    #     assert 0 < len(rs) <= max_results

    @pytest.mark.parametrize("value", [True, False])
    @pytest.mark.parametrize(
        "key",
        [
            "famous",
            "sponsored",
            "noCemetery",
            "cenotaph",
            "monument",
            "isVeteran",
            "flowers",
            "hasPlot",
        ],
    )
    def test_search_bool_parameters(self, key, value, driver) -> None:
        max_results = 5
        args: dict[str, Any] = {
            "driver": driver,
            "max_results": max_results,
            key: value,
        }
        rs: graver.api.ResultSet = Memorial.search(**args)
        assert 0 <= len(rs) <= max_results

    @pytest.mark.parametrize(
        "key, value",
        [
            ("includeNickName", True),
            ("includeMaidenName", True),
            ("includeTitles", True),
            ("exactName", True),
            ("fuzzyNames", True),
        ],
    )
    @pytest.mark.parametrize("firstname, lastname", [("John", "Smith")])
    def test_search_name_filters(self, firstname, lastname, key, value, driver):
        max_results = 5
        args = {
            "driver": driver,
            "max_results": max_results,
            "firstname": firstname,
            "lastname": lastname,
            key: value,
        }
        rs = Memorial.search(**args)
        assert 0 < len(rs) <= max_results

    @pytest.mark.parametrize("value", ["gps", "nogps"])
    def test_gpsfilter(self, value, driver) -> None:
        max_results = 5
        args: dict[str, Any] = {
            "driver": driver,
            "max_results": max_results,
            "gpsfilter": value,
        }
        rs: graver.api.ResultSet = Memorial.search(**args)
        assert 1 <= len(rs) <= max_results

    @pytest.mark.parametrize(
        "key, value",
        [
            ("photofilter", "photos"),
            ("photofilter", "nophotos"),
            ("gpsfilter", "gps"),
            ("gpsfilter", "nogps"),
        ],
    )
    def test_non_bool_filters(self, key, value, driver) -> None:
        max_results = 5
        args: dict[str, Any] = {
            "driver": driver,
            "max_results": max_results,
            key: value,
        }
        rs: graver.api.ResultSet = Memorial.search(**args)
        assert 1 <= len(rs) <= max_results

    @pytest.mark.parametrize(
        "args, expected", [({"lastname": "Jackson", "max_results": 37}, 37)]
    )
    def test_search_max_results(self, args, expected, driver):
        logging.getLogger().setLevel(logging.DEBUG)
        args["driver"] = driver
        rs = Memorial.search(**args)
        assert 0 < len(rs) <= expected
        pass

    @pytest.mark.parametrize("name", TestApi.famous_memorials)
    def test_search_famous_people(self, name: str, driver) -> None:
        person = Test.load_memorial_from_json(name)
        parts = person["name"].split(" ")
        first = parts[0]
        last = parts[len(parts) - 1]
        if len(parts) > 2:
            middle = parts[1]
        else:
            middle = ""

        patt = re.compile(r"\d{4}$")
        assert (match := re.search(patt, person["birth"])) is not None
        birth_year = match.group(0)
        assert (match := re.search(patt, person["death"])) is not None
        death_year = match.group(0)
        results = Memorial.search(
            firstname=first,
            middlename=middle,
            lastname=last,
            birthyear=birth_year,
            deathyear=death_year,
            famous=True,
            driver=driver,
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

    def test_search_empty(self, driver) -> None:
        logging.getLogger(__name__).setLevel(logging.DEBUG)
        logging.getLogger("betamax").setLevel(logging.DEBUG)
        results = Memorial.search(driver=driver)
        assert len(results) == 0

    # @pytest.mark.parametrize(
    #     "cemetery_url",
    #     [
    #         "https://www.findagrave.com/cemetery/641519",
    #     ],
    # )
    # def test_search_cemetery_famous_veterans(self, cemetery_url, driver):
    #     c = Cemetery(cemetery_url, driver=driver)
    #     results = Memorial.search(c, famous="true", isVeteran="true")
    #     assert results is not None
    #     assert len(results) > 0
    #     for m in results:
    #         assert m.famous
    #         assert m.veteran

    # @pytest.mark.parametrize(
    #     "url, max_results", [("https://www.findagrave.com/cemetery/641519", 37)]
    # )
    # def test_search_cemetery_max_results(self, url, max_results, driver):
    #     rs = Memorial.search(Cemetery(url, driver=driver), max_results=max_results)
    #     assert len(rs) == max_results

    def test_search_cemetery_identifies_memorial_type_monument(self, driver):
        cem = Cemetery(
            "https://www.findagrave.com/cemetery/1990395/honolulu-memorial",
            driver=driver,
        )
        rs = Memorial.search(cem, firstname="Adrian", lastname="Williams")
        assert len(rs) == 1
        m = rs[0]
        assert isinstance(m, Memorial)
        assert m.memorial_type == "Monument"

    def test_search_cemetery_identifies_memorial_type_cenotaph(self, driver):
        cem = Cemetery(
            "https://www.findagrave.com/cemetery/1990395/honolulu-memorial",
            driver=driver,
        )
        rs = Memorial.search(cem, firstname="Harold", lastname="Costill")
        assert len(rs) == 1
        m = rs[0]
        assert isinstance(m, Memorial)
        assert m.memorial_type == "Cenotaph"

    @pytest.mark.parametrize(
        "cem_url",
        ["https://www.findagrave.com/cemetery/49269/arlington-national-cemetery"],
    )
    def test_search_cemetery_multi_page(self, cem_url, driver):
        rs = Memorial.search(Cemetery(cem_url, driver=driver), max_results=40)
        assert len(rs) == 40

    @pytest.mark.parametrize(
        "cemetery_name, expected_count",
        [("monticello-graveyard", 18)],
    )
    def test_search_cemetery(self, cemetery_name, expected_count, driver):
        cem = Cemetery.from_dict(Test.load_cemetery_from_json(cemetery_name))
        cem.driver = driver
        results = Memorial.search(cem, isVeteran=True)
        assert results is not None
        assert len(results) == expected_count
        for _, m in enumerate(results):
            assert m.veteran

    @pytest.mark.parametrize(
        "url, memorial_dict",
        [
            (
                "https://www.findagrave.com/cemetery/2783285/rachel-levy-gravesite",
                Test.load_memorial_from_json("rachel-machado-levy"),
            )
        ],
    )
    def test_search_cemetery_all(self, url, memorial_dict, driver) -> None:
        cem = Cemetery(url, driver=driver)
        assert cem.num_memorials > 0
        results = Memorial.search(cem)
        assert len(results) == cem.num_memorials
        expected = Memorial.from_dict(memorial_dict)
        m: Memorial = results[0]
        assert m.name == expected.name
        assert m.memorial_id == expected.memorial_id

    @pytest.mark.parametrize(
        "name, page_num",
        [("monticello-graveyard", 3)],
    )
    def test_search_cemetery_specific_page(
        self, name: str, page_num: int, driver: Driver
    ):
        d: dict[str, Any] = self.load_cemetery_from_json(name)
        d["driver"] = driver
        cem = Cemetery.from_dict(d)
        rs = Memorial.search(cem, page=page_num)
        assert len(rs) == 20
        assert f"page={page_num}" in rs.source
