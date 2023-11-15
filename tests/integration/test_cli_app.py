import os

import pytest

from graver.cli import scrape

# import pytest

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


@pytest.mark.parametrize(
    "filename",
    [
        "input-1.txt",
    ],
)
def test_cli_scrape_with_input_1(filename):
    # TODO test for something here, rather than just db existence
    scrape(filename)
    assert os.path.exists(os.getenv("DATABASE_NAME"))
