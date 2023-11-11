import pytest

from graver.models import Memorial


@pytest.marl.parametrize(
    "url",
    [
        "https://secure.findagrave.com/cgi-bin/fg.cgi?page=gr&GRid=544",
        "https://secure.findagrave.com/cgi-bin/fg.cgi?page=gr&GRid=534",
    ],
)
def test_memorial_scrape(url):
    memorial = Memorial.scrape(url)
    assert memorial is not None