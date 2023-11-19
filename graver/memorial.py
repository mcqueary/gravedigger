import os
import sqlite3
from dataclasses import asdict, dataclass


class MemorialException(Exception):
    pass


class MemorialMergedException(MemorialException):
    pass


class MemorialRemoveddException(MemorialException):
    pass


class NotFound(MemorialException):
    pass


@dataclass
class Memorial:
    """Class for keeping track of a Find A Grave memorial."""

    id: int
    url: str
    name: str
    birth: str
    birthplace: str
    death: str
    deathplace: str
    burial: str
    plot: str
    coords: str
    more_info: bool

    COLUMNS = [
        "id",
        "url",
        "name",
        "birth",
        "birthplace",
        "death",
        "deathplace",
        "burial",
        "plot",
        "coords",
        "more_info",
    ]

    def __eq__(self, other):
        if self.__class__ != other.__class__:
            return False
        return self.__dict__ == other.__dict__

    @classmethod
    def from_dict(cls, d):
        return Memorial(**d)

    def to_dict(self):
        return asdict(self)

    @classmethod
    def get_by_id(cls, grave_id: int):
        con = sqlite3.connect(os.getenv("DATABASE_NAME", "graves.db"))
        con.row_factory = sqlite3.Row

        cur = con.cursor()
        cur.execute("SELECT * FROM graves WHERE id=?", (grave_id,))

        record = cur.fetchone()

        if record is None:
            raise NotFound

        memorial = Memorial(*record)  # Row can be unpacked as dict

        con.close()

        return memorial

    @classmethod
    def create_table(cls, database_name="graves.db"):
        conn = sqlite3.connect(database_name)
        conn.execute(
            """CREATE TABLE IF NOT EXISTS graves
            (id INTEGER PRIMARY KEY, url TEXT,
            name TEXT, birth TEXT, birthplace TEXT, death TEXT, deathplace TEXT,
            burial TEXT, plot TEXT, coords TEXT, more_info BOOL)"""
        )
        conn.close()

    def save(self) -> "Memorial":
        with sqlite3.connect(os.getenv("DATABASE_NAME", "graves.db")) as con:
            con.cursor().execute(
                "INSERT OR REPLACE INTO graves (id,url,name,birth,birthplace,death,"
                + "deathplace,burial,plot,coords,more_info) VALUES"
                + "(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    self.id,
                    self.url,
                    self.name,
                    self.birth,
                    self.birthplace,
                    self.death,
                    self.deathplace,
                    self.burial,
                    self.plot,
                    self.coords,
                    self.more_info,
                ),
            )
            con.commit()

        return self
