import os

import pytest

from graver.app import main


@pytest.mark.parametrize(
    "args",
    [
        ["-i", "input-1.txt"],
        ["--ifile", "input-1.txt"],
    ],
)
def test_main_with_input_file(capsys, args):
    args += ["--dbfile"]
    args += [os.environ["DATABASE_NAME"]]
    # with pytest.raises(SystemExit):
    main(args)
    out, err = capsys.readouterr()
    assert "Progress 100.0%" in out
    assert err == ""
    print(out, err)
