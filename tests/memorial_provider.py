import random
from datetime import date, datetime
from typing import List, Optional

from dateutil.relativedelta import relativedelta
from faker import Faker
from faker.providers import BaseProvider

from graver import Memorial
from graver.api import ResultSet


class MemorialProvider(BaseProvider):
    # def __init__(self) -> None:
    #     super().__init__(pytest.fixtures.faker)
    #     # super().generator
    # fake = pytest.fixture.faker
    # fake = faker.Faker()

    @staticmethod
    def format_url(memorial_id: int, name: str) -> str:
        # remove periods
        flat_name: str = name.replace(".", "")
        # replace existing hyphens with underscores
        flat_name = flat_name.replace("-", "_")
        # replace spaces with hyphens
        flat_name = flat_name.replace(" ", "-")
        # lowercase
        flat_name = flat_name.lower()

        url = f"https://www.findagrave.com/memorial/{memorial_id}/{flat_name}"
        return url

    @staticmethod
    def weighted_choice(pct_chance, choice: List):
        if random.randint(0, 100) < pct_chance:
            return choice[0]
        else:
            return choice[1]

    @staticmethod
    def generate_name(factory: Faker, gender: str, **kwargs) -> str:
        first_name: str | None = None
        middle_name: str | None = None
        if gender == "male":
            # first name
            first_name = kwargs.get("firstname", factory.first_name_male())
            # middle name
            middle_name = kwargs.get(
                "middlename", random.choice(["", factory.first_name_male()])
            )
            while middle_name == first_name:
                middle_name = factory.first_name_male()
        elif gender == "female":
            # first name
            first_name = factory.first_name_female()
            # middle name
            middle_name = random.choice(["", factory.first_name_female()])
            while middle_name == first_name:
                middle_name = factory.first_name_female()
        # last name
        last_name = kwargs.get("lastname", factory.last_name())
        while last_name == first_name or last_name == middle_name:
            last_name = factory.last_name()

        name = f"{first_name} "
        if middle_name != "":
            assert isinstance(middle_name, str)
            middle_name = random.choice([middle_name, middle_name[0] + "."])
            name += f"{middle_name} "
        name += last_name

        return name

    def memorial(self, factory: Faker, **kwargs) -> Memorial:
        # try to gen random every time
        factory.seed_instance(random.randint(1, 1000000) + datetime.now().timestamp())
        #
        memorial_id: int = factory.unique.random_int(min=300000000, max=300050000)
        gender = "male" if factory.pybool() else "female"
        name = self.generate_name(factory, gender, **kwargs)
        prefix: Optional[str] = None
        suffix: Optional[str] = None
        findagrave_url: str = self.format_url(memorial_id, name)
        birth_dt = factory.date_between("-200y", "today")
        birth: str = birth_dt.strftime("%d %B %Y")
        birth_place: str = f"{factory.city()}, {factory.city()} County, {factory.state()}, {factory.current_country()}"
        today_delta = relativedelta(date.today(), birth_dt).years
        max_age = min(105, today_delta)
        death_dt = factory.date_between(
            birth_dt, birth_dt + relativedelta(years=max_age)
        )
        death: str = death_dt.strftime("%d %B %Y")
        death_place: str = f"{factory.city()}, {factory.city()} County, {factory.state()}, {factory.current_country()}"
        age = relativedelta(death_dt, birth_dt).years
        if age >= 18:
            prefix = self.weighted_choice(
                50,
                [
                    factory.prefix_male()
                    if gender == "male"
                    else factory.prefix_female(),
                    None,
                ],
            )
            suffix = self.weighted_choice(
                25,
                [
                    factory.suffix_male()
                    if gender == "male"
                    else factory.suffix_female(),
                    None,
                ],
            )
        nickname: Optional[str] = None
        maiden_name: str | None = (
            random.choice([None, factory.last_name()]) if gender == "female" else None
        )
        original_name: str | None = None
        famous: bool = factory.pybool()
        veteran: bool = factory.pybool()
        memorial_type: str | None = None
        burial_place: str = f"{factory.city()}, {factory.city()} County, {factory.state()}, {factory.current_country()}"
        cemetery_id: int = kwargs.get(
            "cemetery_id", factory.unique.random_int(min=200000, max=300000)
        )
        plot: str | None = self.weighted_choice(
            20, [factory.paragraph(nb_sentences=1), None]
        )
        coords: str | None = random.choice(
            [None, f"{str(factory.latitude())},{str(factory.longitude())}"]
        )
        has_bio: bool = factory.pybool()
        m = Memorial(
            memorial_id=memorial_id,
            findagrave_url=findagrave_url,
            prefix=str(prefix),
            name=name,
            suffix=str(suffix),
            nickname=str(nickname),
            maiden_name=str(maiden_name),
            original_name=str(original_name),
            famous=famous,
            veteran=veteran,
            birth=birth,
            birth_place=birth_place,
            death=death,
            death_place=death_place,
            memorial_type=str(memorial_type),
            burial_place=burial_place,
            cemetery_id=cemetery_id,
            plot=str(plot),
            coords=str(coords),
            has_bio=has_bio,
        )

        return m


class ResultSetProvider(BaseProvider):
    def result_set(
        self, factory: Faker, source: str = "", num_results: int = 0, **kwargs
    ) -> ResultSet:
        rs = ResultSet(source)
        for _ in range(num_results):
            rs.append(factory.memorial(factory, **kwargs))
        return rs
