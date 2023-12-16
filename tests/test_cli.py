import importlib.metadata
import logging
import os

import pytest
import vcr

from graver import Memorial, __version__
from graver.constants import APP_NAME

# live_urls = [
#     "https://secure.findagrave.com/cgi-bin/fg.cgi?page=gr&GRid=1784",
#     "https://www.findagrave.com/memorial/1075/george-washington",
#     "https://secure.findagrave.com/cgi-bin/fg.cgi?page=gr&GRid=534",
#     "https://secure.findagrave.com/cgi-bin/fg.cgi?page=gr&GRid=574",
#     "https://secure.findagrave.com/cgi-bin/fg.cgi?page=gr&GRid=627",
#     "https://secure.findagrave.com/cgi-bin/fg.cgi?page=gr&GRid=544",
#     "https://secure.findagrave.com/cgi-bin/fg.cgi?page=gr&GRid=6",
#     "https://secure.findagrave.com/cgi-bin/fg.cgi?page=gr&GRid=7376621",
#     "https://secure.findagrave.com/cgi-bin/fg.cgi?page=gr&GRid=95929698",
#     "https://secure.findagrave.com/cgi-bin/fg.cgi?page=gr&GRid=1347",
#     "1075",
# ]


@pytest.fixture(autouse=True)
def silence_tqdm():
    os.environ["TQDM_DISABLE"] = "1"
    os.environ["TQDM_MININTERVAL"] = "5"
    yield
    del os.environ["TQDM_DISABLE"]
    del os.environ["TQDM_MININTERVAL"]


@pytest.mark.parametrize("arg", ["-V", "--version"])
def test_cli_version_multiple_ways(helpers, arg):
    assert helpers.graver_cli(arg) == "{} v{}".format(APP_NAME, __version__)
    metadata = importlib.metadata.metadata("graver")
    name_str = metadata["Name"]
    version_str = metadata["Version"]
    expected_str = "{} v{}".format(name_str, version_str)
    result = helpers.graver_cli(arg)
    assert expected_str in result


def test_cli_scrape_file_does_not_exist(helpers, database):
    url_file = "this_file_should_not_exist"
    command = f"scrape-file '{url_file}'"
    output = helpers.graver_cli(command)
    assert "No such file or directory" in output


def test_cli_scrape_file_with_invalid_url(helpers, caplog, database, tmp_path):
    d = tmp_path / "test_cli_scrape_file_with_invalid_url"
    d.mkdir()
    url_file = d / "invalid_url.txt"
    url_file.write_text("this-doesn't-exist\n")

    command = f"scrape-file '{url_file}'"
    helpers.graver_cli(command)
    assert "is not a valid URL" in caplog.text


@pytest.mark.parametrize(
    "name, cassette",
    [("grace-brewster-hopper", pytest.vcr_cassettes + "test-cli-scrape-file.yaml")],
)
def test_cli_scrape_file(name, cassette, helpers, database, tmp_path, caplog):
    urls = [
        "https://secure.findagrave.com/cgi-bin/fg.cgi?page=gr&GRid=1784",
        "https://www.findagrave.com/memorial/1075/george-washington",
        "1075",
    ]
    with vcr.use_cassette(cassette):
        person = pytest.helpers.load_memorial_from_json(name)

        d = tmp_path / "test_cli_scrape_file"
        d.mkdir()
        url_file = d / "input_urls.txt"
        url_file.write_text("\n".join(urls))

        db = os.getenv("DATABASE_NAME")
        command = f"scrape-file '{url_file}' --db '{db}'"
        output = helpers.graver_cli(command)
        assert f"Successfully scraped {len(urls)} of {len(urls)}" in output
        mem_id = person["memorial_id"]
        m = Memorial.get_by_id(mem_id)
        assert m is not None
        assert m.memorial_id == mem_id


@vcr.use_cassette(
    pytest.vcr_cassettes + "test_cli_scrape_file_logs_merged_memorial_exception.yaml"
)
@pytest.mark.parametrize(
    "url, new_url",
    [
        (
            "https://www.findagrave.com/memorial/244781332/william-h-boekholder",
            "https://www.findagrave.com/memorial/260829715/wiliam-henry-boekholder",
        )
    ],
)
def test_cli_scrape_file_logs_merged_memorial_exception(
    url, new_url, helpers, tmp_path, caplog
):
    url = "https://www.findagrave.com/memorial/244781332/william-h-boekholder"
    d = tmp_path / "test_cli_scrape_file"
    d.mkdir()
    url_file = d / "input_urls.txt"
    url_file.write_text(url + "\n")

    db = os.getenv("DATABASE_NAME")
    command = f"scrape-file '{url_file}' --db '{db}'"
    output = helpers.graver_cli(command)
    assert f"{url} has been merged into {new_url}" in caplog.text
    assert "Successfully scraped 1 of 1" in output


@pytest.mark.parametrize(
    "name",
    ["george-washington", "grace-brewster-hopper"],
)
def test_cli_scrape_url(name, helpers, database):
    expected = pytest.helpers.load_memorial_from_json(name)
    cassette = f"{pytest.vcr_cassettes}{name}.yaml"
    with vcr.use_cassette(cassette):
        db = os.getenv("DATABASE_NAME")
        url = expected["findagrave_url"]
        expected_id = expected["memorial_id"]
        command = f"scrape-url '{url}' --db '{db}'"
        helpers.graver_cli(command)
        m = Memorial.get_by_id(expected_id)
        assert m is not None and m.memorial_id == expected_id


def test_cli_scrape_file_with_bad_urls(helpers, database, tmp_path):
    d = tmp_path / "test_cli_scrape_file_with_bad_urls"
    d.mkdir()
    url_file = d / "invalid_urls.txt"
    url_file.write_text("this-does-not-exist\n")

    db = os.getenv("DATABASE_NAME")
    command = f"scrape-file '{url_file}' --db '{db}'"
    output = helpers.graver_cli(command)
    assert "Failed urls were:\nthis-does-not-exist" in output


@pytest.mark.parametrize(
    "url",
    [
        "this-is-not-a-valid-url",
    ],
)
def test_cli_scrape_url_with_bad_url(url, helpers, caplog, database):
    db = os.getenv("DATABASE_NAME")
    command = f"scrape-url '{url}' --db '{db}'"
    helpers.graver_cli(command)
    assert "Invalid URL" in caplog.text


@pytest.mark.parametrize(
    "name",
    [
        "george-washington",
    ],
)
def test_cli_scrape_file_with_single_url_file(name, helpers, database, tmp_path):
    expected = pytest.helpers.load_memorial_from_json(name)
    cassette = f"{pytest.vcr_cassettes}{name}.yaml"

    d = tmp_path / "test_cli_scrape_file_with_single_url_file"
    d.mkdir()
    url_file = d / "single_url.txt"
    url_file.write_text("https://www.findagrave.com/memorial/1075/george-washington\n")

    with vcr.use_cassette(cassette):
        db = os.getenv("DATABASE_NAME")
        command = f"scrape-file '{url_file}' --db '{db}'"
        output = helpers.graver_cli(command)
        print(output)
        m = Memorial.get_by_id(expected["memorial_id"])
        expected = Memorial.from_dict(expected)
        assert m == expected


@pytest.mark.parametrize(
    "firstname, lastname, deathyear", [("Kirby", "Johnson", "1945")]
)
def test_cli_search_no_cemetery(firstname, lastname, deathyear, helpers):
    with vcr.use_cassette(pytest.vcr_cassettes + "test_cli_search_no_cemetery.yaml"):
        command = (
            f"search --firstname='{firstname}' --lastname='{lastname}' "
            f"--deathyear={deathyear}"
        )

        output = helpers.graver_cli(command)
        assert "Error" not in output
        assert "Advertisement" not in output


@pytest.mark.parametrize("cemetery_id, lastname", [(641417, "Jackson")])
def test_cli_search_in_cemetery(cemetery_id, lastname, helpers):
    with vcr.use_cassette(pytest.vcr_cassettes + "test_cli_search_in_cemetery.yaml"):
        max_results = 20
        command = (
            f"search --cemetery-id={cemetery_id} --lastname='{lastname}' "
            f"--max-results={max_results}"
        )
        output = helpers.graver_cli(command)
        assert "Error" not in output
        assert "Advertisement" not in output
