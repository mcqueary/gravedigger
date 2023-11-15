import sqlite3
from dataclasses import asdict, dataclass


class CemeteryException(Exception):
    pass


@dataclass
class Cemetery:
    """Class for keeping track of a Find A Grave cemetery."""

    id: int
    url: str
    name: str
    location: str
    coords: str

    def __eq__(self, other):
        if self.__class__ != other.__class__:
            return False
        return self.__dict__ == other.__dict__

    @classmethod
    def from_dict(cls, d):
        return Cemetery(**d)

    def to_dict(self):
        return asdict(self)

    @classmethod
    def create_table(cls, database_name="graves.db"):
        conn = sqlite3.connect(database_name)
        conn.execute(
            """CREATE TABLE IF NOT EXISTS cemeteries
            (id INTEGER PRIMARY KEY, url TEXT,
            name TEXT, location TEXT, coords TEXT, more_info BOOL)"""
        )
        conn.close()
