import pytest

from graver.app import scrape_grave


@pytest.mark.parametrize(
    "id,name",
    [(1075, "George Washington"), (544, "Thomas Jefferson"), (534, "Andrew Jackson")],
)
def test_scrape_grave(id, name):
    grave = scrape_grave(id)
    assert grave["id"] == id
    assert grave["name"] == name
