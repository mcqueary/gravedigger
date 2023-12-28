import json
import os
from datetime import datetime

import pytest

from graver import Memorial


@pytest.mark.usefixtures("betamax_parametrized_session")
def test_vcr(betamax_parametrized_session):
    response = betamax_parametrized_session.get("http://www.iana.org/domains/reserved")
    assert b"Example domains" in response.content


def test_faker(faker):
    name = faker.name()
    assert isinstance(name, str)
    address = faker.address()
    assert isinstance(address, str)
    dt = faker.date_time()
    assert isinstance(dt, datetime)
    prof = faker.profile()
    assert isinstance(prof, dict)
    url = faker.url(schemes=["https"])
    assert isinstance(url, str)


@pytest.mark.usefixtures("helpers")
class Test:
    ROOT = os.path.dirname(os.path.abspath(__file__))

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

    @pytest.mark.usefixtures("faker")
    def test_gen_memorial(self, faker):
        num_memorials = 50
        memorials = []
        for _ in range(num_memorials):
            m = faker.memorial(faker)
            assert isinstance(m, Memorial)
            memorials.append(m)
        pass

    @staticmethod
    def fake_result_set(source: str, num: int, faker):
        pass
