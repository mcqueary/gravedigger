import pytest

from graver.parsers import MemorialParser


@pytest.mark.integration_test
@pytest.mark.parametrize(
    "url",
    [
        "https://secure.findagrave.com/cgi-bin/fg.cgi?page=gr&GRid=534",
        "https://www.findagrave.com/memorial/534",
    ],
)
def test_memorial_parser_parse(url):
    memorial = MemorialParser().parse(url)
    assert memorial.id == 534
    assert memorial.name == "Andrew Jackson"
