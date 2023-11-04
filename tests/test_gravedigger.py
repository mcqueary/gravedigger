import pytest
from gravedigger import findagravecitation, main


def test_always_passes():
    assert True


@pytest.mark.parametrize("option", ("-h", "--help"))
def test_help(capsys, option):
    try:
        main([option])
    except SystemExit:
        pass
    output = capsys.readouterr().out
    assert "Scrape FindAGrave memorials." in output


def test_findagravecitation():
    graveid = 1075  # George Washington
    grave = findagravecitation(graveid)
    assert grave["id"] == 1075
    assert grave["name"] == "George Washington"
