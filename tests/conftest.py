import os
import pathlib
import shlex
import tempfile

import pytest
from typer.testing import CliRunner

from definitions import ROOT_DIR
from graver.cemetery import Cemetery
from graver.cli import app
from graver.memorial import Memorial

pytest_plugins = ["helpers_namespace"]

runner = CliRunner()


@pytest.helpers.register
def to_uri(abs_path: str):
    return pathlib.Path(abs_path).as_uri()


@pytest.fixture(autouse=True)
def database():
    """Creates an empty graver database as a tempfile"""
    _, file_name = tempfile.mkstemp()
    os.environ["DATABASE_NAME"] = file_name
    Memorial.create_table(database_name=file_name)
    Cemetery.create_table(database_name=file_name)
    yield
    os.unlink(file_name)


live_urls = [
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

asimov_uri = pytest.helpers.to_uri(ROOT_DIR + "/tests/data/asimov.html")
hopper_uri = pytest.helpers.to_uri(ROOT_DIR + "/tests/data/hopper.html")
shoulders_uri = pytest.helpers.to_uri(ROOT_DIR + "/tests/data/shoulders.html")
merged_uri = pytest.helpers.to_uri(ROOT_DIR + "/tests/data/merged.html")
maiden_uri = pytest.helpers.to_uri(ROOT_DIR + "/tests/data/dolores-maiden.html")
cem_3136_uri = pytest.helpers.to_uri(ROOT_DIR + "/tests/data/cem-3136.html")

file_urls = [
    asimov_uri,
    hopper_uri,
    shoulders_uri,
    merged_uri,
    maiden_uri,
    cem_3136_uri,
]


@pytest.fixture(autouse=True)
def silence_tqdm():
    os.environ["TQDM_DISABLE"] = "1"
    os.environ["TQDM_MININTERVAL"] = "5"
    yield
    del os.environ["TQDM_DISABLE"]
    del os.environ["TQDM_MININTERVAL"]


@pytest.fixture(autouse=True)
def text_file_with_bad_url():
    """Creates a text file containing a single memorial URL"""
    _, file_name = tempfile.mkstemp()
    os.environ["BAD_DATA_FILENAME"] = file_name
    with open(file_name, "w") as f:
        f.write("https://www.findagrave.com/this-does-not-exist")
    yield
    os.unlink(file_name)


@pytest.fixture(autouse=True)
def single_line_text_file():
    """Creates a text file containing a single memorial URL"""
    _, file_name = tempfile.mkstemp()
    os.environ["SINGLE_LINE_FILENAME"] = file_name
    with open(file_name, "w") as f:
        f.write(live_urls[0])
    yield
    os.unlink(file_name)


@pytest.fixture(autouse=True)
def multi_line_text_file():
    """Creates a text file containing several memorial URLs, one per line"""
    _, file_name = tempfile.mkstemp()
    os.environ["MULTI_LINE_FILENAME"] = file_name
    with open(file_name, "w") as f:
        f.write("\n".join(live_urls))
    yield
    os.unlink(file_name)


@pytest.fixture(autouse=True)
def multi_line_with_file_uris():
    """Creates a text file containing several memorial URLs, one per line"""
    _, file_name = tempfile.mkstemp()
    os.environ["MULTI_LINE_UNIT_TEST_FILE"] = file_name
    with open(file_name, "w") as f:
        f.write("\n".join(file_urls))
    yield
    os.unlink(file_name)


class Helpers:
    @staticmethod
    def graver_cli(command_string):
        command_list = shlex.split(command_string)
        env = os.environ.copy()
        env["TQDM_DISABLE"] = "1"
        result = runner.invoke(app, command_list, env=env)
        output = result.stdout.rstrip()
        return output


@pytest.fixture
def helpers():
    return Helpers
