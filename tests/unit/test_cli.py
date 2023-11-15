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
