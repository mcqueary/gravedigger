import os
import pytest

from graver.app import main

@pytest.mark.parametrize("option", ("", "--foobar"))
def test_main_no_args(capsys, option):
    try:
        main([option])
    except SystemExit:
        pass
    output = capsys.readouterr().out
    assert "the following arguments are required: -i/--ifile" in output
    
    
@pytest.mark.parametrize("args", [["-i", "input.txt"], ["--ifile", "input.txt"]])
def test_main_with_input_file(capsys, args):
    input_file = args[1]
    assert os.path.isfile(input_file)
    try:
        main([args])
    except SystemExit as e:
        pass
    # output = capsys.readouterr().out
    # assert "Scrape FindAGrave memorials." in output
    
