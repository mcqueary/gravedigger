import importlib.metadata
import logging
import os
import random

import pytest
from click.testing import Result

from graver import Memorial, MemorialMergedException, MemorialParseException
from graver.constants import APP_NAME

from .test import Test


log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)


@pytest.mark.usefixtures("api_mock", "faker")
class TestCli(Test):
    memorials_by_url: dict[str, Memorial] = {}
    memorials_by_id: dict[int, Memorial] = {}

    @staticmethod
    def cache(memorial: Memorial):
        if memorial.findagrave_url not in TestCli.memorials_by_url.keys():
            TestCli.memorials_by_url[memorial.findagrave_url] = memorial
        if memorial.memorial_id not in TestCli.memorials_by_id:
            TestCli.memorials_by_id[memorial.memorial_id] = memorial

    @staticmethod
    @pytest.fixture
    def fake_memorial(faker):
        def _fake_memorial() -> Memorial:
            m = faker.memorial(faker)
            # log.debug(f"Generated {m} from faker instance {faker}")
            TestCli.cache(m)
            return m

        return _fake_memorial

    @staticmethod
    @pytest.fixture
    def api_mock(monkeypatch, faker):
        def _api_mock(url: str) -> bool:
            monkeypatch.setattr(
                "graver.api.Memorial.parse",
                lambda _, **kwargs: TestCli.fake_parse(
                    faker, findagrave_url=url, **kwargs
                ),
            )
            monkeypatch.setattr("graver.api.Memorial.save", TestCli.fake_save)
            monkeypatch.setattr(
                "graver.api.Memorial.create_table", TestCli.fake_create_graves_table
            )
            monkeypatch.setattr(
                "graver.api.Cemetery.create_table", TestCli.fake_create_cemeteries_table
            )
            return True

        return _api_mock

    @staticmethod
    def fake_parse(factory, **kwargs) -> Memorial:
        memorial: Memorial | None = None
        if (url := kwargs.get("findagrave_url", None)) is not None:
            memorial = TestCli.memorials_by_url[url]
        elif (mid := kwargs.get("memorial_id")) is not None:
            memorial = TestCli.memorials_by_id[mid]
        else:
            if "expected" in kwargs:
                memorial = kwargs.get("expected", TestCli.fake_memorial(factory))
        assert memorial is not None
        return memorial

    @staticmethod
    def fake_save(m: Memorial) -> Memorial:
        logging.getLogger(__name__).warning(f"In fake_save for {m}")
        return m

    @staticmethod
    def fake_create_graves_table(filename: str) -> None:
        logging.getLogger(__name__).warning(
            f"In fake_create_graves_table for {filename}"
        )
        return

    @staticmethod
    def fake_create_cemeteries_table(filename: str) -> None:
        logging.getLogger(__name__).warning(
            f"In fake_create_cemeteries_table for {filename}"
        )
        return


class TestCliCommonOptions(TestCli):
    @pytest.mark.parametrize("arg", ["-V", "--version"])
    def test_version(self, helpers, arg, caplog) -> None:
        metadata = importlib.metadata.metadata(APP_NAME)
        name_str = metadata["Name"]
        version_str = metadata["Version"]
        expected_str = "{} v{}".format(name_str, version_str)
        result: Result = helpers.graver_cli(arg)
        assert result.exit_code == 0
        assert result.output == ""
        assert caplog.text.endswith(expected_str + "\n")


class TestCliScrapeFile(TestCli):
    @pytest.fixture(scope="module")
    def silence_tqdm(self):
        os.environ["TQDM_DISABLE"] = "1"
        os.environ["TQDM_MININTERVAL"] = "5"
        yield
        del os.environ["TQDM_DISABLE"]
        del os.environ["TQDM_MININTERVAL"]

    def test_bail_if_file_does_not_exist(self, helpers, caplog):
        url_file = "this_file_should_not_exist"
        command = f"scrape-file '{url_file}'"
        result = helpers.graver_cli(command)
        assert result.exit_code == 1
        assert result.output == ""
        assert "No such file or directory" in caplog.text

    def test_mixed_formats(
        self, helpers, tmp_path, caplog, fake_memorial, api_mock
    ) -> None:
        expected: Memorial = fake_memorial()
        api_mock(expected.findagrave_url)

        urls = [
            expected.findagrave_url,
            f"https://secure.findagrave.com/cgi-bin/fg.cgi?page=gr&GRid={expected.memorial_id}",
            f"{expected.memorial_id}",
        ]

        d = tmp_path / "test_cli_scrape_file"
        d.mkdir()
        url_file = d / "input_urls.txt"
        url_file.write_text("\n".join(urls))

        db = os.getenv("DATABASE_NAME")
        command = f"scrape-file '{url_file}' --db '{db}'"
        result = helpers.graver_cli(command)
        assert result.exit_code == 0
        assert result.output == ""
        assert "Successfully scraped 1 of 1" in caplog.text

    @pytest.mark.parametrize(
        "url",
        [
            "https://www.findagrave.com/memorial/should-produce-404",
        ],
    )
    def test_handles_parse_error(self, url, helpers, tmp_path, caplog, monkeypatch):
        d = tmp_path / "test_cli_scrape_file_handles_http_error"
        d.mkdir()
        url_file = d / "single_url.txt"
        url_file.write_text(f"{url}\n")

        def parse_raises(the_url: str):
            raise MemorialParseException(
                f"404 Client Error: Not Found for url: {the_url}"
            )

        monkeypatch.setattr(Memorial, "parse", parse_raises)
        command = f"scrape-file '{url_file}'"
        result = helpers.graver_cli(command)
        assert result.exit_code == 0
        assert result.output == ""
        assert f"404 Client Error: Not Found for url: {url}" in caplog.text

    def test_handles_invalid_url(self, helpers, caplog, tmp_path):
        d = tmp_path / "test_cli_scrape_file_with_invalid_url"
        d.mkdir()
        url_file = d / "invalid_url.txt"
        url_file.write_text("this-does-not-exist\n")

        command = f"scrape-file '{url_file}'"
        result = helpers.graver_cli(command)
        assert result.exit_code == 0
        assert result.output == ""
        assert "is not a valid URL" in caplog.text
        assert "Failed urls were:\nthis-does-not-exist" in caplog.text

    def test_merged_memorial_exception(
        self, helpers, tmp_path, caplog, fake_memorial, monkeypatch
    ):
        m1 = fake_memorial()
        m2 = fake_memorial()
        assert m1 != m2
        old_url = m1.findagrave_url
        new_url = m2.findagrave_url

        d = tmp_path / "test_cli_scrape_file"
        d.mkdir()
        url_file = d / "input_urls.txt"
        url_file.write_text(old_url + "\n")

        def parse_raises_memorial_merged(findagrave_url: str):
            if findagrave_url == old_url:
                message = f"{old_url} has been merged into {new_url}"
                raise MemorialMergedException(message, old_url, new_url)
            if findagrave_url == new_url:
                return m2

        monkeypatch.setattr(Memorial, "parse", parse_raises_memorial_merged)

        db = os.getenv("DATABASE_NAME")
        command = f"scrape-file '{url_file}' --db '{db}'"
        result = helpers.graver_cli(command)
        assert result.exit_code == 0
        assert result.output == ""
        assert f"{old_url} has been merged into {new_url}" in caplog.text
        assert "Successfully scraped 1 of 1" in caplog.text

    def test_single_url_file(self, helpers, tmp_path, fake_memorial, api_mock) -> None:
        expected: Memorial = fake_memorial()
        url = expected.findagrave_url
        api_mock(url)

        d = tmp_path / "test_single_url_file"
        d.mkdir()
        url_file = d / "single_url.txt"
        url_file.write_text(f"{url}\n")

        db = os.getenv("DATABASE_NAME")
        command = f"scrape-file '{url_file}' --db '{db}'"
        result = helpers.graver_cli(command)
        assert result.exit_code == 0
        assert result.output == ""

    def test_cache(self):
        list_1 = TestCli.memorials_by_url
        list_2 = TestCli.memorials_by_id
        assert len(list_1) > 0
        assert len(list_2) > 0
        assert len(list_1) == len(list_2)


class TestCliScrapeUrl(TestCli):
    @pytest.mark.parametrize(
        "url",
        [
            "https://www.findagrave.com/memorial/should-produce-404",
        ],
    )
    def test_bails_on_http_error(self, url, helpers, caplog, monkeypatch):
        def parse_raises(the_url: str):
            raise MemorialParseException(
                f"404 Client Error: Not Found for url: {the_url}"
            )

        monkeypatch.setattr(Memorial, "parse", parse_raises)

        command = f"scrape-url {url}"
        result = helpers.graver_cli(command)
        assert result.exit_code == 1
        assert result.output == ""
        assert f"404 Client Error: Not Found for url: {url}" in caplog.text

    @pytest.mark.parametrize(
        "non_memorial_url",
        [
            "https://www.findagrave.com/cemetery/1411",
            "this-is-not-a-valid-url",
        ],
    )
    def test_bails_on_non_memorial_url(self, non_memorial_url, helpers, caplog):
        # This will be rejected before a request() is called.
        command = f"scrape-url {non_memorial_url}"
        result = helpers.graver_cli(command)
        assert result.exit_code == 1
        assert result.output == ""
        assert "Invalid or non-memorial URL" in caplog.text

    def test_cli_scrape_url(self, helpers, fake_memorial, api_mock, caplog) -> None:
        expected: Memorial = fake_memorial()
        url = expected.findagrave_url
        api_mock(url)

        db = "test.db"
        os.environ["DATABASE_NAME"] = db
        command = f"scrape-url '{url}' --db '{db}'"
        result = helpers.graver_cli(command)
        assert result.exit_code == 0
        assert result.output == ""


class TestCliSearch(TestCli):
    def test_search_by_id(self, helpers, caplog, fake_memorial, api_mock) -> None:
        expected: Memorial = fake_memorial()
        api_mock(expected.findagrave_url)
        mid = expected.memorial_id
        command = f"search --id={mid}"
        result = helpers.graver_cli(command)
        assert result.exit_code == 0
        assert result.output == ""
        assert f'"memorial_id": {mid}' in caplog.text

    @pytest.mark.parametrize(
        "cemetery_id, lastname, death_year", [(641417, "Jackson", 1828)]
    )
    def test_search_in_cemetery(
        self, cemetery_id, lastname, death_year, helpers, caplog, faker, monkeypatch
    ):
        max_results = 10

        def mock_search(*args, **kwargs):
            return faker.result_set(
                faker,
                "foobar",
                random.randint(0, max_results),
                cemetery_id=cemetery_id,
                lastname=lastname,
                death_year=death_year,
            )

        monkeypatch.setattr(Memorial, "search", mock_search)
        command = (
            f"search --cemetery-id={cemetery_id} --lastname='{lastname}' "
            f"--deathyear={death_year} --max-results={max_results}"
        )
        result = helpers.graver_cli(command)
        assert result.exit_code == 0
        assert result.output == ""

    @pytest.mark.parametrize("value", ["yes", "true"])
    def test_gpsfilter_callback(self, value, helpers):
        command = f"search --gpsfilter={value}"
        result = helpers.graver_cli(command)
        assert result.exit_code == 2
        assert "Invalid value" in result.output

    @pytest.mark.parametrize("value", ["yes", "true"])
    def test_photofilter_callback(self, value, helpers):
        command = f"search --photofilter={value}"
        result = helpers.graver_cli(command)
        assert result.exit_code == 2
        assert "Invalid value" in result.output

    @pytest.mark.parametrize("value", ["yes", "true"])
    def test_yearfilter_callback(self, value, helpers, caplog):
        command = f"search --birthyear=1856 --birthyearfilter={value}"
        result = helpers.graver_cli(command)
        assert result.exit_code == 2
        assert "Invalid value" in result.output

    @pytest.mark.parametrize(
        "param",
        [
            "exactName",
            "fuzzyNames",
        ],
    )
    def test_name_filter_callback(self, param, helpers):
        # Success case
        command = f"search --firstname=foo --{param} --max=5"
        result = helpers.graver_cli(command)
        assert result.exit_code == 0

        # Failure case
        command = f"search --{param} --max=5"
        result = helpers.graver_cli(command)
        assert result.exit_code == 2
        assert "Invalid value" in result.output

    # @pytest.mark.parametrize(
    #     "parm",
    #     [
    #         "famous=true",
    #         "famous=false",
    #         "sponsored=true",
    #         "sponsored=false",
    #         "noCemetery",
    #         "cenotaph=true",
    #         "cenotaph=false",
    #         "monument=true",
    #         "monument=false",
    #         "isVeteran=true",
    #         "isVeteran=false",
    #         "photofilter=photos",
    #         "photofilter=nophotos",
    #         "gpsfilter=gps",
    #         "gpsfilter=nogps",
    #         "flowers=true",
    #         "flowers=false",
    #         "hasPlot=true",
    #         "hasPlot=false",
    #     ],
    # )
    # def test_parameters(self, parm, helpers, caplog):
    #     max_results = 5
    #     command = f"search --{parm} --max-results={max_results}"
    #     # with vcr.use_cassette(
    #     #     os.path.join(Test.CASSETTES, f"test_cli_search_with_parm-{parm}.yaml")
    #     # ):
    #     result = helpers.graver_cli(command)
    #     assert result.exit_code == 0
    #     assert result.output == ""
    #     assert caplog.text.count("\n") == max_results

    # @pytest.mark.parametrize(
    #     "parm",
    #     [
    #         "includeNickName",
    #         "includeMaidenName",
    #         "includeTitles",
    #         "exactName",
    #         "fuzzyNames",
    #     ],
    # )
    # def test_name_filters(self, parm, helpers, caplog):
    #     # with vcr.use_cassette(
    #     #     os.path.join(
    #     #         Test.CASSETTES,
    #     #         f"test_cli_search_with_name_filters" f"-{parm}.yaml",
    #     #     )
    #     # ):
    #     max_results = 5
    #     command = (
    #         f"search --firstname=John --lastname=Smith --{parm} --max-results"
    #         f"={max_results}"
    #     )
    #     result = helpers.graver_cli(command)
    #     assert result.exit_code == 0
    #     assert result.output == ""
    #     assert caplog.text.count("\n") == max_results
