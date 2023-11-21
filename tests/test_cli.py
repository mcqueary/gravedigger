import importlib.metadata
import os

import pytest

import graver
import graver.cli as cli
from definitions import ROOT_DIR
from graver.constants import APP_NAME
from graver.memorial import Memorial

asimov_uri = pytest.helpers.to_uri(ROOT_DIR + "/tests/data/asimov.html")
shoulders_uri = pytest.helpers.to_uri(ROOT_DIR + "/tests/data/shoulders.html")
merged_uri = pytest.helpers.to_uri(ROOT_DIR + "/tests/data/merged.html")
maiden_uri = pytest.helpers.to_uri(ROOT_DIR + "/tests/data/dolores-maiden.html")
cem_3136_uri = pytest.helpers.to_uri(ROOT_DIR + "/tests/data/cem-3136.html")


@pytest.mark.parametrize("arg", ["-v", "--version"])
def test_cli_version_multiple_ways(helpers, arg):
    assert helpers.graver_cli(arg) == "{} v{}".format(APP_NAME, graver.__version__)
    metadata = importlib.metadata.metadata("graver")
    name_str = metadata["Name"]
    version_str = metadata["Version"]
    expected_str = "{} v{}".format(name_str, version_str)
    result = helpers.graver_cli(arg)
    assert expected_str in result


def test_cli_input_file_does_not_exist(helpers):
    url_file = "this_file_should_not_exist"
    command = "scrape {}".format(url_file)
    output = helpers.graver_cli(command)
    assert "No such file or directory" in output


@pytest.mark.parametrize(
    "mem_id",
    [
        10325,
    ],
)
def test_cli_scrape(mem_id, helpers):
    url_file = os.getenv("MULTI_LINE_UNIT_TEST_FILE")
    db = os.getenv("DATABASE_NAME")
    command = "scrape {} --db {}".format(url_file, db)
    output = helpers.graver_cli(command)
    assert "Successfully scraped" in output
    m = Memorial.get_by_id(mem_id)
    assert m is not None
    assert m._id == mem_id


@pytest.mark.parametrize(
    "expected_id, url",
    [
        (1075, "https://secure.findagrave.com/cgi-bin/fg.cgi?page=gr&GRid=1075"),
        (544, "https://www.findagrave.com/memorial/544"),
    ],
)
def test_cli_get_id_from_url(expected_id: int, url: str):
    id = cli.get_id_from_url(url)
    assert id == expected_id


@pytest.mark.parametrize("urls", [[""], ["foo", "bar", "baz"]])
def test_print_failed_urls(urls):
    cli.print_failed_urls(urls)


def test_cli_scrape_file_with_bad_urls(helpers):
    url_file = os.getenv("BAD_DATA_FILENAME")
    db = os.getenv("DATABASE_NAME")
    command = "scrape {} --db {}".format(url_file, db)
    output = helpers.graver_cli(command)
    assert "Failed urls were:\nhttps://www.findagrave.com/this-does-not-exist" in output


live_ids = (1075, 534, 574, 627, 544, 6, 7376621, 95929698, 1347)


@pytest.mark.integration_test
@pytest.mark.parametrize(
    "mem_id",
    [
        1075,
    ],
)
def test_cli_scrape_with_single_url_file(mem_id, helpers):
    url_file = os.getenv("SINGLE_LINE_FILENAME")
    db = os.getenv("DATABASE_NAME")
    command = "scrape {} --db {}".format(url_file, db)
    output = helpers.graver_cli(command)
    print(output)
    m = Memorial.get_by_id(mem_id)
    assert m._id == mem_id
