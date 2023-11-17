import importlib.metadata

import pytest
from typer.testing import CliRunner

import graver
from graver import cli
from graver.cli import app

runner = CliRunner()


def test_version():
    result = runner.invoke(app, ["--version"])
    metadata = importlib.metadata.metadata("graver")
    name_str = metadata["Name"]
    # version_str = metadata["Version"]
    version_str = graver.__version__
    expected_str = "{} v{}".format(name_str, version_str)
    assert expected_str in result.stdout.strip()


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
