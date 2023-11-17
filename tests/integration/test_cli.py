import os

import pytest
from cli import scrape
from memorial import Memorial

# @pytest.mark.parametrize(
#     "args",
#     [
#         ["-i", "input-1.txt"],
#         ["--ifile", "input-1.txt"],
#     ],
# )
# def test_main_with_input_file(capsys, args):
#     args += ["--dbfile"]
#     args += [os.environ["DATABASE_NAME"]]
#     main(args)
#     out, err = capsys.readouterr()
#     assert "Progress 100.0%" in out
#     assert err == ""
#     # print(out, err)

live_ids = (1075, 534, 574, 627, 544, 6, 7376621, 95929698, 1347)


@pytest.mark.parametrize(
    "mem_id",
    [
        1075,
    ],
)
def test_cli_scrape_with_single_url_file(mem_id):
    filename = os.getenv("SINGLE_LINE_FILENAME")
    scrape(filename)
    m = Memorial.get_by_id(mem_id)
    assert m.id == mem_id
