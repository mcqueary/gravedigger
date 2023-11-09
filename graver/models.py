import os
import sqlite3

from pydantic import BaseModel


class Grave(BaseModel):
    id: int
    url: str
    name: str
    birth: str
    birthplace: str
    death: str
    deathplace: str
    burial: str
    plot: str
    more_info: bool

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

    def save(self) -> "Grave":
        with sqlite3.connect(os.getenv("DATABASE_NAME", "graves.db")) as con:
            con.cursor().execute(
                "INSERT INTO graves (id,author,title,content) VALUES"
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
                    self.more_info,
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
