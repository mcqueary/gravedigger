import os
import shlex
import tempfile
from datetime import datetime

import pytest
from betamax import Betamax
from click.testing import Result
from faker import Faker
from typer.testing import CliRunner

from graver import Cemetery, Driver, Memorial
from graver.cli import app
from tests.memorial_provider import MemorialProvider, ResultSetProvider


pytest_plugins = ["helpers_namespace"]


def pytest_configure():
    pass


@pytest.fixture(autouse=True)
def customize_faker(faker: Faker):
    faker.add_provider(MemorialProvider)
    faker.add_provider(ResultSetProvider)


# configure Betamax
with Betamax.configure() as config:
    path = os.path.dirname(os.path.abspath(__file__))
    config.cassette_library_dir = os.path.join(path, "fixtures/cassettes")
    # config.default_cassette_options["record_mode"] = "none"

runner = CliRunner()


@pytest.fixture(scope="function")
def driver(betamax_parametrized_session):
    d = Driver(session=betamax_parametrized_session)
    yield d


# configure Faker
@pytest.fixture(scope="session", autouse=True)
def faker_seed() -> int:
    seed: int = int(datetime.now().timestamp())
    return seed


@pytest.fixture
def database():
    """Creates an empty graver database as a tempfile"""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tf:
        os.environ["DATABASE_NAME"] = tf.name
        Memorial.create_table(database_name=tf.name)
        Cemetery.create_table(database_name=tf.name)
        yield tf


class Helpers:
    @staticmethod
    def graver_cli(command_string) -> Result:
        command_list = shlex.split(command_string)
        env = os.environ.copy()
        env["TQDM_DISABLE"] = "1"
        result = runner.invoke(app, command_list, env=env, obj=driver)
        return result


@pytest.fixture
def helpers():
    return Helpers
