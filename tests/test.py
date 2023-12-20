import json
import logging
import os

import pytest
import requests
import vcr


def test_vcr():
    with vcr.use_cassette(Test.get_cassette("synopsis")):
        response = requests.get("http://www.iana.org/domains/reserved")
        assert b"Example domains" in response.content


@pytest.mark.usefixtures("helpers")
class Test:
    ROOT = os.path.dirname(os.path.abspath(__file__))
    CASSETTES = f"{ROOT}/fixtures/vcr_cassettes/"

    logging.basicConfig()
    vcr_log = logging.getLogger("vcr")
    vcr_log.setLevel(logging.WARN)

    @staticmethod
    def get_cassette(name: str):
        return os.path.join(Test.CASSETTES, f"{name}.yaml")

    @staticmethod
    def load_memorial_from_json(filename: str):
        json_path = f"{Test.ROOT}/fixtures/memorials/{filename}.json"
        with open(json_path) as f:
            return json.load(f)

    @staticmethod
    def load_cemetery_from_json(filename: str):
        json_path = f"{Test.ROOT}/fixtures/cemeteries/{filename}.json"
        with open(json_path) as f:
            return json.load(f)
