import os
import pathlib
import tempfile

import pytest

from graver.cemetery import Cemetery
from graver.memorial import Memorial

pytest_plugins = ["helpers_namespace"]
# pytest_plugins = ["pytester"]


@pytest.helpers.register
def to_uri(abs_path: str):
    return pathlib.Path(abs_path).as_uri()


@pytest.fixture(autouse=True)
def database():
    _, file_name = tempfile.mkstemp()
    os.environ["DATABASE_NAME"] = file_name
    Memorial.create_table(database_name=file_name)
    Cemetery.create_table(database_name=file_name)
    yield
    os.unlink(file_name)
