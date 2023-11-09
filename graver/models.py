import os
import sqlite3

from pydantic import BaseModel
from .soup import (
    get_birth_date,
    get_birth_place,
    get_burial_plot,
    get_death_date,
    get_death_place,
    get_name,
    get_soup,
)


class Grave(BaseModel):
    _id: int
    _url: str
    _name: str
    _birth: str
    _birthplace: str
    _death: str
    _deathplace: str
    _burial: str
    _plot: str
    _more_info: bool

    @classmethod
    def instance_from_soup(id, tree):
        url = "https://www.findagrave.com/memorial/" + str(id)
        name = get_name(tree)
        birth = get_birth_date(tree)
        birthplace = get_birth_place(tree)
        death = get_death_date(tree)
        deathplace = get_death_place(tree)
        plot = get_burial_plot(tree)
        more_info = False
        return Grave(
            id, url, name, birth, birthplace, death, deathplace, plot, more_info
        )

    @classmethod
    def create_table(cls, database_name="graver.db"):
        conn = sqlite3.connect(database_name)
        conn.execute(
            """CREATE TABLE IF NOT EXISTS graves
            (graveid INTEGER PRIMARY KEY, url TEXT,
            name TEXT, birth TEXT, birthplace TEXT, death TEXT, deathplace TEXT,
            burial TEXT, plot TEXT, more_info BOOL)"""
        )
        conn.close()

    def __init__(self, url):
        self._url = url
        tree = get_soup(url)
        self._name = get_name(tree)
        self._birth = get_birth_date(tree)
        self._birthplace = get_birth_place(tree)
        self._death = get_death_date(tree)
        self._deathplace = get_death_place(tree)
        self._plot = get_burial_plot(tree)
        self._more_info = False
        return self

    def save(self) -> "Grave":
        with sqlite3.connect(os.getenv("DATABASE_NAME", "graves.db")) as con:
            con.cursor().execute(
                "INSERT INTO graves (id,author,title,content) VALUES"
                + "(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    self._id,
                    self._url,
                    self._name,
                    self._birth,
                    self._birthplace,
                    self._death,
                    self._deathplace,
                    self._burial,
                    self._plot,
                    self._more_info,
                ),
            )
            con.commit()

        return self

    # def save(self) -> "Grave":
    #     row = (grave["id"],)
    #     keys = ["graveid"]
    #     for key in grave.keys():
    #         if key == "id":
    #             continue
    #         row += (grave[key],)
    #         keys.append(key)

    #     col_names = "(" + ", ".join(keys) + ")"
    #     value_hold = "(" + "?," * (len(keys) - 1) + "?)"
    #     trunk-ignore(bandit/B608)
    #     insert = "INSERT INTO findAGrave " + col_names + " VALUES " + value_hold

    #     try:
    #         conn = sql.connect(filename)
    #         c = conn.cursor()
    #         c.executemany(insert, [row])
    #         conn.commit()
    #         conn.close()
    #     except sql.IntegrityError:
    #         log.warn("Memorial #" + grave["id"] + " is already in database.")
    #     except Exception as e:
    #         log.exception(e)
