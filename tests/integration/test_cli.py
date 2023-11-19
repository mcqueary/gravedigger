import os
import shlex

import pytest
from typer.testing import CliRunner

import graver
from graver.cli import app
from graver.constants import APP_NAME
from graver.memorial import Memorial

live_ids = (1075, 534, 574, 627, 544, 6, 7376621, 95929698, 1347)

runner = CliRunner()


def graver_cli(command_string):
    command_list = shlex.split(command_string)
    result = runner.invoke(app, command_list)
    output = result.stdout.rstrip()
    return output


def test_version():
    assert graver_cli("--version") == "{} v{}".format(APP_NAME, graver.__version__)


@pytest.mark.integration_test
@pytest.mark.parametrize(
    "mem_id",
    [
        1075,
    ],
)
def test_cli_scrape_with_single_url_file(mem_id):
    url_file = os.getenv("SINGLE_LINE_FILENAME")
    db = os.getenv("DATABASE_NAME")
    command = "scrape {} --db {}".format(url_file, db)
    output = graver_cli(command)
    print(output)
    m = Memorial.get_by_id(mem_id)
    assert m.id == mem_id
