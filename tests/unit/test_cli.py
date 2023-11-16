import pytest

import cli

# @pytest.mark.parametrize("option", ("-h", "--help"))
# def test_help(capsys, option):
#     try:
#         main([option])
#     except SystemExit:
#         pass
#     output = capsys.readouterr().out
#     assert "Scrape FindAGrave memorials." in output


# @pytest.mark.parametrize("option", ("-i", "--ifile"))
# def test_app_parse_args_error(capsys, option):
#     with pytest.raises(SystemExit) as error:
#         parse_args([option])
#     assert error.value.code == 2
#     captured = capsys.readouterr()
#     assert "error: argument -i/--ifile: expected one argument" in captured.err


# def test_help(pytester):
#     result = pytester.runpytest("--help")
#     # result.stdout.fnmatch_lines(["*--slow * include tests marked slow*"])

parms = [
    "https://secure.findagrave.com/cgi-bin/fg.cgi?page=gr&GRid=1075",
    "https://secure.findagrave.com/cgi-bin/fg.cgi?page=gr&GRid=534",
    "https://secure.findagrave.com/cgi-bin/fg.cgi?page=gr&GRid=574",
    "https://secure.findagrave.com/cgi-bin/fg.cgi?page=gr&GRid=627",
    "https://secure.findagrave.com/cgi-bin/fg.cgi?page=gr&GRid=544",
    "https://secure.findagrave.com/cgi-bin/fg.cgi?page=gr&GRid=6",
    "https://secure.findagrave.com/cgi-bin/fg.cgi?page=gr&GRid=7376621",
    "https://secure.findagrave.com/cgi-bin/fg.cgi?page=gr&GRid=95929698",
    "https://secure.findagrave.com/cgi-bin/fg.cgi?page=gr&GRid=1347",
]


@pytest.mark.parametrize(
    "expected_id, url",
    [
        (1075, "https://secure.findagrave.com/cgi-bin/fg.cgi?page=gr&GRid=1075"),
        (544, "https://www.findagrave.com/memorial/544"),
    ],
)
def test_get_id_from_url(expected_id: int, url: str):
    id = cli.get_id_from_url(url)
    assert id == expected_id
