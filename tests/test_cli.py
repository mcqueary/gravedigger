import importlib.metadata
import os

import pytest
import vcr

from graver import Memorial, __version__
from graver.constants import APP_NAME

live_urls = [
    "https://secure.findagrave.com/cgi-bin/fg.cgi?page=gr&GRid=1784",
    "https://www.findagrave.com/memorial/1075/george-washington",
    "https://secure.findagrave.com/cgi-bin/fg.cgi?page=gr&GRid=534",
    "https://secure.findagrave.com/cgi-bin/fg.cgi?page=gr&GRid=574",
    "https://secure.findagrave.com/cgi-bin/fg.cgi?page=gr&GRid=627",
    "https://secure.findagrave.com/cgi-bin/fg.cgi?page=gr&GRid=544",
    "https://secure.findagrave.com/cgi-bin/fg.cgi?page=gr&GRid=6",
    "https://secure.findagrave.com/cgi-bin/fg.cgi?page=gr&GRid=7376621",
    "https://secure.findagrave.com/cgi-bin/fg.cgi?page=gr&GRid=95929698",
    "https://secure.findagrave.com/cgi-bin/fg.cgi?page=gr&GRid=1347",
    "1075",
]


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
    command = "scrape-file {}".format(url_file)
    output = helpers.graver_cli(command)
    assert "No such file or directory" in output


@pytest.mark.parametrize(
    "name, cassette",
    [("grace-brewster-hopper", pytest.vcr_cassettes + "test-cli-scrape-file.yaml")],
)
def test_cli_scrape_file(name, cassette, helpers, database, tmp_path):
    urls = [
        "https://www.findagrave.com/memorial/22633912/john-quincy-adams",
        "https://www.findagrave.com/memorial/1784/grace-brewster-hopper",
        "https://www.findagrave.com/cemetery/3136/crown-hill-memorial-park",
    ]
    with vcr.use_cassette(cassette):
        person = pytest.helpers.load_memorial_from_json(name)

        d = tmp_path / "test_cli_scrape_file"
        d.mkdir()
        url_file = d / "input_urls.txt"
        url_file.write_text("\n".join(urls))

        db = os.getenv("DATABASE_NAME")
        command = "scrape-file {} --db {}".format(url_file, db)
        output = helpers.graver_cli(command)
        assert "Successfully scraped" in output
        mem_id = person["memorial_id"]
        m = Memorial.get_by_id(mem_id)
        assert m is not None
        assert m.memorial_id == mem_id


def test_cli_scrape_file_with_invalid_url(helpers, caplog, database, tmp_path):
    d = tmp_path / "test_cli_scrape_file_with_invalid_url"
    d.mkdir()
    url_file = d / "invalid_url.txt"
    url_file.write_text("this-doesn't-exist\n")

    command = "scrape-file {}".format(url_file)
    helpers.graver_cli(command)
    assert "is not a valid URL" in caplog.text


@vcr.use_cassette(pytest.vcr_cassettes + "jacob-wolf.yaml")
@pytest.mark.parametrize(
    "url",
    [
        "https://www.findagrave.com/memorial/49636099/jacob-wolf",
    ],
)
def test_cli_scrape_url(url, helpers, database):
    db = os.getenv("DATABASE_NAME")
    command = "scrape-url {} --db {}".format(url, db)
    helpers.graver_cli(command)
    m = Memorial.get_by_id(49636099)
    assert m is not None
    assert m.memorial_id == 49636099


def test_cli_scrape_file_with_bad_urls(helpers, database, tmp_path):
    d = tmp_path / "test_cli_scrape_file_with_bad_urls"
    d.mkdir()
    url_file = d / "invalid_urls.txt"
    url_file.write_text("this-does-not-exist\n")

    db = os.getenv("DATABASE_NAME")
    command = "scrape-file {} --db {}".format(url_file, db)
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
    command = "scrape-url {} --db {}".format(url, db)
    helpers.graver_cli(command)
    assert "Invalid URL" in caplog.text


live_ids = (1075, 534, 574, 627, 544, 6, 7376621, 95929698, 1347)


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
        command = "scrape-file {} --db {}".format(url_file, db)
        output = helpers.graver_cli(command)
        print(output)
        m = Memorial.get_by_id(expected["memorial_id"])
        expected_mem = Memorial.from_dict(expected)
        assert m == expected_mem


@pytest.mark.parametrize(
    "firstname, lastname, deathyear", [("Kirby", "Johnson", "1945")]
)
def test_cli_search_no_cemetery(firstname, lastname, deathyear, helpers):
    with vcr.use_cassette(pytest.vcr_cassettes + "test_cli_search_no_cemetery.yaml"):
        command = "search --firstname={} --lastname={} --deathyear={}".format(
            firstname, lastname, deathyear
        )
        output = helpers.graver_cli(command)
        assert "Error" not in output
        assert "Advertisement" not in output


@pytest.mark.parametrize("cemetery_id, lastname", [(641417, "Jackson")])
def test_cli_search_in_cemetery(cemetery_id, lastname, helpers):
    with vcr.use_cassette(pytest.vcr_cassettes + "test_cli_search_in_cemetery.yaml"):
        max_results = 20
        command = "search --cemetery-id={} --lastname={} --max-results={}".format(
            cemetery_id, lastname, max_results
        )
        output = helpers.graver_cli(command)
        assert "Error" not in output
        assert "Advertisement" not in output
