import importlib.metadata
import logging
import os

import pytest
import requests
import vcr
from urllib3.exceptions import MaxRetryError

from graver import Memorial

vcr_log = logging.getLogger("vcr")
vcr_log.setLevel(logging.WARN)


@pytest.fixture(autouse=True)
def silence_tqdm():
    os.environ["TQDM_DISABLE"] = "1"
    os.environ["TQDM_MININTERVAL"] = "5"
    yield
    del os.environ["TQDM_DISABLE"]
    del os.environ["TQDM_MININTERVAL"]


@pytest.mark.parametrize("arg", ["-V", "--version"])
def test_cli_version(helpers, arg, caplog):
    # assert helpers.graver_cli(arg) == "{} v{}".format(APP_NAME, __version__)
    metadata = importlib.metadata.metadata("graver")
    name_str = metadata["Name"]
    version_str = metadata["Version"]
    expected_str = "{} v{}".format(name_str, version_str)
    assert helpers.graver_cli(arg) == ""
    assert caplog.text.endswith(expected_str + "\n")


def test_cli_scrape_file_does_not_exist(helpers, database, caplog):
    url_file = "this_file_should_not_exist"
    command = f"scrape-file '{url_file}'"
    assert helpers.graver_cli(command) == ""
    assert "No such file or directory" in caplog.text


def test_cli_scrape_file_with_invalid_url(helpers, caplog, database, tmp_path):
    d = tmp_path / "test_cli_scrape_file_with_invalid_url"
    d.mkdir()
    url_file = d / "invalid_url.txt"
    url_file.write_text("this-doesn't-exist\n")

    command = f"scrape-file '{url_file}'"
    assert helpers.graver_cli(command) == ""
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
        assert helpers.graver_cli(command) == ""
        assert f"Successfully scraped {len(urls)} of {len(urls)}" in caplog.text
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
    assert helpers.graver_cli(command) == ""
    assert f"{url} has been merged into {new_url}" in caplog.text
    assert "Successfully scraped 1 of 1" in caplog.text


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
        assert helpers.graver_cli(command) == ""
        m = Memorial.get_by_id(expected_id)
        assert m is not None and m.memorial_id == expected_id


@pytest.mark.parametrize(
    "non_memorial_url", ["https://www.findagrave.com/cemetery/1411"]
)
def test_cli_scrape_non_memorial_url(non_memorial_url, helpers, caplog):
    command = f"scrape-url {non_memorial_url}"
    assert helpers.graver_cli(command) == ""
    assert "Invalid or non-memorial URL" in caplog.text


def test_cli_scrape_file_with_bad_urls(helpers, database, tmp_path, caplog):
    d = tmp_path / "test_cli_scrape_file_with_bad_urls"
    d.mkdir()
    url_file = d / "invalid_urls.txt"
    url_file.write_text("this-does-not-exist\n")

    db = os.getenv("DATABASE_NAME")
    command = f"scrape-file '{url_file}' --db={db}"
    assert helpers.graver_cli(command) == ""
    assert "Failed urls were:\nthis-does-not-exist" in caplog.text


@pytest.mark.parametrize(
    "url",
    [
        "this-is-not-a-valid-url",
    ],
)
def test_cli_scrape_url_with_bad_url(url, helpers, caplog, database):
    db = os.getenv("DATABASE_NAME")
    command = f"scrape-url '{url}' --db '{db}'"
    assert helpers.graver_cli(command) == ""
    assert "Invalid or non-memorial URL" in caplog.text


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
        assert helpers.graver_cli(command) == ""
        m = Memorial.get_by_id(expected["memorial_id"])
        expected = Memorial.from_dict(expected)
        assert m == expected


@pytest.mark.parametrize("cemetery_id, lastname", [(641417, "Jackson")])
def test_cli_search_in_cemetery(cemetery_id, lastname, helpers, caplog):
    with vcr.use_cassette(pytest.vcr_cassettes + "test_cli_search_in_cemetery.yaml"):
        max_results = 20
        command = (
            f"search --cemetery-id={cemetery_id} --lastname='{lastname}' "
            f"--max-results={max_results}"
        )
        assert helpers.graver_cli(command) == ""
        assert caplog.text != ""


@pytest.mark.parametrize("name", ["grace-brewster-hopper"])
def test_cli_search_memorial_id(name, helpers, caplog):
    expected = pytest.helpers.load_memorial_from_json(name)
    mid = expected["memorial_id"]

    cassette = os.path.join(
        pytest.vcr_cassettes, f"test_cli_search_memorial_id-{mid}.yaml"
    )
    with vcr.use_cassette(cassette):
        command = f"search --id={mid}"
        assert helpers.graver_cli(command) == ""
        assert caplog.text.count("\n") == 1
        assert f'"memorial_id": {mid}' in caplog.text


@pytest.mark.parametrize("value", ["yes", "true"])
def test_cli_search_gpsfilter_bad_values(value, helpers):
    command = f"search --gpsfilter={value}"
    output = helpers.graver_cli(command)
    assert "Invalid value" in output


@pytest.mark.parametrize("value", ["yes", "true"])
def test_cli_search_yearfilter_bad_values(value, helpers, caplog):
    command = f"search --birthyear=1856 --birthyearfilter={value}"
    output = helpers.graver_cli(command)
    assert "Invalid value" in output


@pytest.mark.parametrize(
    "parm",
    [
        "famous=true",
        "famous=false",
        "sponsored=true",
        "sponsored=false",
        "noCemetery",
        "cenotaph=true",
        "cenotaph=false",
        "monument=true",
        "monument=false",
        "isVeteran=true",
        "isVeteran=false",
        "photofilter=photos",
        "photofilter=nophotos",
        "gpsfilter=gps",
        "gpsfilter=nogps",
        "flowers=true",
        "flowers=false",
        "hasPlot=true",
        "hasPlot=false",
    ],
)
def test_cli_search_with_parm(parm, helpers, caplog):
    max_results = 5
    command = f"search --{parm} --max-results={max_results}"
    with vcr.use_cassette(
        os.path.join(pytest.vcr_cassettes, f"test_cli_search_with_parm-{parm}.yaml")
    ):
        assert helpers.graver_cli(command) == ""
        assert caplog.text.count("\n") == max_results


@pytest.mark.parametrize(
    "parm",
    [
        "includeNickName",
        "includeMaidenName",
        "includeTitles",
        "exactName",
        "fuzzyNames",
    ],
)
def test_cli_search_with_name_filters(parm, helpers, caplog):
    with vcr.use_cassette(
        os.path.join(
            pytest.vcr_cassettes, f"test_cli_search_with_name_filters" f"-{parm}.yaml"
        )
    ):
        max_results = 5
        command = (
            f"search --firstname=John --lastname=Smith --{parm} --max-results"
            f"={max_results}"
        )
        assert helpers.graver_cli(command) == ""
        assert caplog.text.count("\n") == max_results


@pytest.mark.parametrize(
    "requested_url, new_url",
    [
        (
            "https://www.findagrave.com/memorial/244781332/william-h-boekholder",
            "https://www.findagrave.com/memorial/260829715/wiliam-henry-boekholder",
        )
    ],
)
def test_cli_scrape_url_merged_memorial(requested_url, new_url, helpers, caplog):
    with vcr.use_cassette(
        os.path.join(pytest.vcr_cassettes, "test_cli_scrape_url_merged_memorial.yaml")
    ):
        command = f"scrape-url {requested_url}"
        assert helpers.graver_cli(command) == ""
        assert caplog.text.count("\n") == 2
        expected_text = f"{requested_url} has been merged into {new_url}"
        assert expected_text in caplog.text


@pytest.mark.parametrize(
    "url, cassette",
    [
        (
            "https://www.findagrave.com/memorial/should-produce-404",
            pytest.vcr_cassettes + "404-memorial.yaml",
        ),
    ],
)
def test_cli_scrape_url_handles_http_error(url, cassette, helpers, caplog):
    command = f"scrape-url {url}"
    assert helpers.graver_cli(command) == ""
    assert caplog.text.count("\n") == 1
    assert f"404 Client Error: Not Found for url: {url}" in caplog.text


@pytest.mark.parametrize(
    "url, cassette",
    [
        (
            "https://www.findagrave.com/memorial/should-produce-404",
            pytest.vcr_cassettes + "404-memorial.yaml",
        ),
    ],
)
def test_cli_scrape_file_handles_http_error(url, cassette, helpers, tmp_path, caplog):
    d = tmp_path / "test_cli_scrape_file_handles_http_error"
    d.mkdir()
    url_file = d / "single_url.txt"
    url_file.write_text(f"{url}\n")

    command = f"scrape-file {url_file}"
    assert helpers.graver_cli(command) == ""
    assert f"404 Client Error: Not Found for url: {url}" in caplog.text


@pytest.mark.parametrize(
    "url", ["https://www.findagrave.com/memorial/7/john-quincy-adams"]
)
def test_cli_unrecoverable_error(url, helpers, requests_mock, caplog):
    requests_mock.reset()
    requests_mock.get(
        url,
        [
            {"status_code": 403, "reason": "Forbidden"},
        ],
    )
    command = f"scrape-url {url}"
    assert helpers.graver_cli(command) == ""
    assert f"403 Client Error: Forbidden for url: {url}" in caplog.text


@pytest.mark.parametrize(
    "url", ["https://www.findagrave.com/memorial/7/john-quincy-adams"]
)
def test_cli_unrecoverable_connection_error(url, helpers, caplog, requests_mock):
    requests_mock.reset()
    requests_mock.get(
        url,
        exc=requests.exceptions.ConnectTimeout(MaxRetryError(None, url, None), None),
    )

    command = f"scrape-url {url}"
    assert helpers.graver_cli(command) == ""
    # expected_text = f"{requested_url} has been merged into {new_url}"
    assert "Max retries exceeded" in caplog.text
