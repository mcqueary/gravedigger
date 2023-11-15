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


@pytest.fixture(autouse=True)
def sample_text_file():
    _, file_name = tempfile.mkstemp()
    with open(file_name, "w") as f:
        f.write("\n".join(live_urls))
    yield
    os.unlink(file_name)
