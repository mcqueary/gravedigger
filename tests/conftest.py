import os
import tempfile

import pytest

from memorial import Memorial
from cemetery import Cemetery


@pytest.fixture(autouse=True)
def database():
    _, file_name = tempfile.mkstemp()
    os.environ["DATABASE_NAME"] = file_name
    Memorial.create_table(database_name=file_name)
    Cemetery.create_table(database_name=file_name)
    yield
    os.unlink(file_name)


# pytest_plugins = ["pytester"]
