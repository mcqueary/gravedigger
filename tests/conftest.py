import os
import shlex
import tempfile

import pytest
from typer.testing import CliRunner

# from cli import app
from graver import Cemetery, Memorial
from graver.cli import app

# import vcr

pytest_plugins = ["helpers_namespace"]

runner = CliRunner()


@pytest.fixture
def database():
    """Creates an empty graver database as a tempfile"""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tf:
        os.environ["DATABASE_NAME"] = tf.name
        Memorial.create_table(database_name=tf.name)
        Cemetery.create_table(database_name=tf.name)
        yield tf


# def pytest_configure():
#     pytest.CASSETTES = f"tests/fixtures/vcr_cassettes/"


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
