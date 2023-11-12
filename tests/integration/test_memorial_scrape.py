import pytest

from graver.memorial import Memorial


@pytest.mark.parametrize(
    "url",
    [
        "https://secure.findagrave.com/cgi-bin/fg.cgi?page=gr&GRid=534",
        "https://www.findagrave.com/memorial/534",
    ],
)
def test_memorial_scrape(url):
    memorial = Memorial.scrape(url)
    assert memorial.id == 534
    assert memorial.name == "Andrew Jackson"
