import json
import os
import pathlib
import shlex
import tempfile

import pytest
from typer.testing import CliRunner

# from cli import app
from definitions import PROJECT_ROOT
from graver import Cemetery, Memorial
from graver.cli import app

# from graver import app

pytest_plugins = ["helpers_namespace"]

runner = CliRunner()


def to_uri(path: str):
    return pathlib.Path(PROJECT_ROOT + path).as_uri()


@pytest.helpers.register
def load_memorial_from_json(filename: str):
    json_path = f"{PROJECT_ROOT}/tests/fixtures/memorials/{filename}.json"
    with open(json_path) as f:
        return json.load(f)


@pytest.helpers.register
def load_cemetery_from_json(filename: str):
    json_path = f"{PROJECT_ROOT}/tests/fixtures/cemeteries/{filename}.json"
    with open(json_path) as f:
        return json.load(f)


@pytest.fixture
def database():
    """Creates an empty graver database as a tempfile"""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tf:
        os.environ["DATABASE_NAME"] = tf.name
        Memorial.create_table(database_name=tf.name)
        Cemetery.create_table(database_name=tf.name)
        yield tf
        tf.close()
        os.unlink(tf.name)


def pytest_configure():
    pytest.vcr_cassettes = f"{PROJECT_ROOT}/tests/fixtures/vcr_cassettes/"


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
